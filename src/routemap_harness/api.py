"""FastAPI surface for routemap-harness."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import audit_store, run_store
from .adapters import (
    DEFAULT_MODEL_REF,
    EXPERIMENTAL_CLI_RUNTIMES,
    ModelAdapterError,
    ModelAdapterUnavailable,
    metadata_dict,
    model_fn,
)
from .core import HarnessDecision, harness_check
from .policy import repair, repair_stub
from .scorecard import scorecard
from routemap_bench.tasks import exact_value_feasible
from routemap_digital.parser import parse_expression
from routemap_prompt import optimize_prompt as structure_prompt
from routemap_token import route_passage, route_passage_detail


app = FastAPI(title="RouteMap Harness API")
_LAST_MODEL_METADATA: dict[str, Any] = {}


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
    decision = _with_model_record(decision, body.get("model"))
    audit_store.append(decision, _audit_path())
    response = decision.to_dict()
    response["scorecard"] = scorecard(response)
    return response


@app.post("/run")
def run(body: dict[str, Any]) -> dict[str, Any]:
    model_ref = str(body.get("model_ref") or DEFAULT_MODEL_REF)
    runtime = str(body.get("runtime") or "ollama")
    return _run_once(body, runtime=runtime, model_ref=model_ref)


def _run_once(body: dict[str, Any], *, runtime: str, model_ref: str) -> dict[str, Any]:
    global _LAST_MODEL_METADATA
    prompt = str(body.get("prompt", ""))
    optimization = _prompt_optimization(body, prompt)
    prompt_for_model = str(optimization["prompt"])
    compression = _optimize_prompt(body, prompt_for_model)
    model_output = model_fn(
        str(compression["prompt_sent"]),
        model_ref=model_ref,
        runtime=runtime,
        auth_mode=_auth_mode(runtime),
        strict_model=bool(body.get("strict")),
    )
    model_metadata = metadata_dict(model_output)
    _LAST_MODEL_METADATA = model_metadata
    payload = _run_payload(body, prompt=prompt_for_model, model_output=str(model_output), model_ref=model_ref, runtime=runtime)
    decision = harness_check(payload, strict=bool(body.get("strict")))
    decision = _with_model_record(decision, model_ref)
    decision = _with_compression_record(decision, compression)
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

    response = {
        "prompt": prompt,
        "prompt_sent": compression["prompt_sent"],
        "optimized": optimization["optimized"],
        "optimized_prompt": optimization["optimized_prompt"],
        "preserved": optimization["preserved"],
        "model_output": str(model_output),
        "final_output": final_output,
        "decision": _api_decision(final_decision),
        "repair_attempts": repair_attempts,
        "compressed": compression["compressed"],
        "tokens_before": compression["tokens_before"],
        "tokens_after": compression["tokens_after"],
        "reduction": compression["reduction"],
        "route_note": compression["route_note"],
        "audit_id": final_decision.decision_id,
        "exact_correction": exact_correction,
    }
    response["scorecard"] = scorecard(final_decision.to_dict(), run=response)
    run_store.append_run(
        _run_record(
            response,
            final_decision,
            compression=compression,
            model_metadata=model_metadata,
            runtime=runtime,
            model_ref=model_ref,
        ),
        _runs_path(),
    )
    return response


@app.post("/compare")
def compare(body: dict[str, Any]) -> dict[str, Any]:
    prompt = str(body.get("prompt", ""))
    results: list[dict[str, Any]] = []
    for model in body.get("models") or []:
        runtime = str(dict(model).get("runtime") or "ollama")
        model_ref = str(dict(model).get("model_ref") or DEFAULT_MODEL_REF)
        run_body = {
            **body,
            "prompt": prompt,
            "runtime": runtime,
            "model_ref": model_ref,
        }
        try:
            run_result = _run_once(run_body, runtime=runtime, model_ref=model_ref)
        except (ModelAdapterUnavailable, ModelAdapterError) as exc:
            results.append({
                "runtime": runtime,
                "model_ref": model_ref,
                "available": False,
                "error": str(exc),
            })
            continue
        decision = dict(run_result.get("decision") or {})
        metadata = dict(_LAST_MODEL_METADATA)
        results.append({
            "runtime": runtime,
            "model_ref": model_ref,
            "available": True,
            "model_output": run_result["model_output"],
            "final_output": run_result["final_output"],
            "decision": run_result["decision"],
            "repair_attempts": run_result["repair_attempts"],
            "tokens_before": run_result["tokens_before"],
            "tokens_after": run_result["tokens_after"],
            "reduction": run_result["reduction"],
            "latency_ms": metadata.get("latency_ms", decision.get("latency_ms")),
            "cost_usd": metadata.get("cost_usd"),
        })
    return {"prompt": prompt, "results": results}


@app.post("/route")
def route(body: dict[str, Any]) -> dict[str, Any]:
    passage = str(body.get("passage") or "")
    question = str(body.get("question") or "")
    router_mode = str(body.get("router_mode") or "element")
    rows = route_passage_detail(passage, question, router_mode=router_mode)
    kept = [str(row["token"]) for row in rows if row.get("route_action") == "keep"]
    token_count = len(rows)
    kept_count = len(kept)
    cheap_count = sum(1 for row in rows if row.get("route_action") == "cheap")
    return {
        "router_mode": router_mode,
        "tokens": token_count,
        "kept": kept_count,
        "cheap": cheap_count,
        "reduction": 0.0 if token_count == 0 else 1.0 - (kept_count / token_count),
        "compressed_prompt": " ".join(kept),
        "rows": rows,
    }


@app.post("/repair")
def repair_decision(body: dict[str, Any]) -> dict[str, Any]:
    _repair = repair
    return dict(repair_stub(str(body.get("decision_id", ""))))


@app.get("/audit")
def audit_tail(limit: int = 20) -> list[dict[str, Any]]:
    return audit_store.tail(_audit_path(), limit)


@app.get("/summary")
def summary() -> dict[str, Any]:
    return audit_store.summarize(_audit_path())


@app.get("/replay/{decision_id}")
def replay(decision_id: str) -> dict[str, Any]:
    decision = audit_store.get_record(decision_id, _audit_path())
    run_record = run_store.get_run(decision_id, _runs_path())
    if decision is None and run_record is None:
        raise HTTPException(status_code=404, detail="replay not found")
    return {"decision": decision, "run": run_record}


@app.get("/audit/{decision_id}")
def audit_record(decision_id: str) -> dict[str, Any]:
    record = audit_store.get_record(decision_id, _audit_path())
    if record is None:
        raise HTTPException(status_code=404, detail="decision not found")
    return record


def _audit_path() -> str:
    return str(getattr(app.state, "audit_path", audit_store.DEFAULT_AUDIT))


def _runs_path() -> str:
    return str(getattr(app.state, "runs_path", run_store.DEFAULT_RUNS))


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
    if task == "grounded_qa":
        payload["answer"] = body.get("output")
    if body.get("spec") is not None:
        payload["schema"] = body.get("spec")
    if body.get("allowed_tools") is not None:
        payload["allowed_tools"] = body.get("allowed_tools")
    if body.get("source") is not None:
        payload["source"] = body.get("source")
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
    if body.get("allowed_tools") is not None:
        payload["allowed_tools"] = body.get("allowed_tools")
    if body.get("source") is not None:
        payload["source"] = body.get("source")
    if payload.get("task_type") == "grounded_qa":
        payload["answer"] = model_output
    if payload.get("task_type") == "arithmetic":
        payload["task_type"] = "arithmetic"
        payload["expr"] = prompt
        payload["claimed_answer"] = _first_int(model_output)
    return payload


def _should_repair(decision: HarnessDecision) -> bool:
    return decision.action == "repair" or (
        decision.verdict == "RULED_OUT_WRONG"
        and decision.task_type in {"arithmetic", "json_schema", "tool_call", "python_code"}
    )


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


def _first_int(text: str) -> int:
    import re

    match = re.search(r"[+-]?\d+", text)
    return int(match.group(0)) if match else 0


def _auth_mode(runtime: str) -> str:
    return "api_key" if runtime in {"openai", "anthropic"} else "local"


def _optimize_prompt(body: dict[str, Any], prompt: str) -> dict[str, Any]:
    passage = str(body.get("passage") or "")
    question = str(body.get("question") or "")
    source_text = passage or prompt
    rough_tokens = source_text.split()
    if not bool(body.get("compress_context")):
        return _compression_result(prompt, False, len(rough_tokens), len(rough_tokens), 0.0, "compression disabled")
    if not passage and len(rough_tokens) <= 200:
        return _compression_result(prompt, False, len(rough_tokens), len(rough_tokens), 0.0, "short input -> full context")
    rows = route_passage(source_text, question)
    kept = [str(row["token"]) for row in rows if row.get("route_action") == "keep"]
    tokens_before = len(rows)
    tokens_after = len(kept)
    reduction = 0.0 if tokens_before == 0 else 1.0 - (tokens_after / tokens_before)
    if not kept or reduction < 0.15 or str(body.get("risk", "low")) == "high":
        return _compression_result(prompt, False, tokens_before, tokens_before, 0.0, "weak keep-set -> full context")
    compressed_text = " ".join(kept)
    return _compression_result(
        _compressed_prompt(prompt, passage, question, compressed_text),
        True,
        tokens_before,
        tokens_after,
        reduction,
        "element router compressed input context",
    )


def _compression_result(
    prompt_sent: str,
    compressed: bool,
    tokens_before: int,
    tokens_after: int,
    reduction: float,
    route_note: str,
) -> dict[str, Any]:
    return {
        "prompt_sent": prompt_sent,
        "compressed": compressed,
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "reduction": reduction,
        "route_note": route_note,
    }


def _compressed_prompt(prompt: str, passage: str, question: str, compressed_text: str) -> str:
    if passage:
        task = question or prompt
        return f"{task}\n\nCompressed passage:\n{compressed_text}"
    return compressed_text


def _prompt_optimization(body: dict[str, Any], prompt: str) -> dict[str, Any]:
    if not bool(body.get("optimize_prompt")):
        return {"prompt": prompt, "optimized": False, "optimized_prompt": "", "preserved": []}
    result = structure_prompt(prompt, task_hint=body.get("task_hint"))
    return {
        "prompt": result["structured"],
        "optimized": True,
        "optimized_prompt": result["structured"],
        "preserved": result["preserved"],
    }


def _with_compression_record(decision: HarnessDecision, compression: dict[str, Any]) -> HarnessDecision:
    if not compression["compressed"]:
        return decision
    data = decision.to_dict()
    data["validator_record"] = {
        **dict(decision.validator_record or {}),
        "input_compression": {
            "router": "routemap_token.route_passage",
            "router_mode": "element",
            "route_family": "token_element",
            "tokens_before": compression["tokens_before"],
            "tokens_after": compression["tokens_after"],
            "reduction": compression["reduction"],
            "guard": "kept non-empty and reduction >= 0.15",
        },
    }
    return HarnessDecision(**data, blocking=decision.is_blocking())


def _with_model_record(decision: HarnessDecision, model: Any) -> HarnessDecision:
    model_name = str(model or "").strip()
    if not model_name:
        return decision
    data = decision.to_dict()
    data["model"] = model_name
    return HarnessDecision(**data, blocking=decision.is_blocking())


def _run_record(
    response: dict[str, Any],
    decision: HarnessDecision,
    *,
    compression: dict[str, Any],
    model_metadata: dict[str, Any],
    runtime: str,
    model_ref: str,
) -> dict[str, Any]:
    return {
        "decision_id": decision.decision_id,
        "timestamp": decision.timestamp,
        "prompt": response["prompt"],
        "prompt_sent": response["prompt_sent"],
        "model_output": response["model_output"],
        "final_output": response["final_output"],
        "repair_attempts": response["repair_attempts"],
        "compression": {
            "compressed": compression["compressed"],
            "tokens_before": compression["tokens_before"],
            "tokens_after": compression["tokens_after"],
            "reduction": compression["reduction"],
            "route_note": compression["route_note"],
        },
        "model": {
            "runtime": model_metadata.get("runtime", runtime),
            "model_ref": model_metadata.get("model_ref", model_ref),
            "auth_mode": model_metadata.get("auth_mode", _auth_mode(runtime)),
            "latency_ms": model_metadata.get("latency_ms"),
            "cost_usd": model_metadata.get("cost_usd"),
            "tokens": model_metadata.get("tokens"),
        },
    }


def _api_decision(decision: HarnessDecision) -> dict[str, Any]:
    data = decision.to_dict()
    data["verdict"] = str(data["verdict"]).lower()
    return data


__all__ = ["app"]
