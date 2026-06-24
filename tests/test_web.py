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


def test_control_page_served(tmp_path: Path) -> None:
    api.app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(api.app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "RouteMap Harness Control" in response.text


def test_models_reports_ollama_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "_ollama_available", lambda: True)
    client = TestClient(api.app)

    response = client.get("/models")

    assert response.status_code == 200
    models = response.json()
    ollama = next(model for model in models if model["runtime"] == "ollama")
    assert ollama["available"] is True
    assert ollama["auth_mode"] == "local"


def test_audit_tail_returns_list(tmp_path: Path) -> None:
    api.app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(api.app)

    response = client.get("/audit")

    assert response.status_code == 200
    assert response.json() == []
