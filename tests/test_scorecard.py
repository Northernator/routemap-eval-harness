from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness.scorecard import scorecard


def test_json_schema_scorecard_counts_hard_failures() -> None:
    decision = {
        "task_type": "json_schema",
        "verdict": "RULED_OUT_WRONG",
        "action": "repair",
        "final_status": "repaired",
        "repair_attempt": 1,
        "validator_record": {
            "checks": [
                {"checker": "required", "verdict": "NOT_RULED_OUT", "reason": "id present"},
                {"checker": "score", "verdict": "RULED_OUT_WRONG", "reason": "score too high"},
            ]
        },
    }

    card = scorecard(decision)

    assert 0.0 <= card["validation_coverage"] <= 1.0
    assert card["validation_coverage"] == 1.0
    assert card["hard_failures"] == 1
    assert card["repair_attempts"] == 1
    assert "correct" not in card["summary"].lower()


def test_uncheckable_scorecard_requires_escalation() -> None:
    decision = {
        "task_type": "unknown",
        "verdict": "UNCHECKABLE",
        "action": "escalate",
        "final_status": "escalated",
        "repair_attempt": 0,
        "validator_record": {"checks": []},
    }

    card = scorecard(decision)

    assert card["validation_coverage"] == 0.0
    assert card["unchecked_claims"] == 1
    assert card["escalation_required"] is True
    assert "correct" not in card["summary"].lower()
