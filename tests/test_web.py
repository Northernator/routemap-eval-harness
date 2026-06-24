from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

import routemap_harness.api as api


def test_app_page_served(tmp_path: Path) -> None:
    api.app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(api.app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "RouteMap Harness" in response.text


def test_models_reports_ollama_available() -> None:
    client = TestClient(api.app)

    response = client.get("/models")

    assert response.status_code == 200
    models = response.json()
    ollama = next(model for model in models if model["runtime"] == "ollama")
    assert ollama["available"] is True
    assert ollama["auth_mode"] == "local"


def test_check_invalid_json_returns_schema_valid_decision(tmp_path: Path) -> None:
    api.app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(api.app)
    schema = {
        "type": "object",
        "required": ["id"],
        "properties": {"id": {"type": "string"}},
    }

    response = client.post("/check", json={"task": "json_schema", "output": "{not-json", "spec": schema})

    assert response.status_code == 200
    decision = response.json()
    decision_schema = json.loads((ROOT / "schemas" / "harness_decision_v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(decision_schema)
    Draft202012Validator(decision_schema).validate(decision)


def test_run_wrong_arithmetic_attaches_exact_correction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api.app.state.audit_path = str(tmp_path / "audit.jsonl")

    def wrong_answer(prompt: str, **kwargs: object) -> str:
        return "6"

    monkeypatch.setattr(api, "model_fn", wrong_answer)
    client = TestClient(api.app)

    response = client.post(
        "/run",
        json={"prompt": "2 + 3", "model_ref": "unit-test", "runtime": "ollama", "task_hint": "arithmetic"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"]["verdict"] == "RULED_OUT_WRONG"
    assert body["exact_correction"] == 5
    assert body["final_output"] == 5


def test_audit_tail_returns_list(tmp_path: Path) -> None:
    api.app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(api.app)

    response = client.get("/audit")

    assert response.status_code == 200
    assert response.json() == []
