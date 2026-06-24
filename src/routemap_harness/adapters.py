"""Model adapter contract and optional provider runtimes."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Protocol


DEFAULT_MODEL_REF = "llama3.1"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OPENAI_URL = "https://api.openai.com/v1/responses"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
EXPERIMENTAL_CLI_RUNTIMES = {"codex", "claude-cli", "gemini-cli"}
_PINS: dict[str, tuple[str, str, str, str]] = {}


class ModelAdapterError(RuntimeError):
    """Raised when a model adapter cannot complete the requested call."""


class ModelAdapterUnavailable(ModelAdapterError):
    """Raised when a runtime is unavailable or disabled."""


class ModelFn(Protocol):
    def __call__(
        self,
        prompt: str,
        *,
        model_ref: str,
        runtime: str = "ollama",
        auth_mode: str = "local",
        timeout: int = 60,
        strict_model: bool = False,
        fallbacks: list[str] | None = None,
    ) -> str:
        ...


@dataclass(frozen=True)
class ModelCallMetadata:
    provider: str
    model_ref: str
    runtime: str
    auth_mode: str
    fallback_used: str | None
    latency_ms: float
    tokens: int | None = None
    cost_usd: float | None = None
    run_id: str | None = None
    session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


class ModelResponse(str):
    """String response with attached model-call metadata."""

    metadata: ModelCallMetadata

    def __new__(cls, text: str, metadata: ModelCallMetadata) -> "ModelResponse":
        obj = str.__new__(cls, text)
        obj.metadata = metadata
        return obj


def model_fn(
    prompt: str,
    *,
    model_ref: str,
    runtime: str = "ollama",
    auth_mode: str = "local",
    timeout: int = 60,
    strict_model: bool = False,
    fallbacks: list[str] | None = None,
) -> str:
    """Call a configured model runtime and return model text."""
    pinned = _pinned(runtime=runtime, model_ref=model_ref, auth_mode=auth_mode)
    if pinned:
        runtime, model_ref, auth_mode = pinned[2], pinned[1], pinned[3]

    attempts = [(runtime, model_ref)] if strict_model else [(runtime, model_ref), *[_parse_fallback(runtime, item) for item in (fallbacks or [])]]
    errors: list[str] = []
    for index, (candidate_runtime, candidate_model) in enumerate(attempts):
        start = time.perf_counter()
        fallback_used = None if index == 0 else f"{candidate_runtime}:{candidate_model}"
        try:
            text, usage = _dispatch(prompt, model_ref=candidate_model, runtime=candidate_runtime, auth_mode=auth_mode, timeout=timeout)
        except ModelAdapterUnavailable as exc:
            errors.append(str(exc))
            if strict_model:
                raise
            continue
        except ModelAdapterError as exc:
            errors.append(str(exc))
            if strict_model:
                raise
            continue
        latency_ms = (time.perf_counter() - start) * 1000.0
        metadata = ModelCallMetadata(
            provider=_provider_for_runtime(candidate_runtime),
            model_ref=candidate_model,
            runtime=candidate_runtime,
            auth_mode=auth_mode,
            fallback_used=fallback_used,
            latency_ms=latency_ms,
            tokens=usage.get("tokens"),
            cost_usd=usage.get("cost_usd"),
            run_id=_run_id(),
            session_id=_session_id(),
        )
        _pin(candidate_runtime, candidate_model, auth_mode)
        return ModelResponse(text, metadata)
    raise ModelAdapterUnavailable("; ".join(errors) if errors else "no model adapter available")


def ollama_adapter(prompt: str, *, model_ref: str, timeout: int = 60) -> tuple[str, dict[str, Any]]:
    """Local Ollama adapter using deterministic generation settings."""
    payload = json.dumps(
        {
            "model": model_ref,
            "stream": False,
            "prompt": prompt,
            "options": {"temperature": 0, "num_predict": 256},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ModelAdapterError(f"ollama adapter failed: {exc}") from exc
    usage = {"tokens": _usage_total(data)}
    return str(data.get("response", "")), usage


def openai_api_adapter(prompt: str, *, model_ref: str, timeout: int = 60) -> tuple[str, dict[str, Any]]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ModelAdapterUnavailable("OPENAI_API_KEY is not set")
    payload = json.dumps({"model": model_ref, "input": prompt}).encode("utf-8")
    request = urllib.request.Request(
        OPENAI_URL,
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    data = _json_request(request, timeout=timeout, provider="openai")
    text = _openai_text(data)
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    return text, {"tokens": usage.get("total_tokens")}


def anthropic_api_adapter(prompt: str, *, model_ref: str, timeout: int = 60) -> tuple[str, dict[str, Any]]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ModelAdapterUnavailable("ANTHROPIC_API_KEY is not set")
    payload = json.dumps(
        {
            "model": model_ref,
            "max_tokens": 512,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        ANTHROPIC_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    data = _json_request(request, timeout=timeout, provider="anthropic")
    chunks = data.get("content", [])
    text = "".join(str(item.get("text", "")) for item in chunks if isinstance(item, dict))
    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    tokens = None
    if "input_tokens" in usage or "output_tokens" in usage:
        tokens = int(usage.get("input_tokens", 0)) + int(usage.get("output_tokens", 0))
    return text, {"tokens": tokens}


def experimental_cli_adapter(prompt: str, *, runtime: str, model_ref: str, timeout: int = 60) -> tuple[str, dict[str, Any]]:
    raise ModelAdapterUnavailable(
        f"{runtime} is an experimental CLI/OAuth runtime and is disabled by default; "
        "enable only with an explicit user-controlled adapter that follows provider terms"
    )


def metadata_from_response(response: Any) -> ModelCallMetadata | None:
    metadata = getattr(response, "metadata", None)
    return metadata if isinstance(metadata, ModelCallMetadata) else None


def metadata_dict(response: Any) -> dict[str, Any]:
    metadata = metadata_from_response(response)
    return {} if metadata is None else metadata.to_dict()


def _dispatch(prompt: str, *, model_ref: str, runtime: str, auth_mode: str, timeout: int) -> tuple[str, dict[str, Any]]:
    if runtime == "ollama":
        if auth_mode != "local":
            raise ModelAdapterUnavailable("ollama runtime requires auth_mode=local")
        return ollama_adapter(prompt, model_ref=model_ref, timeout=timeout)
    if runtime == "openai":
        if auth_mode != "api_key":
            raise ModelAdapterUnavailable("openai runtime requires auth_mode=api_key")
        return openai_api_adapter(prompt, model_ref=model_ref, timeout=timeout)
    if runtime == "anthropic":
        if auth_mode != "api_key":
            raise ModelAdapterUnavailable("anthropic runtime requires auth_mode=api_key")
        return anthropic_api_adapter(prompt, model_ref=model_ref, timeout=timeout)
    if runtime in EXPERIMENTAL_CLI_RUNTIMES:
        return experimental_cli_adapter(prompt, runtime=runtime, model_ref=model_ref, timeout=timeout)
    raise ModelAdapterUnavailable(f"unknown runtime: {runtime}")


def _json_request(request: urllib.request.Request, *, timeout: int, provider: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise ModelAdapterError(f"{provider} adapter failed: {exc}") from exc


def _openai_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return str(data["output_text"])
    chunks: list[str] = []
    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    return "".join(chunks)


def _usage_total(data: dict[str, Any]) -> int | None:
    total = data.get("eval_count")
    if total is None:
        return None
    try:
        return int(total)
    except (TypeError, ValueError):
        return None


def _parse_fallback(runtime: str, fallback: str) -> tuple[str, str]:
    if ":" in fallback:
        candidate_runtime, candidate_model = fallback.split(":", 1)
        return candidate_runtime, candidate_model
    return runtime, fallback


def _provider_for_runtime(runtime: str) -> str:
    if runtime in {"ollama", "openai", "anthropic"}:
        return runtime
    if runtime in EXPERIMENTAL_CLI_RUNTIMES:
        return runtime
    return "unknown"


def _run_id() -> str | None:
    return os.environ.get("ROUTEMAP_RUN_ID")


def _session_id() -> str | None:
    return os.environ.get("ROUTEMAP_SESSION_ID")


def _pin_key() -> str | None:
    return _run_id() or _session_id()


def _pin(runtime: str, model_ref: str, auth_mode: str) -> None:
    key = _pin_key()
    if key and key not in _PINS:
        _PINS[key] = (_provider_for_runtime(runtime), model_ref, runtime, auth_mode)


def _pinned(*, runtime: str, model_ref: str, auth_mode: str) -> tuple[str, str, str, str] | None:
    key = _pin_key()
    if not key:
        return None
    return _PINS.get(key)


__all__ = [
    "ANTHROPIC_URL",
    "DEFAULT_MODEL_REF",
    "EXPERIMENTAL_CLI_RUNTIMES",
    "ModelAdapterError",
    "ModelAdapterUnavailable",
    "ModelCallMetadata",
    "ModelFn",
    "ModelResponse",
    "OLLAMA_URL",
    "OPENAI_URL",
    "anthropic_api_adapter",
    "experimental_cli_adapter",
    "metadata_dict",
    "metadata_from_response",
    "model_fn",
    "ollama_adapter",
    "openai_api_adapter",
]
