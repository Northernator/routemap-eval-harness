from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

import routemap_harness.api as api
from routemap_harness.api import app


def test_api_check_json_schema_and_audit_lookup(tmp_path: Path) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(app)

    response = client.post(
        "/check",
        json={
            "task": "json_schema",
            "model": "unit-test",
            "output": '{"id":"x","score":88,"status":"pass","tags":["ok"]}',
            "spec": {
                "type": "object",
                "required": ["id", "score", "status", "tags"],
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "status": {"enum": ["pass", "fail"]},
                    "tags": {"type": "array", "minItems": 1},
                },
            },
        },
    )

    assert response.status_code == 200
    decision = response.json()
    assert decision["schema_version"] == "harness_decision_v1"
    assert decision["task_type"] == "json_schema"
    assert decision["final_status"] == "accepted"

    audit_response = client.get(f"/audit/{decision['decision_id']}")
    assert audit_response.status_code == 200
    assert audit_response.json()["decision_id"] == decision["decision_id"]


def test_api_repair_stub(tmp_path: Path) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(app)

    response = client.post("/repair", json={"decision_id": "demo", "model_ref": "llama3.1"})

    assert response.status_code == 200
    assert response.json()["status"] == "needs_input"


def test_route_endpoint_highlights_tokens(tmp_path: Path) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(app)
    passage = (
        "the of and to the of and to "
        "The verifier must not drop negated risk statements before release. "
        "the of and to the of and to"
    )

    response = client.post(
        "/route",
        json={
            "passage": passage,
            "question": "What must the verifier not drop?",
            "router_mode": "element",
        },
    )

    assert response.status_code == 200
    body = response.json()
    rows = body["rows"]
    assert rows
    assert any(row["route_action"] == "cheap" for row in rows)
    assert any(row["route_action"] == "keep" for row in rows)
    not_row = next(row for row in rows if row["token"].lower() == "not")
    assert not_row["protected"] is True
    passage_words = {word.lower().strip(".,;:!?") for word in passage.split()}
    compressed_words = {word.lower().strip(".,;:!?") for word in body["compressed_prompt"].split()}
    assert compressed_words <= passage_words


def test_run_returns_pipeline_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")

    def fixed_answer(prompt: str, **kwargs: object) -> str:
        return "4"

    monkeypatch.setattr(api, "model_fn", fixed_answer)
    client = TestClient(app)

    response = client.post(
        "/run",
        json={
            "prompt": "2 + 2",
            "model_ref": "unit-test",
            "runtime": "ollama",
            "task_hint": "arithmetic",
        },
    )

    assert response.status_code == 200
    body = response.json()
    for key in {
        "prompt",
        "prompt_sent",
        "model_output",
        "final_output",
        "decision",
        "repair_attempts",
        "tokens_before",
        "tokens_after",
        "reduction",
        "audit_id",
    }:
        assert key in body
