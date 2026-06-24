#!/usr/bin/env python3
"""Run offline harness demos and write EVIDENCE/HARNESS_RESULTS.md."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import median
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from routemap_harness import harness_check
from routemap_harness.audit_store import append, summarize, validate_record
from routemap_harness.policy import repair


OUT = ROOT / "EVIDENCE"
AUDIT = OUT / "harness_demo_audit.jsonl"

DEMOS = [
    ("json_valid", "examples/json_tool_call/harness_cli_payload.json", None, None),
    ("json_repair", "examples/json_tool_call/invalid.json", None, ['{"id":"x","score":88,"status":"pass","tags":["ok"]}']),
    ("arithmetic_correct", "examples/arithmetic/correct.json", None, None),
    ("arithmetic_wrong", "examples/arithmetic/wrong.json", None, ["6", "6"]),
    ("extraction_escalate", "examples/extraction/unknown.json", None, None),
    ("long_context_answerable", "examples/long_context/answerable.json", None, None),
    ("long_context_escalate", "examples/long_context/escalate.json", None, None),
]


def main() -> int:
    OUT.mkdir(exist_ok=True)
    if AUDIT.exists():
        AUDIT.unlink()
    rows: list[dict[str, Any]] = []
    for name, rel_path, risk, repair_outputs in DEMOS:
        payload = _load(rel_path)
        decision = harness_check(payload, risk=risk or "low")
        append(decision, AUDIT)
        final = decision
        repaired = False
        if repair_outputs and decision.verdict != "NOT_RULED_OUT":
            result = repair(decision, payload, _outputs(repair_outputs), audit_path=AUDIT)
            final = result.final_decision
            repaired = final.final_status == "repaired"
        rows.append(
            {
                "name": name,
                "task_type": final.task_type,
                "label": "known_wrong" if payload.get("known_wrong") else "known_correct",
                "verdict": final.verdict,
                "action": final.action,
                "final_status": final.final_status,
                "repaired": repaired,
                "latency_ms": final.latency_ms,
            }
        )
    summary = summarize(AUDIT)
    audit_rows = _audit_rows()
    for record in audit_rows:
        validate_record(record)
    failures_caught = sum(1 for row in rows if row["label"] == "known_wrong" and row["final_status"] != "accepted")
    false_accepts = sum(1 for row in rows if row["label"] == "known_wrong" and row["final_status"] == "accepted")
    repairs = sum(1 for row in rows if row["repaired"])
    escalations = sum(1 for row in rows if row["final_status"] == "escalated" or row["action"] == "full_compute")
    latency_values = [float(row["latency_ms"]) for row in rows]
    lines = [
        "# Harness Demo Results",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| failures_caught | {failures_caught} |",
        f"| repairs | {repairs} |",
        f"| escalations | {escalations} |",
        f"| false_accepts | {false_accepts} |",
        f"| audit_completeness | {len(audit_rows)} schema-valid rows |",
        f"| latency_ms_p50 | {_percentile(latency_values, 0.50):.3f} |",
        f"| latency_ms_p95 | {_percentile(latency_values, 0.95):.3f} |",
        "",
        "| Demo | Task | Label | Verdict | Action | Final status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {row['name']} | {row['task_type']} | {row['label']} | {row['verdict']} | {row['action']} | {row['final_status']} |"
        for row in rows
    )
    lines += ["", "## Audit Summary", "", summary["markdown"]]
    (OUT / "HARNESS_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT / 'HARNESS_RESULTS.md'} with {len(audit_rows)} audit rows")
    return 1 if false_accepts else 0


def _load(rel_path: str) -> dict[str, Any]:
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def _audit_rows() -> list[dict[str, Any]]:
    return [json.loads(line) for line in AUDIT.read_text(encoding="utf-8").splitlines() if line.strip()]


def _outputs(values: list[str]):
    calls: list[int] = []

    def model_fn(_request: Mapping[str, Any]) -> str:
        index = min(len(calls), len(values) - 1)
        calls.append(index)
        return values[index]

    return model_fn


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * q)]


if __name__ == "__main__":
    raise SystemExit(main())
