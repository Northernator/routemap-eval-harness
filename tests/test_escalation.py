from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness import HarnessDecision, harness_check
from routemap_harness.policy import (
    assert_guard_or_escalation_target,
    decide_escalation,
    repair,
    with_escalation_target,
)


def test_high_risk_unknown_escalates_to_human_review() -> None:
    decision = harness_check({"note": "no supported route signature"}, risk="high")

    assert decision.final_status == "escalated"
    assert decide_escalation(decision) == "human_review"
    assert decision.validator_record["escalation_target"] == "human_review"


def test_high_risk_arithmetic_uses_full_compute() -> None:
    decision = harness_check({"task_type": "arithmetic", "expr": "2 + 3", "claimed_answer": 5}, risk="high")

    assert decision.final_status == "escalated"
    assert decide_escalation(decision) == "full_compute"
    assert decision.validator_record["escalation_target"] == "full_compute"


def test_arithmetic_ruled_out_after_repair_escalates_to_full_compute() -> None:
    payload = {"task_type": "arithmetic", "expr": "2 + 3", "claimed_answer": 6}
    decision = harness_check(payload)

    result = repair(decision, payload, lambda _request: "6", max_retries=1)

    assert result.final_decision.action == "full_compute"
    assert decide_escalation(result.final_decision) == "full_compute"
    assert result.final_decision.validator_record["escalation_target"] == "full_compute"


def test_uncheckable_extraction_targets_model_when_configured_else_human() -> None:
    decision = _decision(task_type="extraction", verdict="UNCHECKABLE", validator="", action="escalate")

    assert decide_escalation(decision) == "human_review"
    assert decide_escalation(decision, model_fn_configured=True) == "stronger_model"
    annotated = with_escalation_target(decision, model_fn_configured=True)
    assert annotated.validator_record["escalation_target"] == "stronger_model"


def test_uncheckable_code_targets_stronger_model_when_configured() -> None:
    decision = _decision(task_type="python_code", verdict="UNCHECKABLE", validator="python_code_parse_v1")

    assert decide_escalation(decision, model_fn_configured=True) == "stronger_model"


def test_long_context_weak_guard_targets_full_compute() -> None:
    decision = _decision(
        task_type="long_context_qa",
        verdict="UNCHECKABLE",
        validator="answer_span_recall_guard",
        validator_record={"risk": "low", "validator": "answer_span_recall_guard"},
    )

    assert decide_escalation(decision) == "full_compute"
    assert with_escalation_target(decision).validator_record["escalation_target"] == "full_compute"


def test_accept_repair_prune_decisions_must_have_validator_or_escalation_target() -> None:
    accepted = harness_check(
        {
            "task_type": "retrieval",
            "query": "digital residue",
            "documents": ["Digital residues verify arithmetic claims."],
        }
    )
    assert accepted.action == "accept"
    assert accepted.validator
    assert_guard_or_escalation_target(accepted)

    with pytest.raises(AssertionError):
        assert_guard_or_escalation_target(_decision(verdict="NOT_RULED_OUT", action="accept", validator=""))

    explicit_target = _decision(
        verdict="UNCHECKABLE",
        action="repair",
        validator="",
        final_status="escalated",
        validator_record={"risk": "low", "escalation_target": "human_review"},
    )
    assert_guard_or_escalation_target(explicit_target)


def _decision(
    *,
    task_type: str = "unknown",
    verdict: str = "UNCHECKABLE",
    action: str = "escalate",
    final_status: str = "escalated",
    validator: str = "",
    validator_record: dict[str, object] | None = None,
) -> HarnessDecision:
    return HarnessDecision(
        schema_version="harness_decision_v1",
        decision_id="test-0",
        timestamp="2026-06-24T00:00:00Z",
        task_type=task_type,
        route_family="full_compute",
        verdict=verdict,
        action=action,
        final_status=final_status,
        validator=validator,
        reason="test",
        input_hash="0" * 64,
        repair_attempt=0,
        latency_ms=0.0,
        validator_record=validator_record or {"risk": "low"},
    )
