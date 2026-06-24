#!/usr/bin/env python3
"""Automated §18 harness acceptance checklist."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from routemap_harness import harness_check
from routemap_harness.audit_store import append, validate_record
from routemap_harness.policy import repair


Check = tuple[str, Callable[[], None]]


def main() -> int:
    checks: list[Check] = [
        ("requirements-dev install surface", _check_requirements_dev),
        ("check works for all lanes", _check_all_lanes),
        ("schema-valid JSONL for every decision", _check_schema_valid_jsonl),
        ("repair fixes JSON and logs rest", _check_repair),
        ("arithmetic wrong ruled out/escalated with 0 false accepts", _check_arithmetic_wrong),
        ("unknown/high-risk escalates by default", _check_escalation_defaults),
        ("run_evidence includes harness tests", _check_run_evidence),
        ("README/EVIDENCE defaults and headlines agree", _check_docs_agree),
        ("no correctness-certification wording", _check_no_certification_claims),
    ]
    rows: list[tuple[str, str, str]] = []
    for name, fn in checks:
        try:
            fn()
            rows.append((name, "PASS", ""))
        except Exception as exc:
            rows.append((name, "FAIL", str(exc)))
    lines = ["| Check | Status | Detail |", "| --- | --- | --- |"]
    lines.extend(f"| {name} | {status} | {detail} |" for name, status, detail in rows)
    print("\n".join(lines))
    return 1 if any(status == "FAIL" for _name, status, _detail in rows) else 0


def _check_requirements_dev() -> None:
    reqs = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    for dep in ("numpy", "pytest", "jsonschema"):
        assert dep in reqs, f"missing {dep}"
    assert (ROOT / "pyproject.toml").read_text(encoding="utf-8").count("routemap-harness") >= 2


def _check_all_lanes() -> None:
    lanes = set()
    for row in _gold_rows():
        decision = harness_check(row["payload"], risk=str(row.get("risk", "low")))
        lanes.add(decision.task_type)
    assert lanes == {"arithmetic", "json_schema", "python_code", "extraction", "long_context_qa", "retrieval"}


def _check_schema_valid_jsonl() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "audit.jsonl"
        for row in _gold_rows():
            decision = harness_check(row["payload"], risk=str(row.get("risk", "low")))
            record = append(decision, path)
            validate_record(record)
        assert path.exists()
        assert len(path.read_text(encoding="utf-8").splitlines()) == len(_gold_rows())


def _check_repair() -> None:
    payload = json.loads((ROOT / "examples/json_tool_call/invalid.json").read_text(encoding="utf-8"))
    decision = harness_check(payload)
    with tempfile.TemporaryDirectory() as tmp:
        result = repair(decision, payload, _outputs(['{"id":"x","score":88,"status":"pass","tags":["ok"]}']), audit_path=Path(tmp) / "repair.jsonl")
        assert result.final_decision.final_status == "repaired"
        assert result.attempts


def _check_arithmetic_wrong() -> None:
    payload = json.loads((ROOT / "examples/arithmetic/wrong.json").read_text(encoding="utf-8"))
    decision = harness_check(payload)
    assert decision.verdict == "RULED_OUT_WRONG"
    assert decision.final_status == "rejected"
    result = repair(decision, payload, _outputs(["6", "6"]), max_retries=2)
    assert result.final_decision.final_status == "escalated"
    assert result.final_decision.action == "full_compute"
    assert result.false_accepts == 0


def _check_escalation_defaults() -> None:
    unknown = harness_check({"task_type": "extraction", "raw": "unsupported"}, strict=True)
    high = harness_check({"task_type": "retrieval", "query": "x", "documents": ["x"]}, risk="high", strict=True)
    assert unknown.final_status == "escalated"
    assert unknown.is_blocking()
    assert high.final_status == "escalated"
    assert high.is_blocking()


def _check_run_evidence() -> None:
    text = (ROOT / "run_evidence.py").read_text(encoding="utf-8")
    assert "pytest: harness core+gold" in text
    assert "tests/test_harness_gold.py" in text
    assert "demo: harness CLI check" in text


def _check_docs_agree() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    evidence = (ROOT / "EVIDENCE_PACK.md").read_text(encoding="utf-8")
    for text, name in ((readme, "README"), (evidence, "EVIDENCE_PACK")):
        assert "default" in text.lower() and "element" in text.lower(), f"{name} missing default element wording"
        assert "0.000" in text, f"{name} missing FP 0.000 headline"
        assert "one-sided" in text.lower(), f"{name} missing one-sided checker wording"


def _check_no_certification_claims() -> None:
    files = [ROOT / "README.md", ROOT / "EVIDENCE_PACK.md"]
    files.extend((ROOT / "docs").glob("*.md"))
    forbidden = ("certifies correctness", "guarantees correctness", "proves correctness", "certified correct")
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        for phrase in forbidden:
            assert phrase not in text, f"{path.name} contains forbidden phrase: {phrase}"


def _gold_rows() -> list[dict[str, Any]]:
    path = ROOT / "data/harness_gold/cases.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _outputs(values: list[str]):
    calls: list[int] = []

    def model_fn(_request: Mapping[str, Any]) -> str:
        index = min(len(calls), len(values) - 1)
        calls.append(index)
        return values[index]

    return model_fn


if __name__ == "__main__":
    raise SystemExit(main())
