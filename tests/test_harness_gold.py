from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data" / "harness_gold"
sys.path.insert(0, str(ROOT / "src"))

from routemap_harness import harness_check


def test_harness_gold_zero_false_accepts_and_fp_rate() -> None:
    _verify_manifest()
    rows = _load_cases()
    false_accepts = 0
    sound_wrong = 0
    sound_false_positive = 0

    for row in rows:
        decision = harness_check(
            row["payload"],
            risk=str(row.get("risk", "low")),
            model_fn=_model_fn(row) if row.get("repair_outputs") else None,
        )
        is_wrong = row["label"] == "known_wrong"
        if is_wrong and decision.final_status == "accepted":
            false_accepts += 1
        if row["sound_lane"] and is_wrong:
            sound_wrong += 1
            if decision.final_status == "accepted":
                sound_false_positive += 1

    false_positive_rate = sound_false_positive / max(1, sound_wrong)
    assert false_accepts == 0
    assert f"{false_positive_rate:.3f}" == "0.000"


def test_harness_gold_has_each_lane_and_label() -> None:
    _verify_manifest()
    rows = _load_cases()
    lanes = {row["lane"] for row in rows}
    labels_by_lane = {lane: {row["label"] for row in rows if row["lane"] == lane} for lane in lanes}

    assert lanes == {"arithmetic", "json_schema", "python_code", "extraction", "long_context_qa", "retrieval"}
    for labels in labels_by_lane.values():
        assert labels == {"known_correct", "known_wrong"}


def _verify_manifest() -> None:
    for line in (GOLD / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, rel_path = line.split(maxsplit=1)
        actual = hashlib.sha256((GOLD / rel_path).read_bytes()).hexdigest()
        assert actual == expected, f"frozen harness gold hash mismatch: {rel_path}"


def _load_cases() -> list[dict[str, Any]]:
    return [json.loads(line) for line in (GOLD / "cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def _model_fn(row: Mapping[str, Any]):
    outputs = list(row.get("repair_outputs", []))
    calls: list[int] = []

    def model_fn(_request: Mapping[str, Any]) -> str:
        index = min(len(calls), len(outputs) - 1)
        calls.append(index)
        return str(outputs[index])

    return model_fn
