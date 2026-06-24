from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness.run_store import append_run, get_run


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
