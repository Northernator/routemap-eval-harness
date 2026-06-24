from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness import HarnessDecision, harness_check


JSON_SCHEMA_SPEC = {
    "type": "object",
    "required": ["id", "score", "status", "tags"],
    "properties": {
        "id": {"type": "string"},
        "score": {"type": "integer", "minimum": 0, "maximum": 100},
        "status": {"enum": ["pass", "fail"]},
        "tags": {"type": "array", "minItems": 1},
    },
}


FIXTURES = [
    pytest.param(
        "arithmetic",
        {"task_type": "arithmetic", "expr": "2 + 3", "claimed_answer": 5},
        id="arithmetic",
    ),
    pytest.param(
        "json_schema",
        {
            "task_type": "json_schema",
            "raw": '{"id":"x","score":88,"status":"pass","tags":["ok"]}',
            "schema": JSON_SCHEMA_SPEC,
        },
        id="json_schema",
    ),
    pytest.param(
        "tool_call",
        {
            "task_type": "tool_call",
            "raw": '{"name":"search_docs","arguments":"{\\"query\\":\\"route maps\\",\\"limit\\":3}"}',
            "schema": {
                "type": "object",
                "required": ["query", "limit"],
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 0},
                },
            },
            "allowed_tools": ["search_docs"],
        },
        id="tool_call",
    ),
    pytest.param(
        "grounded_qa",
        {
            "task_type": "grounded_qa",
            "answer": "RouteMap rejected 7 unsafe calls in London on 2026-06-24 [S1].",
            "source": {"S1": "The RouteMap harness rejected 7 unsafe calls in London on 2026-06-24."},
        },
        id="grounded_qa",
    ),
    pytest.param(
        "python_code",
        {"task_type": "python_code", "code": "def add(a, b):\n    return a + b\n"},
        id="python_code",
    ),
    pytest.param(
        "extraction",
        {"task_type": "extraction", "raw": '{"entity":"route","role":"checker"}'},
        id="extraction",
    ),
    pytest.param(
        "long_context_qa",
        {
            "task_type": "long_context_qa",
            "passage": "The RouteMap memo says residue checks review arithmetic claims before release.",
            "question": "What reviews arithmetic claims?",
        },
        id="long_context_qa",
    ),
    pytest.param(
        "retrieval",
        {
            "task_type": "retrieval",
            "query": "digital residue checks",
            "documents": [
                ("a", "Token routes trim low information passages."),
                ("b", "Digital residue checks arithmetic claims."),
                ("c", "Embedding routes shortlist candidates."),
            ],
        },
        id="retrieval",
    ),
]


@pytest.fixture(scope="module")
def decision_validator() -> Draft202012Validator:
    schema = json.loads((ROOT / "schemas" / "harness_decision_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(("lane", "payload"), FIXTURES)
def test_harness_check_returns_schema_valid_decision(
    lane: str,
    payload: dict[str, object],
    decision_validator: Draft202012Validator,
) -> None:
    decision = harness_check(payload)

    assert isinstance(decision, HarnessDecision)
    decision_validator.validate(decision.to_dict())
    assert decision.schema_version == "harness_decision_v1"
    assert decision.validator_record
    if lane == "extraction":
        assert decision.action == "escalate"
        assert decision.is_blocking() is False


def test_strict_escalation_is_blocking() -> None:
    decision = harness_check({"task_type": "extraction", "raw": "{}"}, strict=True)

    assert decision.final_status == "escalated"
    assert decision.is_blocking() is True
