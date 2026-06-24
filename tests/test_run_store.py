from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness.run_store import append_run, export_failures, get_run


def test_append_run_get_run_round_trip(tmp_path: Path) -> None:
    runs_path = tmp_path / "runs.jsonl"
    record = {
        "decision_id": "decision-1",
        "timestamp": "2026-06-24T00:00:00Z",
        "prompt": "2 + 2",
        "prompt_sent": "2 + 2",
        "model_output": "4",
        "final_output": "4",
        "repair_attempts": [],
        "compression": {
            "compressed": False,
            "tokens_before": 3,
            "tokens_after": 3,
            "reduction": 0.0,
            "route_note": "compression disabled",
        },
        "model": {
            "runtime": "ollama",
            "model_ref": "unit-test",
            "auth_mode": "local",
            "latency_ms": 1.5,
            "cost_usd": None,
            "tokens": None,
        },
    }

    stored = append_run(record, runs_path)

    assert stored == record
    assert get_run("decision-1", runs_path) == record
    assert get_run("missing", runs_path) is None


def test_export_failures_joins_audit_and_runs(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    runs_path = tmp_path / "runs.jsonl"
    decision = {
        "decision_id": "decision-2",
        "task_type": "json_schema",
        "verdict": "RULED_OUT_WRONG",
        "reason": "score above maximum",
        "final_status": "repaired",
        "validator_record": {
            "checks": [
                {"checker": "score", "verdict": "RULED_OUT_WRONG", "reason": "too high"},
            ]
        },
    }
    audit_path.write_text(json.dumps(decision) + "\n", encoding="utf-8")
    append_run(
        {
            "decision_id": "decision-2",
            "prompt": "return json",
            "model_output": '{"score":104}',
            "final_output": '{"score":88}',
            "repair_attempts": [
                {"validator_record": {"repair_prompt": "Fix score"}},
            ],
        },
        runs_path,
    )

    rows = export_failures(audit_path, runs_path)

    assert rows == [
        {
            "prompt": "return json",
            "model_output": '{"score":104}',
            "failure_type": "json_schema:score",
            "validator_reason": "score above maximum",
            "repair_prompt": "Fix score",
            "corrected_output": '{"score":88}',
            "final_status": "repaired",
        }
    ]
