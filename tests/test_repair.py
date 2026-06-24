from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness import harness_check
from routemap_harness.policy import repair


SCHEMA = {
    "type": "object",
    "required": ["id", "score", "status", "tags"],
    "properties": {
        "id": {"type": "string"},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "status": {"enum": ["pass", "fail"]},
        "tags": {"type": "array", "minItems": 1},
    },
}


def test_json_schema_failure_repairs_to_valid() -> None:
    payload = {
        "task_type": "json_schema",
        "raw": '{"id":"x","score":104,"status":"maybe","tags":[]}',
        "schema": SCHEMA,
    }
    decision = harness_check(payload)

    result = repair(decision, payload, _outputs('{"id":"x","score":88,"status":"pass","tags":["ok"]}'))

    assert result.final_decision.verdict == "NOT_RULED_OUT"
    assert result.final_decision.action == "repair"
    assert result.final_decision.final_status == "repaired"
    assert result.final_decision.input_hash == decision.input_hash
    assert result.final_decision.repair_attempt == 1
    assert result.false_accepts == 0


def test_arithmetic_stays_wrong_escalates_to_exact_compute() -> None:
    payload = {"task_type": "arithmetic", "expr": "2 + 3", "claimed_answer": 6, "known_wrong": True}
    decision = harness_check(payload)

    result = repair(decision, payload, _outputs("6", "6"), max_retries=2)

    assert result.final_decision.verdict == "RULED_OUT_WRONG"
    assert result.final_decision.action == "full_compute"
    assert result.final_decision.final_status == "escalated"
    assert result.final_decision.repair_attempt == 3
    assert result.final_decision.validator_record["full_compute"]["engine"] == "routemap_bench.tasks.exact_value_feasible"
    assert result.final_decision.validator_record["full_compute"]["exact_value"] == 5
    assert result.false_accepts == 0


def test_repair_rejects_newly_invalid_previously_valid_field() -> None:
    payload = {
        "task_type": "json_schema",
        "raw": '{"id":"x","score":104,"status":"pass","tags":["ok"]}',
        "schema": SCHEMA,
    }
    decision = harness_check(payload)

    result = repair(decision, payload, _outputs('{"id":7,"score":90,"status":"pass","tags":["ok"]}'), max_retries=1)

    assert result.final_decision.verdict == "UNCHECKABLE"
    assert result.final_decision.action == "repair"
    assert result.final_decision.final_status == "escalated"
    assert "previously valid fields became invalid: id" in result.final_decision.reason
    assert result.final_decision.validator_record["anti_hallucination_guard"]["damaged_fields"] == ["id"]


def test_harness_check_can_run_repair_loop_with_model_fn() -> None:
    payload = {
        "task_type": "json_schema",
        "raw": '{"id":"x","score":104,"status":"maybe","tags":[]}',
        "schema": SCHEMA,
    }

    decision = harness_check(payload, model_fn=_outputs('{"id":"x","score":88,"status":"pass","tags":["ok"]}'))

    assert decision.verdict == "NOT_RULED_OUT"
    assert decision.action == "repair"
    assert decision.final_status == "repaired"
    assert decision.repair_attempt == 1


def _outputs(*values: str):
    calls: list[int] = []

    def model_fn(_request: Mapping[str, Any]) -> str:
        index = min(len(calls), len(values) - 1)
        calls.append(index)
        return values[index]

    return model_fn
