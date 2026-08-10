from __future__ import annotations

import json
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


def _demo_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["id", "score", "status", "tags"],
        "properties": {
            "id": {"type": "string"},
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "status": {"enum": ["pass", "fail"]},
            "tags": {"type": "array", "minItems": 1},
        },
    }


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
    assert {
        "validation_coverage",
        "hard_failures",
        "unchecked_claims",
        "repair_attempts",
        "escalation_required",
        "input_compression",
        "source_grounding",
        "summary",
    } <= set(decision["scorecard"])

    audit_response = client.get(f"/audit/{decision['decision_id']}")
    assert audit_response.status_code == 200
    assert audit_response.json()["decision_id"] == decision["decision_id"]


def test_api_repair_runs_model_and_repairs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    monkeypatch.setattr(
        api,
        "model_fn",
        lambda prompt, **kw: '{"id":"x","score":88,"status":"pass","tags":["ok"]}',
    )
    client = TestClient(app)

    response = client.post(
        "/repair",
        json={
            "task": "json_schema",
            "output": '{"id":"x","score":104,"status":"maybe","tags":[]}',
            "spec": _demo_schema(),
            "model_ref": "unit-test",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["repaired"] is True
    assert body["attempts"]
    assert body["decision"]["final_status"] == "repaired"


def test_api_repair_no_model_returns_503(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    private_detail = "private-adapter-path:/srv/models/secret.bin"

    def boom(prompt: str, **kw: object) -> str:
        raise api.ModelAdapterUnavailable(private_detail)

    monkeypatch.setattr(api, "model_fn", boom)
    client = TestClient(app)

    response = client.post(
        "/repair",
        json={
            "task": "json_schema",
            "output": '{"id":"x","score":104,"status":"maybe","tags":[]}',
            "spec": _demo_schema(),
            "model_ref": "unit-test",
        },
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "repair needs a model (start Ollama or set an API key)"}
    assert private_detail not in response.text
    assert private_detail not in caplog.text


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


def test_check_tool_call_rejects_unsafe_path(tmp_path: Path) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(app)

    response = client.post(
        "/check",
        json={
            "task": "tool_call",
            "output": '{"name":"read_file","arguments":"{\\"path\\":\\"../etc/passwd\\"}"}',
            "spec": {
                "type": "object",
                "required": ["path"],
                "properties": {"path": {"type": "string"}},
            },
            "allowed_tools": ["read_file"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_type"] == "tool_call"
    assert body["verdict"] == "RULED_OUT_WRONG"
    assert "unsafe path" in body["reason"]


def test_check_grounded_qa_names_missing_items(tmp_path: Path) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    client = TestClient(app)

    response = client.post(
        "/check",
        json={
            "task": "grounded_qa",
            "output": "RouteMap rejected 9 unsafe calls in Paris on 2026-06-24 [S1].",
            "source": {"S1": "The RouteMap harness rejected 7 unsafe calls in London on 2026-06-24."},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_type"] == "grounded_qa"
    assert body["route_family"] == "grounding"
    assert body["verdict"] == "RULED_OUT_WRONG"
    assert "Paris" in body["reason"]
    assert "9" in body["reason"]


def test_run_returns_pipeline_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")

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


def test_run_persists_run_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")

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
    audit_id = response.json()["audit_id"]

    replay_response = client.get(f"/replay/{audit_id}")

    assert replay_response.status_code == 200
    replay = replay_response.json()
    assert replay["decision"]["decision_id"] == audit_id
    assert replay["run"]["decision_id"] == audit_id
    assert replay["run"]["prompt"] == "2 + 2"
    assert replay["run"]["model_output"] == "4"
    assert replay["run"]["compression"]["compressed"] is False
    assert replay["run"]["model"]["model_ref"] == "unit-test"


def test_run_optimizes_prompt_when_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")
    prompts: list[str] = []

    def fixed_answer(prompt: str, **kwargs: object) -> str:
        prompts.append(prompt)
        return "done"

    monkeypatch.setattr(api, "model_fn", fixed_answer)
    client = TestClient(app)

    response = client.post(
        "/run",
        json={
            "prompt": "Summarize Acme report 42 from 2026 and do not omit [7].",
            "model_ref": "unit-test",
            "runtime": "ollama",
            "task_hint": "extraction",
            "optimize_prompt": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["optimized"] is True
    assert body["optimized_prompt"]
    assert "Preserve exactly:" in body["optimized_prompt"]
    assert {"Acme", "42", "2026", "not", "[7]"} <= set(body["preserved"])
    assert prompts and prompts[0] == body["optimized_prompt"]


def test_replay_404_for_unknown_id(tmp_path: Path) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")
    client = TestClient(app)

    response = client.get("/replay/missing")

    assert response.status_code == 404


def test_export_failures_returns_ndjson(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")

    def wrong_answer(prompt: str, **kwargs: object) -> str:
        return "6"

    monkeypatch.setattr(api, "model_fn", wrong_answer)
    client = TestClient(app)
    run_response = client.post(
        "/run",
        json={
            "prompt": "2 + 3",
            "model_ref": "unit-test",
            "runtime": "ollama",
            "task_hint": "arithmetic",
        },
    )
    assert run_response.status_code == 200

    response = client.get("/export/failures")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    lines = [line for line in response.text.splitlines() if line.strip()]
    rows = [json.loads(line) for line in lines]
    assert rows
    assert {
        "prompt",
        "model_output",
        "failure_type",
        "validator_reason",
        "repair_prompt",
        "corrected_output",
        "final_status",
    } <= set(rows[0])


def test_summary_endpoint_aggregates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")

    def valid_json(prompt: str, **kwargs: object) -> str:
        return '{"id":"x","score":88,"status":"pass","tags":["ok"]}'

    monkeypatch.setattr(api, "model_fn", valid_json)
    client = TestClient(app)
    spec = {
        "type": "object",
        "required": ["id", "score", "status", "tags"],
        "properties": {
            "id": {"type": "string"},
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "status": {"enum": ["pass", "fail"]},
            "tags": {"type": "array", "minItems": 1},
        },
    }

    check_response = client.post(
        "/check",
        json={
            "task": "json_schema",
            "model": "check-model",
            "output": '{"id":"x","score":88,"status":"pass","tags":["ok"]}',
            "spec": spec,
        },
    )
    run_response = client.post(
        "/run",
        json={
            "prompt": "return valid json",
            "model_ref": "run-model",
            "runtime": "ollama",
            "task_hint": "json_schema",
            "spec": spec,
        },
    )
    summary_response = client.get("/summary")

    assert check_response.status_code == 200
    assert run_response.status_code == 200
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert summary["total"] == 2
    assert summary["counts"]["task_type"]["json_schema"] == 2
    assert summary["counts"]["final_status"]["accepted"] == 2
    assert summary["by_model"]["check-model"]["total"] == 1
    assert summary["by_model"]["run-model"]["total"] == 1
    assert summary["by_model"]["run-model"]["counts"]["verdict"]["NOT_RULED_OUT"] == 1
    assert "markdown" in summary


def test_compare_runs_each_model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")

    def echo_model_ref(prompt: str, **kwargs: object) -> str:
        return str(kwargs["model_ref"])

    monkeypatch.setattr(api, "model_fn", echo_model_ref)
    client = TestClient(app)

    response = client.post(
        "/compare",
        json={
            "prompt": "Compare this output.",
            "task_hint": "extraction",
            "models": [
                {"runtime": "ollama", "model_ref": "model-a"},
                {"runtime": "ollama", "model_ref": "model-b"},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    assert {result["model_output"] for result in body["results"]} == {"model-a", "model-b"}
    assert all(result["available"] is True for result in body["results"])
    assert all("decision" in result for result in body["results"])


def test_compare_isolates_model_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app.state.audit_path = str(tmp_path / "audit.jsonl")
    app.state.runs_path = str(tmp_path / "runs.jsonl")
    private_detail = "private-adapter-path:/srv/models/secret.bin"

    def maybe_fail(prompt: str, **kwargs: object) -> str:
        if kwargs["model_ref"] == "bad-model":
            raise api.ModelAdapterUnavailable(private_detail)
        return "ok"

    monkeypatch.setattr(api, "model_fn", maybe_fail)
    client = TestClient(app)

    response = client.post(
        "/compare",
        json={
            "prompt": "Compare this output.",
            "task_hint": "extraction",
            "models": [
                {"runtime": "ollama", "model_ref": "bad-model"},
                {"runtime": "ollama", "model_ref": "good-model"},
            ],
        },
    )

    assert response.status_code == 200
    results = response.json()["results"]
    failed = next(result for result in results if result["model_ref"] == "bad-model")
    ok = next(result for result in results if result["model_ref"] == "good-model")
    assert failed["available"] is False
    assert failed["error"] == "model unavailable"
    assert private_detail not in response.text
    assert private_detail not in caplog.text
    assert ok["available"] is True
    assert ok["model_output"] == "ok"
