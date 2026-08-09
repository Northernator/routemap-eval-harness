from __future__ import annotations

import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_cli_check_json_schema_appends_audit(tmp_path: Path) -> None:
    schema_path = tmp_path / "schema.json"
    payload_path = tmp_path / "payload.json"
    audit_path = tmp_path / "audit.jsonl"
    schema_path.write_text(
        json.dumps(
            {
                "type": "object",
                "required": ["id", "status"],
                "properties": {
                    "id": {"type": "string"},
                    "status": {"enum": ["pass", "fail"]},
                },
            }
        ),
        encoding="utf-8",
    )
    payload_path.write_text(json.dumps({"raw": '{"id":"x","status":"pass"}'}), encoding="utf-8")

    result = _run_cli(
        "check",
        "--task",
        "json_schema",
        "--schema",
        str(schema_path),
        "--input",
        str(payload_path),
        "--audit",
        str(audit_path),
    )

    assert result.returncode == 0, result.stderr
    decision = json.loads(result.stdout)
    assert decision["task_type"] == "json_schema"
    assert decision["verdict"] == "NOT_RULED_OUT"
    assert decision["action"] == "accept"
    assert decision["final_status"] == "accepted"

    audit_rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert [row["decision_id"] for row in audit_rows] == [decision["decision_id"]]


def test_cli_validate_config_passes() -> None:
    result = _run_cli("validate-config")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["lanes"]["extraction"] == "explicit_escalation"


def test_cli_help_explains_tasks_inputs_and_exit_codes() -> None:
    root_help = _run_cli("--help")
    check_help = _run_cli("check", "--help")

    assert root_help.returncode == 0
    assert "one-sided, auditable checks" in root_help.stdout
    assert "0 accepted/repaired, 1 rejected/escalated, 2 invalid" in root_help.stdout
    assert "preview offline token routing" in root_help.stdout
    assert check_help.returncode == 0
    assert "arithmetic, json_schema, tool_call" in check_help.stdout
    assert "JSON payload file, or - for standard input" in check_help.stdout


def test_cli_check_returns_nonzero_when_output_is_rejected(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    audit_path = tmp_path / "audit.jsonl"
    payload_path.write_text(
        json.dumps({"expr": "2 + 3", "claimed_answer": 6}),
        encoding="utf-8",
    )

    result = _run_cli(
        "check",
        "--task",
        "arithmetic",
        "--input",
        str(payload_path),
        "--audit",
        str(audit_path),
    )

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["verdict"] == "RULED_OUT_WRONG"
    assert decision["final_status"] == "rejected"
    assert len(audit_path.read_text(encoding="utf-8").splitlines()) == 1


def test_cli_check_returns_nonzero_when_output_is_escalated(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    audit_path = tmp_path / "audit.jsonl"
    payload_path.write_text(json.dumps({"raw": "unsupported"}), encoding="utf-8")

    result = _run_cli(
        "check",
        "--task",
        "unknown",
        "--input",
        str(payload_path),
        "--audit",
        str(audit_path),
    )

    assert result.returncode == 1
    decision = json.loads(result.stdout)
    assert decision["final_status"] == "escalated"


def test_cli_repair_runs_offline_model_output(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    audit_path = tmp_path / "audit.jsonl"
    payload_path.write_text(
        json.dumps(
            {
                "task_type": "json_schema",
                "raw": '{"id":"x","score":104,"status":"maybe","tags":[]}',
                "schema": {
                    "type": "object",
                    "required": ["id", "score", "status", "tags"],
                    "properties": {
                        "id": {"type": "string"},
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "status": {"enum": ["pass", "fail"]},
                        "tags": {"type": "array", "minItems": 1},
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli(
        "repair",
        "--decision-id",
        "demo",
        "--input",
        str(payload_path),
        "--audit",
        str(audit_path),
        "--model-output",
        '{"id":"x","score":88,"status":"pass","tags":["ok"]}',
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["final_decision"]["action"] == "repair"
    assert payload["final_decision"]["final_status"] == "repaired"
    assert len(payload["attempts"]) == 1
    assert len(audit_path.read_text(encoding="utf-8").splitlines()) == 1


def test_cli_repair_returns_nonzero_when_retries_are_exhausted(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    audit_path = tmp_path / "audit.jsonl"
    payload_path.write_text(
        json.dumps(
            {
                "task_type": "arithmetic",
                "expr": "2 + 3",
                "claimed_answer": 6,
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli(
        "repair",
        "--decision-id",
        "demo",
        "--input",
        str(payload_path),
        "--audit",
        str(audit_path),
        "--max-retries",
        "1",
        "--model-output",
        "6",
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["final_decision"]["final_status"] == "escalated"


def test_cli_serve_invokes_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    fake_uvicorn = types.ModuleType("uvicorn")

    def _fake_run(app: str, **kwargs: object) -> None:
        captured["app"] = app
        captured.update(kwargs)

    fake_uvicorn.run = _fake_run  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    from routemap_harness.__main__ import main

    rc = main(["serve", "--host", "0.0.0.0", "--port", "9123"])

    assert rc == 0
    assert captured["app"] == "routemap_harness.api:app"
    assert captured["host"] == "0.0.0.0"
    assert captured["port"] == 9123
    assert captured["reload"] is False


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "routemap_harness", *args],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
