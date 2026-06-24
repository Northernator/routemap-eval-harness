from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness.audit_store import append, summarize, summarize_records, validate_record


def test_append_validates_every_record_and_summarizes(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    records = [
        _record("accepted", action="accept", task_type="json_schema", route_family="sound_checker", verdict="NOT_RULED_OUT", latency_ms=10.0),
        _record("rejected", action="reject", task_type="arithmetic", route_family="digital_residue", verdict="RULED_OUT_WRONG", latency_ms=20.0),
        _record("escalated", action="escalate", task_type="unknown", route_family="full_compute", verdict="UNCHECKABLE", validator="", latency_ms=30.0),
        _record("repaired", action="repair", task_type="json_schema", route_family="sound_checker", verdict="NOT_RULED_OUT", repair_attempt=1, latency_ms=40.0),
        _record("failed", action="retry", task_type="python_code", route_family="sound_checker", verdict="UNCHECKABLE", latency_ms=50.0),
    ]

    for record in records:
        append(record, audit_path)

    schema = json.loads((ROOT / "schemas" / "harness_decision_v1.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    rows = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 5
    for row in rows:
        validator.validate(row)
        validate_record(row)

    summary = summarize(audit_path)
    assert summary["total"] == 5
    assert summary["counts"]["final_status"] == {
        "accepted": 1,
        "rejected": 1,
        "escalated": 1,
        "repaired": 1,
        "failed": 1,
    }
    assert summary["counts"]["task_type"]["json_schema"] == 2
    assert summary["counts"]["route_family"]["sound_checker"] == 3
    assert summary["counts"]["verdict"]["UNCHECKABLE"] == 2
    assert summary["counts"]["action"]["repair"] == 1
    assert summary["repair_success_rate"] == 1.0
    assert summary["escalation_rate"] == 0.2
    assert summary["false_accepts"] == 0
    assert summary["latency_ms"]["p50"] == 30.0
    assert summary["latency_ms"]["p95"] == 50.0
    assert "| final_status | repaired | 1 |" in summary["markdown"]


def test_append_raises_on_invalid_record(tmp_path: Path) -> None:
    record = _record("accepted")
    del record["latency_ms"]

    with pytest.raises(ValueError):
        append(record, tmp_path / "audit.jsonl")


def test_summarize_records_has_by_model() -> None:
    false_accept = _record("accepted", model="model-a")
    false_accept["validator_record"] = {"schema_version": "route_decision_v1", "known_wrong": True}
    records = [
        false_accept,
        _record("repaired", action="repair", repair_attempt=1, model="model-a"),
        _record("escalated", action="escalate", verdict="UNCHECKABLE", model="model-b"),
    ]

    summary = summarize_records(records)

    assert summary["total"] == 3
    assert summary["by_model"]["model-a"]["total"] == 2
    assert summary["by_model"]["model-a"]["counts"]["final_status"]["accepted"] == 1
    assert summary["by_model"]["model-a"]["counts"]["action"]["repair"] == 1
    assert summary["by_model"]["model-a"]["false_accepts"] == 1
    assert summary["by_model"]["model-a"]["repair_success_rate"] == 1.0
    assert summary["by_model"]["model-b"]["counts"]["verdict"]["UNCHECKABLE"] == 1


def test_cli_summarize_prints_markdown_table(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    append(_record("accepted", action="accept"), audit_path)

    result = _run_cli("summarize", "--audit", str(audit_path))

    assert result.returncode == 0, result.stderr
    assert "| metric | value | count |" in result.stdout
    assert "| final_status | accepted | 1 |" in result.stdout


def _record(
    final_status: str,
    *,
    action: str = "accept",
    task_type: str = "retrieval",
    route_family: str = "embedding",
    verdict: str = "NOT_RULED_OUT",
    validator: str = "test_validator",
    repair_attempt: int = 0,
    latency_ms: float = 1.0,
    model: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": "harness_decision_v1",
        "decision_id": f"{final_status}-{repair_attempt}",
        "timestamp": "2026-06-24T00:00:00Z",
        "task_type": task_type,
        "route_family": route_family,
        "verdict": verdict,
        "action": action,
        "final_status": final_status,
        "validator": validator,
        "reason": "test",
        "input_hash": "0" * 64,
        "repair_attempt": repair_attempt,
        "latency_ms": latency_ms,
        "validator_record": {"schema_version": "route_decision_v1", "known_wrong": False},
    }
    if model is not None:
        record["model"] = model
    return record


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
