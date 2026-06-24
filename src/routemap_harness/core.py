"""Core harness decision API."""

from __future__ import annotations

import json
from dataclasses import InitVar, asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping

from routemap_controller import route_decide
from routemap_token import route_passage
from routemap_validators.verdicts import NOT_RULED_OUT, RULED_OUT_WRONG, UNCHECKABLE

SCHEMA_VERSION = "harness_decision_v1"

TASK_TYPES = {
    "arithmetic",
    "json_schema",
    "python_code",
    "extraction",
    "long_context_qa",
    "retrieval",
    "unknown",
}

ROUTE_FAMILY_BY_CONTROLLER = {
    "digital_residue": "digital_residue",
    "sound_checker": "sound_checker",
    "token_importance": "token_element",
    "embedding_fingerprint": "embedding",
    "full_compute": "full_compute",
    "human_review": "human_review",
}

VERDICTS = {RULED_OUT_WRONG, NOT_RULED_OUT, UNCHECKABLE}

LANE_REGISTRY = {
    "arithmetic": "digital_residue",
    "json_schema": "sound_checker",
    "python_code": "sound_checker",
    "extraction": "explicit_escalation",
    "long_context_qa": "token_element",
    "retrieval": "embedding",
    "unknown": "explicit_escalation",
}


@dataclass(frozen=True)
class HarnessDecision:
    schema_version: str
    decision_id: str
    timestamp: str
    task_type: str
    route_family: str
    verdict: str
    action: str
    final_status: str
    validator: str
    reason: str
    input_hash: str
    repair_attempt: int
    latency_ms: float
    model: str | None = None
    tokens: int | None = None
    cost_usd: float | None = None
    validator_record: Mapping[str, Any] | None = None
    blocking: InitVar[bool] = False

    def __post_init__(self, blocking: bool) -> None:
        object.__setattr__(self, "_blocking", blocking)

    def is_blocking(self) -> bool:
        return bool(getattr(self, "_blocking", False))

    def to_dict(self) -> dict[str, Any]:
        record = asdict(self)
        return {key: value for key, value in record.items() if value is not None}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=True, sort_keys=True, default=str)


def harness_check(
    payload: dict[str, Any],
    *,
    budget: str = "balanced",
    risk: str = "low",
    router_mode: str | None = None,
    strict: bool = False,
) -> HarnessDecision:
    """Route and validate a payload with the existing RouteMap controller."""
    input_hash = _input_hash(payload)
    repair_attempt = int(payload.get("repair_attempt", 0)) if isinstance(payload, dict) else 0
    task_hint = _task_hint(payload)

    start = perf_counter()
    plan = route_decide(payload, task=task_hint, budget=budget, risk=risk, router_mode=router_mode)
    latency_ms = (perf_counter() - start) * 1000.0

    verdict = _verdict_from_outcome(str(plan.outcome))
    task_type = _task_type(task_hint or plan.task_type)
    route_family = _route_family(plan.route_family)
    action, final_status = _policy(verdict, task_type=task_type, risk=risk)
    blocking = strict and (final_status == "escalated" or verdict == UNCHECKABLE)
    validator = str(plan.validator or "")
    if not validator and action == "escalate" and task_type != "unknown":
        validator = "explicit_escalation"

    return HarnessDecision(
        schema_version=SCHEMA_VERSION,
        decision_id=f"{input_hash[:16]}-{repair_attempt}",
        timestamp=str(plan.record.get("timestamp") or _utc_now()),
        task_type=task_type,
        route_family=route_family,
        verdict=verdict,
        action=action,
        final_status=final_status,
        validator=validator,
        reason=str(plan.reason),
        input_hash=input_hash,
        repair_attempt=repair_attempt,
        latency_ms=latency_ms,
        validator_record=dict(plan.record),
        blocking=blocking,
    )


def append_audit_record(path: str | Path, decision: HarnessDecision) -> dict[str, Any]:
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    record = decision.to_dict()
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True, default=str) + "\n")
    return record


def route_tokens(passage: str, question: str, *, router: str = "element") -> dict[str, Any]:
    rows = route_passage(passage, question, router_mode=router)
    kept = [row for row in rows if row["route_action"] == "keep"]
    cheap = [row for row in rows if row["route_action"] == "cheap"]
    return {
        "router": router,
        "tokens": len(rows),
        "kept": len(kept),
        "cheap": len(cheap),
        "recall_guard": bool(kept),
        "kept_tokens": [row["token"] for row in kept],
        "cheap_tokens": [row["token"] for row in cheap],
        "rows": rows,
    }


def validate_config(schema_path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    path = Path(schema_path)
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return {"ok": False, "errors": [f"schema file unreadable: {exc}"], "lanes": dict(LANE_REGISTRY)}
    except json.JSONDecodeError as exc:
        return {"ok": False, "errors": [f"schema file is not valid JSON: {exc}"], "lanes": dict(LANE_REGISTRY)}

    schema_task_types = set(schema.get("properties", {}).get("task_type", {}).get("enum", []))
    registered_task_types = set(LANE_REGISTRY)
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        errors.append("schema is not draft 2020-12")
    if schema.get("properties", {}).get("schema_version", {}).get("const") != SCHEMA_VERSION:
        errors.append("schema_version const mismatch")
    missing = schema_task_types - registered_task_types
    extra = registered_task_types - schema_task_types
    if missing:
        errors.append("schema task_type missing from lane registry: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("lane registry task_type missing from schema: " + ", ".join(sorted(extra)))
    for task_type, lane in sorted(LANE_REGISTRY.items()):
        if not lane:
            errors.append(f"{task_type} has no lane or explicit escalation")

    return {"ok": not errors, "errors": errors, "lanes": dict(LANE_REGISTRY)}


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str)


def _input_hash(payload: Mapping[str, Any]) -> str:
    return sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _task_hint(payload: Mapping[str, Any]) -> str | None:
    task_type = payload.get("task_type")
    return str(task_type) if isinstance(task_type, str) else None


def _task_type(task_type: str) -> str:
    return task_type if task_type in TASK_TYPES else "unknown"


def _route_family(route_family: str) -> str:
    return ROUTE_FAMILY_BY_CONTROLLER.get(route_family, "full_compute")


def _verdict_from_outcome(outcome: str) -> str:
    if outcome in VERDICTS:
        return outcome
    if outcome == "accept":
        return NOT_RULED_OUT
    return UNCHECKABLE


def _policy(verdict: str, *, task_type: str, risk: str) -> tuple[str, str]:
    if risk == "high" or task_type == "unknown":
        return "escalate", "escalated"
    if verdict == RULED_OUT_WRONG:
        return "reject", "rejected"
    if verdict == NOT_RULED_OUT:
        return "accept", "accepted"
    return "escalate", "escalated"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


__all__ = [
    "HarnessDecision",
    "append_audit_record",
    "harness_check",
    "route_tokens",
    "validate_config",
]
