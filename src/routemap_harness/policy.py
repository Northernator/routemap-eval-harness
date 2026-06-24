"""Repair and escalation policy."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping

from dr_repair_wrapper_v1 import build_repair_prompt
from routemap_bench.tasks import exact_value_feasible
from routemap_digital import parse_expression
from routemap_validators.verdicts import NOT_RULED_OUT, RULED_OUT_WRONG, UNCHECKABLE

from .adapters import DEFAULT_MODEL_REF, ModelCallMetadata, metadata_from_response
from .core import HarnessDecision, append_audit_record, harness_check

ModelFn = Callable[..., Any]

REPAIRABLE_TASKS = {"arithmetic", "json_schema", "tool_call", "python_code"}
ESCALATION_TARGETS = {"full_compute", "deterministic_tool", "stronger_model", "human_review"}


@dataclass(frozen=True)
class RepairResult:
    final_decision: HarnessDecision
    attempts: list[HarnessDecision]
    false_accepts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_decision": self.final_decision.to_dict(),
            "attempts": [decision.to_dict() for decision in self.attempts],
            "false_accepts": self.false_accepts,
        }


def choose_policy(decision: Mapping[str, Any]) -> Mapping[str, Any]:
    """Select repair or escalation policy for a decision."""
    verdict = str(decision.get("verdict", UNCHECKABLE))
    if verdict == RULED_OUT_WRONG:
        return {"action": "repair", "final_status": "repaired"}
    if verdict == NOT_RULED_OUT:
        return {"action": "accept", "final_status": "accepted"}
    return {"action": "escalate", "final_status": "escalated"}


def decide_escalation(decision: HarnessDecision, *, model_fn_configured: bool = False) -> str:
    """Choose an escalation target for a harness decision."""
    risk = _risk(decision)
    if risk == "high":
        return "full_compute" if _deterministic_full_compute_covers(decision.task_type) else "human_review"
    if decision.task_type == "unknown":
        return "human_review"
    if decision.task_type == "arithmetic" and decision.verdict == RULED_OUT_WRONG:
        return "full_compute"
    if decision.verdict == UNCHECKABLE and decision.task_type in {"extraction", "python_code"}:
        return "stronger_model" if model_fn_configured else "human_review"
    if decision.task_type == "long_context_qa" and _route_guard_weak(decision):
        return "full_compute"
    if decision.verdict == UNCHECKABLE:
        return "human_review"
    return "human_review"


def with_escalation_target(decision: HarnessDecision, *, model_fn_configured: bool = False) -> HarnessDecision:
    """Attach escalation_target to validator_record when policy requires escalation."""
    if decision.final_status != "escalated" and decision.verdict != UNCHECKABLE and decision.action != "full_compute":
        return decision
    target = decide_escalation(decision, model_fn_configured=model_fn_configured)
    return _clone_decision(
        decision,
        validator_record={
            **dict(decision.validator_record or {}),
            "escalation_target": target,
        },
    )


def assert_guard_or_escalation_target(decision: HarnessDecision) -> None:
    """Enforce no-silent-prune invariant for accepted/repaired/pruned outputs."""
    if decision.action not in {"accept", "repair"}:
        return
    record = dict(decision.validator_record or {})
    if decision.validator or record.get("escalation_target"):
        return
    raise AssertionError("accept/repair/prune decision must name validator or escalation_target")


def repair(
    decision: HarnessDecision,
    original_payload: Mapping[str, Any],
    model_fn: ModelFn,
    *,
    max_retries: int = 2,
    audit_path: str | Path | None = None,
) -> RepairResult:
    """Repair a ruled-out/checkable payload by looping through the model adapter."""
    if decision.task_type not in REPAIRABLE_TASKS:
        escalated = _clone_decision(
            decision,
            action="escalate",
            final_status="escalated",
            reason=f"repair unsupported for task_type={decision.task_type}",
        )
        escalated = with_escalation_target(escalated, model_fn_configured=True)
        _maybe_append(audit_path, escalated)
        return RepairResult(escalated, [escalated], _false_accepts(original_payload, escalated))

    attempts: list[HarnessDecision] = []
    last_decision = decision
    for attempt in range(1, max_retries + 1):
        prompt = build_repair_prompt(_flagged(decision, original_payload), attempt)
        model_output, model_metadata = _call_model_fn(model_fn, prompt, attempt, last_decision, original_payload)
        candidate_payload = _candidate_payload(original_payload, model_output, decision.task_type)
        candidate_payload["repair_attempt"] = attempt
        repaired = harness_check(candidate_payload)
        model_record = model_metadata.to_dict()
        repaired = _clone_decision(
            repaired,
            decision_id=f"{decision.input_hash[:16]}-{attempt}",
            input_hash=decision.input_hash,
            action="repair",
            final_status="repaired" if repaired.verdict == NOT_RULED_OUT else "escalated",
            model=model_metadata.model_ref,
            tokens=model_metadata.tokens,
            cost_usd=model_metadata.cost_usd,
            validator_record={
                **dict(repaired.validator_record or {}),
                "repair_prompt": prompt,
                "repair_attempt": attempt,
                "model_call": model_record,
            },
        )
        guarded = _apply_anti_hallucination_guard(decision, original_payload, candidate_payload, repaired)
        guarded = with_escalation_target(guarded, model_fn_configured=True)
        assert_guard_or_escalation_target(guarded)
        attempts.append(guarded)
        _maybe_append(audit_path, guarded)
        last_decision = guarded
        if guarded.verdict == NOT_RULED_OUT and guarded.final_status == "repaired":
            return RepairResult(guarded, attempts, _false_accepts(original_payload, guarded))

    if decision.task_type == "arithmetic" and last_decision.verdict == RULED_OUT_WRONG:
        exact = with_escalation_target(_arithmetic_exact_decision(decision, original_payload, len(attempts) + 1))
        attempts.append(exact)
        _maybe_append(audit_path, exact)
        return RepairResult(exact, attempts, _false_accepts(original_payload, exact))

    return RepairResult(last_decision, attempts, _false_accepts(original_payload, last_decision))


def repair_stub(decision_id: str) -> Mapping[str, Any]:
    """Placeholder response when CLI lacks original payload/model output."""
    return {
        "status": "needs_input",
        "decision_id": decision_id,
        "message": "provide --input and --model-output to run offline repair",
    }


def summarize_stub(audit: str) -> Mapping[str, Any]:
    """Placeholder audit summary response for Prompt 6."""
    return {
        "status": "stub",
        "audit": audit,
        "message": "summarize is not wired until Prompt 6",
    }


def _flagged(decision: HarnessDecision, original_payload: Mapping[str, Any]) -> dict[str, Any]:
    raw_output = _raw_output(original_payload, decision.task_type)
    return {
        "domain": decision.task_type,
        "raw_output": raw_output,
        "extracted_content": raw_output,
        "checker_reason": decision.reason,
        "prompt": str(original_payload.get("prompt") or original_payload.get("expr") or original_payload.get("task") or ""),
        "verdict": decision.verdict,
    }


def _raw_output(payload: Mapping[str, Any], task_type: str) -> str:
    if task_type == "arithmetic":
        return str(payload.get("claimed_answer", ""))
    if task_type == "python_code":
        return str(payload.get("code") or payload.get("raw") or "")
    return str(payload.get("raw", ""))


def _candidate_payload(original_payload: Mapping[str, Any], model_output: Any, task_type: str) -> dict[str, Any]:
    if isinstance(model_output, Mapping) and isinstance(model_output.get("payload"), Mapping):
        return dict(model_output["payload"])
    output = _model_text(model_output)
    candidate = dict(original_payload)
    if task_type == "arithmetic":
        candidate["claimed_answer"] = _integer_output(output)
    elif task_type == "python_code":
        candidate["code"] = output
        candidate["raw"] = output
    else:
        candidate["raw"] = output
    return candidate


def _call_model_fn(
    model_fn: ModelFn,
    prompt: str,
    attempt: int,
    decision: HarnessDecision,
    original_payload: Mapping[str, Any],
) -> tuple[Any, ModelCallMetadata]:
    start = perf_counter()
    try:
        output = model_fn(
            prompt,
            model_ref=str(original_payload.get("model_ref", DEFAULT_MODEL_REF)),
            runtime=str(original_payload.get("runtime", "ollama")),
            auth_mode=str(original_payload.get("auth_mode", "local")),
            timeout=int(original_payload.get("timeout", 60)),
            strict_model=bool(original_payload.get("strict_model", False)),
            fallbacks=original_payload.get("fallbacks") if isinstance(original_payload.get("fallbacks"), list) else None,
        )
    except TypeError:
        output = model_fn(
            {
                "prompt": prompt,
                "round": attempt,
                "decision": decision.to_dict(),
                "payload": dict(original_payload),
            }
        )
    metadata = metadata_from_response(output)
    if metadata is None:
        metadata = ModelCallMetadata(
            provider="custom",
            model_ref=str(original_payload.get("model_ref", "custom")),
            runtime="callable",
            auth_mode="in_process",
            fallback_used=None,
            latency_ms=(perf_counter() - start) * 1000.0,
        )
    return output, metadata


def _model_text(model_output: Any) -> str:
    if isinstance(model_output, Mapping):
        for key in ("raw_output", "output", "raw", "code", "text"):
            if key in model_output:
                return str(model_output[key])
        return json.dumps(model_output, ensure_ascii=True, sort_keys=True)
    return str(model_output)


def _integer_output(output: str) -> int:
    match = re.search(r"[+-]?\d+", output)
    if match is None:
        return 0
    return int(match.group(0))


def _apply_anti_hallucination_guard(
    original_decision: HarnessDecision,
    original_payload: Mapping[str, Any],
    candidate_payload: Mapping[str, Any],
    repaired: HarnessDecision,
) -> HarnessDecision:
    if original_decision.task_type != "json_schema":
        return repaired
    damaged = _damaged_json_fields(original_payload, candidate_payload)
    if not damaged:
        return repaired
    return _clone_decision(
        repaired,
        verdict=UNCHECKABLE,
        action="repair",
        final_status="escalated",
        reason="repair rejected: previously valid fields became invalid: " + ", ".join(damaged),
        validator_record={
            **dict(repaired.validator_record or {}),
            "anti_hallucination_guard": {"damaged_fields": damaged},
        },
    )


def _damaged_json_fields(original_payload: Mapping[str, Any], candidate_payload: Mapping[str, Any]) -> list[str]:
    schema = original_payload.get("schema")
    if not isinstance(schema, Mapping):
        return []
    try:
        original = json.loads(str(original_payload.get("raw", "")))
        candidate = json.loads(str(candidate_payload.get("raw", "")))
    except json.JSONDecodeError:
        return []
    if not isinstance(original, dict) or not isinstance(candidate, dict):
        return []
    properties = schema.get("properties")
    if not isinstance(properties, Mapping):
        return []

    from dr_checker_schema_v1 import validate_value

    damaged: list[str] = []
    for field, field_schema in properties.items():
        if field not in original or field not in candidate or not isinstance(field_schema, Mapping):
            continue
        was_valid = not validate_value(original[field], field_schema, f"$.{field}")
        now_valid = not validate_value(candidate[field], field_schema, f"$.{field}")
        if was_valid and not now_valid:
            damaged.append(str(field))
    return damaged


def _arithmetic_exact_decision(
    decision: HarnessDecision,
    original_payload: Mapping[str, Any],
    repair_attempt: int,
) -> HarnessDecision:
    expr_spec, _modulus = parse_expression(str(original_payload.get("expr", "")))
    exact_value = exact_value_feasible(expr_spec)
    return _clone_decision(
        decision,
        decision_id=f"{decision.input_hash[:16]}-{repair_attempt}",
        repair_attempt=repair_attempt,
        route_family="full_compute",
        action="full_compute",
        final_status="escalated",
        validator="full_compute_validator",
        reason=f"repair exhausted; exact_value_feasible returned {exact_value}",
        validator_record={
            **dict(decision.validator_record or {}),
            "full_compute": {
                "engine": "routemap_bench.tasks.exact_value_feasible",
                "expr_spec": expr_spec,
                "exact_value": exact_value,
            },
            "escalation_target": "full_compute",
        },
    )


def _clone_decision(decision: HarnessDecision, **updates: Any) -> HarnessDecision:
    blocking = updates.pop("blocking", decision.is_blocking())
    data = decision.to_dict()
    data.update(updates)
    return HarnessDecision(**data, blocking=blocking)


def _false_accepts(original_payload: Mapping[str, Any], decision: HarnessDecision) -> int:
    return int(bool(original_payload.get("known_wrong")) and decision.final_status == "accepted")


def _maybe_append(audit_path: str | Path | None, decision: HarnessDecision) -> None:
    if audit_path is not None:
        append_audit_record(audit_path, decision)


def _risk(decision: HarnessDecision) -> str:
    return str(dict(decision.validator_record or {}).get("risk", "low"))


def _deterministic_full_compute_covers(task_type: str) -> bool:
    return task_type in {"arithmetic", "long_context_qa"}


def _route_guard_weak(decision: HarnessDecision) -> bool:
    record = dict(decision.validator_record or {})
    return (
        decision.task_type == "long_context_qa"
        and decision.verdict == UNCHECKABLE
        and str(record.get("validator", decision.validator)) == "answer_span_recall_guard"
    )


__all__ = [
    "ESCALATION_TARGETS",
    "RepairResult",
    "assert_guard_or_escalation_target",
    "choose_policy",
    "decide_escalation",
    "repair",
    "repair_stub",
    "summarize_stub",
    "with_escalation_target",
]
