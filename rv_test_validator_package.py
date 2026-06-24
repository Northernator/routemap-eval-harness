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


TOOL_CALL_SCHEMA = {
    "type": "object",
    "required": ["query", "limit", "start_date"],
    "properties": {
        "query": {"type": "string"},
        "limit": {"type": "integer", "minimum": 0},
        "start_date": {"type": "string", "format": "date"},
        "path": {"type": "string"},
    },
}


def _tool_call(arguments: dict[str, object], name: str = "search_docs") -> str:
    return json.dumps({"name": name, "arguments": json.dumps(arguments)})


def test_tool_call_firewall_valid_call_passes() -> None:
    decision = check_output(
        _tool_call({"query": "route maps", "limit": 3, "start_date": "2026-06-24"}),
        "tool_call",
        {"schema": TOOL_CALL_SCHEMA, "allowed_tools": ["search_docs"]},
        object_id="tool_valid",
    )

    assert decision.verdict == Verdict.NOT_RULED_OUT
    assert decision.checker == "tool_call_firewall"
    validate_record(decision.record)


def test_tool_call_firewall_missing_required_field_rejected() -> None:
    decision = check_output(
        _tool_call({"query": "route maps", "limit": 3}),
        "tool_call",
        {"schema": TOOL_CALL_SCHEMA, "allowed_tools": ["search_docs"]},
    )

    assert decision.verdict == Verdict.RULED_OUT_WRONG
    assert "schema violation" in decision.reason
    assert "start_date" in decision.reason


def test_tool_call_firewall_unsafe_path_rejected() -> None:
    decision = check_output(
        _tool_call({"query": "route maps", "limit": 3, "start_date": "2026-06-24", "path": "../etc/passwd"}),
        "tool_call",
        {"schema": TOOL_CALL_SCHEMA, "allowed_tools": ["search_docs"]},
    )

    assert decision.verdict == Verdict.RULED_OUT_WRONG
    assert "unsafe path" in decision.reason


def test_tool_call_firewall_disallowed_tool_rejected() -> None:
    decision = check_output(
        _tool_call({"query": "route maps", "limit": 3, "start_date": "2026-06-24"}, name="delete_file"),
        "tool_call",
        {"schema": TOOL_CALL_SCHEMA, "allowed_tools": ["search_docs"]},
    )

    assert decision.verdict == Verdict.RULED_OUT_WRONG
    assert "disallowed tool" in decision.reason
    assert "delete_file" in decision.reason


def test_tool_call_firewall_invalid_date_rejected() -> None:
    decision = check_output(
        _tool_call({"query": "route maps", "limit": 3, "start_date": "2026-99-99"}),
        "tool_call",
        {"schema": TOOL_CALL_SCHEMA, "allowed_tools": ["search_docs"]},
    )

    assert decision.verdict == Verdict.RULED_OUT_WRONG
    assert "invalid ISO date" in decision.reason
