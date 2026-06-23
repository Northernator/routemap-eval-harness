from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from routemap_validators import AuditLog, Verdict, check_output, to_record, validate_record
from routemap_validators.run_regression import (
    check_exact_multiple_soundness,
    check_hardening,
    pass_but_wrong_count,
    regression_table,
    rescore_slice05,
    smoke_imports,
)


def test_slice05_regression_matches_locked_summary() -> None:
    decisions, summary, expected = rescore_slice05()
    table = regression_table(summary, expected)
    assert all(row["status"] == "PASS" for row in table)
    assert pass_but_wrong_count(decisions) == 0


def test_hardening_battery_and_combined_modulus_soundness() -> None:
    hardening = check_hardening()
    assert hardening["standard_catch_rate"] == "1.000"
    assert hardening["false_positive_rate"] == "0.000"
    assert hardening["combined_modulus_not_ruled_out"] is True
    assert check_exact_multiple_soundness() == Verdict.NOT_RULED_OUT


def test_extraction_failure_is_uncheckable_not_ruled_out() -> None:
    raw = "Here is the code:\n```\n\n```\ndef f_0(a, b): return a + b"
    decision = check_output(raw, "python_code", object_id="cascade_fixed")
    assert decision.verdict == Verdict.UNCHECKABLE
    assert decision.extraction_ok is False
    assert decision.checker is None
    validate_record(decision.record)


def test_audit_record_validates_and_writes_jsonl(tmp_path: Path) -> None:
    decision = check_output("42", "arithmetic", {"family": "bigsum", "values": [40, 2]}, object_id="audit_smoke")
    validate_record(decision.record)
    assert decision.record == to_record(decision)
    path = tmp_path / "audit.jsonl"
    AuditLog(path).append(decision.record)
    record = json.loads(path.read_text(encoding="utf-8").strip())
    validate_record(record)


def test_existing_dr_and_evaluate_modules_still_import() -> None:
    assert smoke_imports() == []
