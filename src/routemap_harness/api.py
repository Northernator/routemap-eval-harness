"""FastAPI surface for routemap-harness."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import audit_store
from .adapters import DEFAULT_MODEL_REF, EXPERIMENTAL_CLI_RUNTIMES, model_fn
from .core import HarnessDecision, harness_check
from .policy import repair, repair_stub
from routemap_bench.tasks import exact_value_feasible
from routemap_digital.parser import parse_expression


app = FastAPI(title="RouteMap Harness API")


@app.get("/")
def app_page() -> FileResponse:
    return FileResponse(_app_page_path(), media_type="text/html")


@app.get("/models")
def models() -> list[dict[str, Any]]:
    return _model_statuses()


@app.post("/check")
def check(body: dict[str, Any]) -> dict[str, Any]:
    payload = _check_payload(body)
    decision = harness_check(payload, strict=bool(body.get("strict")))
    audit_store.append(decision, _audit_path())
    return decision.to_dict()


@app.post("/run")
def run(body: dict[str, Any]) -> dict[str, Any]:
    prompt = str(body.get("prompt", ""))
    model_ref = str(body.get("model_ref") or DEFAULT_MODEL_REF)
    runtime = str(body.get("runtime") or "ollama")
    model_output = model_fn(
        prompt,
        model_ref=model_ref,
        runtime=runtime,
        auth_mode=_auth_mode(runtime),
        strict_model=bool(body.get("strict")),
    )
    payload = _run_payload(body, prompt=prompt, model_output=str(model_output), model_ref=model_ref, runtime=runtime)
    decision = harness_check(payload, strict=bool(body.get("strict")))
    audit_store.append(decision, _audit_path())

    final_decision = decision
    repair_attempts: list[dict[str, Any]] = []
    final_output: Any = str(model_output)
    if _should_repair(decision):
        repaired = repair(decision, payload, model_fn, max_retries=2, audit_path=_audit_path())
        final_decision = repaired.final_decision
        repair_attempts = [attempt.to_dict() for attempt in repaired.attempts]
        final_output = _final_output(str(model_output), final_decision)

    exact_correction = _exact_correction(payload, final_decision)
    if exact_correction is not None:
        final_output = exact_correction

    return {
        "prompt": prompt,
        "model_output": str(model_output),
        "final_output": final_output,
        "decision": final_decision.to_dict(),
        "repair_attempts": repair_attempts,
        "audit_id": final_decision.decision_id,
        "exact_correction": exact_correction,
    }


@app.post("/repair")
def repair_decision(body: dict[str, Any]) -> dict[str, Any]:
    _repair = repair
    return dict(repair_stub(str(body.get("decision_id", ""))))


@app.get("/audit")
def audit_tail(limit: int = 20) -> list[dict[str, Any]]:
    return audit_store.tail(_audit_path(), limit)


@app.get("/audit/{decision_id}")
def audit_record(decision_id: str) -> dict[str, Any]:
    record = audit_store.get_record(decision_id, _audit_path())
    if record is None:
        raise HTTPException(status_code=404, detail="decision not found")
    return record


def _audit_path() -> str:
    return str(getattr(app.state, "audit_path", audit_store.DEFAULT_AUDIT))


def _app_page_path() -> Path:
    return Path(__file__).resolve().parent / "web" / "app.html"


def _model_statuses() -> list[dict[str, Any]]:
    openai_available = bool(os.environ.get("OPENAI_API_KEY"))
    anthropic_available = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return [
        {
            "model_ref": DEFAULT_MODEL_REF,
            "runtime": "ollama",
            "auth_mode": "local",
            "available": True,
            "note": "local Ollama runtime",
        },
        {
            "model_ref": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            "runtime": "openai",
            "auth_mode": "api_key",
            "available": openai_available,
            "note": "OPENAI_API_KEY set" if openai_available else "OPENAI_API_KEY not set",
        },
        {
            "model_ref": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            "runtime": "anthropic",
            "auth_mode": "api_key",
            "available": anthropic_available,
            "note": "ANTHROPIC_API_KEY set" if anthropic_available else "ANTHROPIC_API_KEY not set",
        },
        *[
            {
                "model_ref": runtime,
                "runtime": runtime,
                "auth_mode": "cli",
                "available": False,
                "note": "experimental runtime disabled in local control page",
            }
            for runtime in sorted(EXPERIMENTAL_CLI_RUNTIMES)
        ],
    ]


def _check_payload(body: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {"raw": body.get("output")}
    task = body.get("task")
    if task:
        payload["task_type"] = task
    if body.get("spec") is not None:
        payload["schema"] = body.get("spec")
    return payload


def _run_payload(
    body: dict[str, Any],
    *,
    prompt: str,
    model_output: str,
    model_ref: str,
    runtime: str,
) -> dict[str, Any]:
    task_hint = body.get("task_hint")
    payload: dict[str, Any] = {
        "prompt": prompt,
        "raw": model_output,
        "model_ref": model_ref,
        "runtime": runtime,
        "auth_mode": _auth_mode(runtime),
    }
    if task_hint:
        payload["task_type"] = str(task_hint)
    if body.get("spec") is not None:
        payload["schema"] = body.get("spec")
    if payload.get("task_type") == "arithmetic" or (not task_hint and _is_arithmetic_prompt(prompt)):
        payload["task_type"] = "arithmetic"
        payload["expr"] = prompt
        payload["claimed_answer"] = _first_int(model_output)
    elif not task_hint and "```" not in model_output:
        payload["task_type"] = "unknown"
    return payload


def _should_repair(decision: HarnessDecision) -> bool:
    return decision.action == "repair" or (decision.task_type == "arithmetic" and decision.verdict == "RULED_OUT_WRONG")


def _final_output(model_output: str, decision: HarnessDecision) -> Any:
    full_compute = dict(decision.validator_record or {}).get("full_compute")
    if isinstance(full_compute, dict) and "exact_value" in full_compute:
        return full_compute["exact_value"]
    return model_output


def _exact_correction(payload: dict[str, Any], decision: HarnessDecision) -> Any:
    if decision.task_type != "arithmetic" or decision.verdict != "RULED_OUT_WRONG":
        return None
    full_compute = dict(decision.validator_record or {}).get("full_compute")
    if isinstance(full_compute, dict) and "exact_value" in full_compute:
        return full_compute["exact_value"]
    try:
        expr_spec, _modulus = parse_expression(str(payload.get("expr", "")))
        return exact_value_feasible(expr_spec)
    except (ValueError, TypeError, OverflowError):
        return None


def _is_arithmetic_prompt(prompt: str) -> bool:
    try:
        parse_expression(prompt)
        return True
    except ValueError:
        return False


def _first_int(text: str) -> int:
    import re

    match = re.search(r"[+-]?\d+", text)
    return int(match.group(0)) if match else 0


def _auth_mode(runtime: str) -> str:
    return "api_key" if runtime in {"openai", "anthropic"} else "local"


__all__ = ["app"]
