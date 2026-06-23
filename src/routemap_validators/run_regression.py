"""Offline regression runner for the RouteMap validator package."""

from __future__ import annotations

import argparse
import ast
import csv
import importlib
import json
from pathlib import Path
from typing import Any

from dr_generate_corpus_v1 import DOMAINS
from dr_residue_engine_v1 import DEFAULT_MODULI

from . import AuditLog, check_output, validate_record
from .verdicts import Verdict


ROOT = Path(__file__).resolve().parents[2]
SLICE05 = ROOT / "data" / "v1" / "digital_route" / "slice_05_scale"
SLICE02 = ROOT / "data" / "v1" / "digital_route" / "slice_02_hardening"
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_07_validator_package"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.000"
    return f"{numerator / denominator:.3f}"


def rescore_slice05() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    corpus = read_jsonl(SLICE05 / "corpus.jsonl")
    decisions: list[dict[str, Any]] = []
    for row in corpus:
        spec = row.get("expr_spec") if row["domain"] == "arithmetic" else row.get("schema")
        decision = check_output(
            row.get("raw_output", ""),
            row["domain"],
            spec,
            object_id=row.get("task_id"),
            model=row.get("model"),
        )
        validate_record(decision.record)
        decisions.append({"row": row, "decision": decision})
    summary = summarize_slice05(decisions)
    expected = json.loads((SLICE05 / "summary.json").read_text(encoding="utf-8-sig"))
    return decisions, summary, expected


def summarize_slice05(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    target_n = max(len([item for item in items if item["row"]["domain"] == domain]) for domain in DOMAINS)
    for domain in DOMAINS:
        domain_items = [item for item in items if item["row"]["domain"] == domain]
        completed = [item for item in domain_items if item["row"].get("status") == "completed"]
        extracted = [item for item in completed if item["decision"].extraction_ok]
        ruled_out = [item for item in extracted if item["decision"].verdict == Verdict.RULED_OUT_WRONG]
        uncheckable = [item for item in domain_items if item["decision"].verdict == Verdict.UNCHECKABLE]
        valid = [item for item in extracted if actually_valid(item)]
        false_positive = [item for item in valid if item["decision"].verdict == Verdict.RULED_OUT_WRONG]
        if false_positive:
            raise AssertionError("practical false-positive detected")
        summary.append(
            {
                "domain": domain,
                "target_n": target_n,
                "cached_n": len(domain_items),
                "completed_n": len(completed),
                "partial": "1" if len(completed) < target_n else "0",
                "completed_generation_rate": rate(len(completed), target_n),
                "extraction_success_rate_completed": rate(len(extracted), len(completed)),
                "content_rule_out_rate_extracted": rate(len(ruled_out), len(extracted)),
                "uncheckable_rate_cached": rate(len(uncheckable), len(domain_items)),
                "practical_false_positive_rate": rate(len(false_positive), len(valid)),
                "valid_extracted_n": len(valid),
                "ruled_out_n": len(ruled_out),
                "uncheckable_n": len(uncheckable),
            }
        )
    return summary


def actually_valid(item: dict[str, Any]) -> bool:
    row = item["row"]
    decision = item["decision"]
    extracted = decision.record["extracted_repr"]
    if row["domain"] == "arithmetic":
        return decision.extraction_ok and int(extracted or "0") == int(row["true_answer"])
    if row["domain"] == "python_code":
        if not decision.extraction_ok:
            return False
        try:
            ast.parse(str(extracted))
            return True
        except SyntaxError:
            return False
    return decision.verdict == Verdict.NOT_RULED_OUT


def pass_but_wrong_count(items: list[dict[str, Any]]) -> int:
    total = 0
    for item in items:
        if item["row"]["domain"] != "arithmetic":
            continue
        if item["decision"].verdict == Verdict.NOT_RULED_OUT and not actually_valid(item):
            total += 1
    return total


def check_hardening() -> dict[str, Any]:
    rows = read_csv(SLICE02 / "hardening_results.csv")
    correct = [row for row in rows if row["is_correct"] == "1"]
    standard_wrong = [row for row in rows if row["is_correct"] == "0" and row["corruption_type"] != "off_by_combined_modulus"]
    standard_caught = [row for row in standard_wrong if row["verdict"] == Verdict.RULED_OUT_WRONG]
    false_positive = [row for row in correct if row["verdict"] == Verdict.RULED_OUT_WRONG]
    blind = [row for row in rows if row["corruption_type"] == "off_by_combined_modulus"]
    blind_safe = all(row["verdict"] == Verdict.NOT_RULED_OUT for row in blind)
    return {
        "standard_catch_rate": rate(len(standard_caught), len(standard_wrong)),
        "false_positive_rate": rate(len(false_positive), len(correct)),
        "combined_modulus_not_ruled_out": blind_safe,
        "combined_modulus_count": len(blind),
    }


def check_exact_multiple_soundness() -> str:
    expr_spec = {"family": "bigsum", "values": [2, 3]}
    combined_m = 1
    for modulus in DEFAULT_MODULI:
        combined_m *= modulus
    decision = check_output(str(5 + combined_m), "arithmetic", expr_spec, object_id="combined_m_smoke")
    return decision.verdict


def smoke_imports() -> list[str]:
    failures: list[str] = []
    for pattern in ("dr_*.py", "evaluate_*.py"):
        for path in sorted((ROOT / "src").glob(pattern)):
            try:
                importlib.import_module(path.stem)
            except Exception as exc:
                failures.append(f"{path.stem}: {type(exc).__name__}: {exc}")
    return failures


def emit_example_audit(items: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    AuditLog(path).append(items[0]["decision"].record)
    first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    validate_record(first)
    return path


def regression_table(summary: list[dict[str, Any]], expected: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    expected_by_domain = {row["domain"]: row for row in expected}
    for actual in summary:
        expected_row = expected_by_domain[actual["domain"]]
        fields = (
            "completed_generation_rate",
            "extraction_success_rate_completed",
            "content_rule_out_rate_extracted",
            "uncheckable_rate_cached",
            "practical_false_positive_rate",
            "valid_extracted_n",
            "ruled_out_n",
            "uncheckable_n",
        )
        passed = all(actual[field] == expected_row[field] for field in fields)
        rows.append(
            {
                "domain": actual["domain"],
                "expected_rule_out": str(expected_row["content_rule_out_rate_extracted"]),
                "actual_rule_out": str(actual["content_rule_out_rate_extracted"]),
                "expected_uncheckable": str(expected_row["uncheckable_rate_cached"]),
                "actual_uncheckable": str(actual["uncheckable_rate_cached"]),
                "expected_fp": str(expected_row["practical_false_positive_rate"]),
                "actual_fp": str(actual["practical_false_positive_rate"]),
                "status": "PASS" if passed else "FAIL",
            }
        )
    return rows


def run(example_audit_path: Path | None = None) -> dict[str, Any]:
    decisions, summary, expected = rescore_slice05()
    hardening = check_hardening()
    imports = smoke_imports()
    exact_multiple_verdict = check_exact_multiple_soundness()
    pass_but_wrong = pass_but_wrong_count(decisions)
    table = regression_table(summary, expected)
    example_path = emit_example_audit(decisions, example_audit_path or (OUT_DIR / "example_audit.jsonl"))
    ok = (
        all(row["status"] == "PASS" for row in table)
        and hardening["standard_catch_rate"] == "1.000"
        and hardening["false_positive_rate"] == "0.000"
        and hardening["combined_modulus_not_ruled_out"]
        and exact_multiple_verdict == Verdict.NOT_RULED_OUT
        and pass_but_wrong == 0
        and not imports
    )
    return {
        "ok": ok,
        "table": table,
        "summary": summary,
        "expected": expected,
        "hardening": hardening,
        "exact_multiple_verdict": exact_multiple_verdict,
        "pass_but_wrong": pass_but_wrong,
        "import_failures": imports,
        "example_audit_path": str(example_path),
    }


def print_table(result: dict[str, Any]) -> None:
    print("domain,expected_rule_out,actual_rule_out,expected_uncheckable,actual_uncheckable,expected_fp,actual_fp,status")
    for row in result["table"]:
        print(
            f"{row['domain']},{row['expected_rule_out']},{row['actual_rule_out']},"
            f"{row['expected_uncheckable']},{row['actual_uncheckable']},"
            f"{row['expected_fp']},{row['actual_fp']},{row['status']}"
        )
    hardening = result["hardening"]
    print(
        "hardening,"
        f"standard_catch={hardening['standard_catch_rate']},"
        f"fp={hardening['false_positive_rate']},"
        f"combined_modulus_safe={hardening['combined_modulus_not_ruled_out']}"
    )
    print(f"pass_but_wrong={result['pass_but_wrong']}")
    print(f"import_failures={len(result['import_failures'])}")
    print(f"example_audit_path={result['example_audit_path']}")
    print("status=" + ("PASS" if result["ok"] else "FAIL"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--example-audit-path", default=None)
    args = parser.parse_args()
    result = run(Path(args.example_audit_path) if args.example_audit_path else None)
    print_table(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["run", "rescore_slice05", "check_hardening", "smoke_imports", "regression_table"]
