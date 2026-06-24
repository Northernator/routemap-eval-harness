"""Honest coverage scorecard for harness decisions."""

from __future__ import annotations

from typing import Any, Mapping


RULED_OUT_WRONG = "RULED_OUT_WRONG"
NOT_RULED_OUT = "NOT_RULED_OUT"
UNCHECKABLE = "UNCHECKABLE"


def scorecard(decision_dict: Mapping[str, Any], *, run: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Compute check coverage and failure metadata without adding schema fields."""
    decision = dict(decision_dict)
    record = dict(decision.get("validator_record") or {})
    checks = [dict(check) for check in record.get("checks", []) if isinstance(check, Mapping)]
    verdict = str(decision.get("verdict", ""))
    coverage = _validation_coverage(verdict, checks)
    hard_failures = _hard_failures(verdict, checks)
    repairs = _repair_attempts(decision, run)
    return {
        "validation_coverage": coverage,
        "hard_failures": hard_failures,
        "unchecked_claims": _unchecked_claims(verdict, checks),
        "repair_attempts": repairs,
        "escalation_required": _escalation_required(decision, verdict),
        "input_compression": _input_compression(record, run),
        "source_grounding": _source_grounding(decision, checks),
        "summary": _summary(coverage, hard_failures, repairs),
    }


def _validation_coverage(verdict: str, checks: list[dict[str, Any]]) -> float:
    if verdict == UNCHECKABLE:
        return 0.0
    if checks:
        checked = sum(1 for check in checks if str(check.get("verdict")) != UNCHECKABLE)
        return checked / len(checks)
    return 1.0 if verdict else 0.0


def _hard_failures(verdict: str, checks: list[dict[str, Any]]) -> int:
    if checks:
        return sum(1 for check in checks if str(check.get("verdict")) == RULED_OUT_WRONG)
    return int(verdict == RULED_OUT_WRONG)


def _unchecked_claims(verdict: str, checks: list[dict[str, Any]]) -> int:
    unchecked = sum(1 for check in checks if str(check.get("verdict")) == UNCHECKABLE)
    if not checks and verdict == UNCHECKABLE:
        return 1
    return unchecked


def _repair_attempts(decision: Mapping[str, Any], run: Mapping[str, Any] | None) -> int:
    run_attempts = run.get("repair_attempts") if isinstance(run, Mapping) else None
    run_count = len(run_attempts) if isinstance(run_attempts, list) else 0
    try:
        decision_count = int(decision.get("repair_attempt", 0))
    except (TypeError, ValueError):
        decision_count = 0
    return max(decision_count, run_count)


def _escalation_required(decision: Mapping[str, Any], verdict: str) -> bool:
    return (
        verdict == UNCHECKABLE
        or decision.get("action") == "escalate"
        or decision.get("final_status") == "escalated"
    )


def _input_compression(record: Mapping[str, Any], run: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    compression = record.get("input_compression")
    if isinstance(compression, Mapping):
        return dict(compression)
    run_compression = run.get("compression") if isinstance(run, Mapping) else None
    if isinstance(run_compression, Mapping):
        return dict(run_compression)
    return None


def _source_grounding(decision: Mapping[str, Any], checks: list[dict[str, Any]]) -> str:
    if decision.get("task_type") != "grounded_qa":
        return "n/a"
    applicable = [check for check in checks if str(check.get("verdict")) != UNCHECKABLE]
    if not applicable:
        return "none"
    passed = sum(1 for check in applicable if str(check.get("verdict")) == NOT_RULED_OUT)
    if passed == len(applicable):
        return "full"
    if passed:
        return "partial"
    return "none"


def _summary(coverage: float, hard_failures: int, repairs: int) -> str:
    percent = round(max(0.0, min(1.0, coverage)) * 100)
    repair_label = "repair" if repairs == 1 else "repairs"
    return (
        f"{percent}% of this output was covered by checkable routes; "
        f"{hard_failures} hard failures; {repairs} {repair_label}."
    )


__all__ = ["scorecard"]
