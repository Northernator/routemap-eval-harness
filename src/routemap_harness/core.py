"""Core harness decision API."""

from __future__ import annotations

import json
from dataclasses import InitVar, asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from time import perf_counter
from typing import Any, Mapping

from routemap_controller import route_decide
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
    task_type = _task_type(plan.task_type)
    route_family = _route_family(plan.route_family)
    action, final_status = _policy(verdict, task_type=task_type, risk=risk)
    blocking = strict and (final_status == "escalated" or verdict == UNCHECKABLE)

    return HarnessDecision(
        schema_version=SCHEMA_VERSION,
        decision_id=f"{input_hash[:16]}-{repair_attempt}",
        timestamp=str(plan.record.get("timestamp") or _utc_now()),
        task_type=task_type,
        route_family=route_family,
        verdict=verdict,
        action=action,
        final_status=final_status,
        validator=str(plan.validator),
        reason=str(plan.reason),
        input_hash=input_hash,
        repair_attempt=repair_attempt,
        latency_ms=latency_ms,
        validator_record=dict(plan.record),
        blocking=blocking,
    )


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


__all__ = ["HarnessDecision", "harness_check"]
