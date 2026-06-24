from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

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
