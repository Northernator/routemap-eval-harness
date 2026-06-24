from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import routemap_harness.adapters as adapters
from routemap_harness import harness_check
from routemap_harness.adapters import ModelAdapterError, metadata_from_response, model_fn


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


def test_ollama_adapter_model_fn_contract_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_ollama(prompt: str, *, model_ref: str, timeout: int = 60):
        assert prompt == "repair this"
        assert model_ref == "llama3.1"
        assert timeout == 7
        return "fixed", {"tokens": 12}

    monkeypatch.setattr(adapters, "ollama_adapter", fake_ollama)

    response = model_fn("repair this", model_ref="llama3.1", runtime="ollama", auth_mode="local", timeout=7)

    assert isinstance(response, str)
    assert response == "fixed"
    metadata = metadata_from_response(response)
    assert metadata is not None
    assert metadata.provider == "ollama"
    assert metadata.model_ref == "llama3.1"
    assert metadata.runtime == "ollama"
    assert metadata.auth_mode == "local"
    assert metadata.fallback_used is None
    assert metadata.tokens == 12


def test_model_call_metadata_is_copied_into_repair_decision(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_ollama(prompt: str, *, model_ref: str, timeout: int = 60):
        return '{"id":"x","score":88,"status":"pass","tags":["ok"]}', {"tokens": 17}

    monkeypatch.setattr(adapters, "ollama_adapter", fake_ollama)
    payload = {
        "task_type": "json_schema",
        "raw": '{"id":"x","score":104,"status":"maybe","tags":[]}',
        "schema": SCHEMA,
        "model_ref": "llama3.1",
    }

    decision = harness_check(payload, model_fn=model_fn)

    assert decision.final_status == "repaired"
    assert decision.model == "llama3.1"
    assert decision.tokens == 17
    assert decision.validator_record["model_call"]["provider"] == "ollama"
    assert decision.validator_record["model_call"]["runtime"] == "ollama"
    assert "latency_ms" in decision.validator_record["model_call"]


def test_strict_model_raises_instead_of_falling_back(monkeypatch: pytest.MonkeyPatch) -> None:
    def failing_ollama(prompt: str, *, model_ref: str, timeout: int = 60):
        raise ModelAdapterError("primary failed")

    monkeypatch.setattr(adapters, "ollama_adapter", failing_ollama)

    with pytest.raises(ModelAdapterError):
        model_fn(
            "repair this",
            model_ref="missing",
            runtime="ollama",
            auth_mode="local",
            strict_model=True,
            fallbacks=["fallback-model"],
        )
