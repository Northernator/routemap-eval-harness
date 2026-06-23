"""Phase 3 Slice 6 repair evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dr_generate_corpus_v1 import DOMAINS, build_tasks
from dr_repair_wrapper_v1 import append_jsonl, read_jsonl, repair_once
from dr_run_checker_framework_eval_v3 import evaluate_row, rate, read_cache, write_csv
from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


UNCHECKABLE = "UNCHECKABLE"
ROOT = Path(__file__).resolve().parents[1]
SLICE5_CACHE = ROOT / "data" / "v1" / "digital_route" / "slice_05_scale" / "corpus.jsonl"
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_06_repair"
REPAIR_CACHE = OUT_DIR / "repair_cache.jsonl"
RECORDS_DIR = ROOT / "data" / "v1" / "digital_route" / "records"
RECORD_PATH = RECORDS_DIR / "SLICE_06_repair_wrapper.md"
INDEX_PATH = RECORDS_DIR / "PHASE3_INDEX.md"


def flagged_rows(cache_rows: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    evaluated: list[dict[str, Any]] = []
    for task in build_tasks(30):
        row = cache_rows.get(task.task_id)
        if row is None:
            continue
        result = evaluate_row(row)
        if result["verdict"] in (RULED_OUT_WRONG, UNCHECKABLE):
            result["prompt"] = row.get("prompt", "")
            result["expr_spec"] = row.get("expr_spec")
            result["true_answer"] = row.get("true_answer")
            result["schema"] = row.get("schema")
            evaluated.append(result)
    return evaluated


def existing_repairs() -> dict[tuple[str, int], dict[str, Any]]:
    return {(row["task_id"], int(row["round"])): row for row in read_jsonl(REPAIR_CACHE)}


def repair_to_cache(flagged: list[dict[str, Any]], rounds: int, timeout: int, retries: int) -> None:
    repairs = existing_repairs()
    for item in flagged:
        for round_index in range(1, rounds + 1):
            key = (item["task_id"], round_index)
            if key in repairs:
                repair_row = repairs[key]
            else:
                repair_row = repair_once(item, round_index, timeout_seconds=timeout, retries=retries)
                append_jsonl(REPAIR_CACHE, repair_row)
                repairs[key] = repair_row
                print(f"repair {item['domain']} {item['task_id']} round {round_index}: {repair_row['status']}")
            candidate = cache_row_from_repair(item, repair_row)
            evaluated = evaluate_row(candidate)
            if evaluated["verdict"] == NOT_RULED_OUT:
                break


def cache_row_from_repair(original: dict[str, Any], repair: dict[str, Any] | None) -> dict[str, Any]:
    row = {
        "task_id": original["task_id"],
        "domain": original["domain"],
        "prompt": original.get("prompt", ""),
        "expr_spec": original.get("expr_spec"),
        "true_answer": original.get("true_answer"),
        "schema": original.get("schema"),
        "model": "llama3.1",
    }
    if repair is None:
        row.update({"status": "generation_failed", "raw_output": "", "generation_error": "no repair row"})
    else:
        row.update(
            {
                "status": repair.get("status", "generation_failed"),
                "raw_output": repair.get("raw_output", ""),
                "generation_error": repair.get("generation_error", ""),
            }
        )
    return row


def final_repair_result(original: dict[str, Any], repairs: dict[tuple[str, int], dict[str, Any]], rounds: int) -> dict[str, Any]:
    last_eval: dict[str, Any] | None = None
    last_repair: dict[str, Any] | None = None
    for round_index in range(1, rounds + 1):
        repair = repairs.get((original["task_id"], round_index))
        if repair is None:
            continue
        last_repair = repair
        candidate = cache_row_from_repair(original, repair)
        last_eval = evaluate_row(candidate)
        if last_eval["verdict"] == NOT_RULED_OUT:
            break
    if last_eval is None:
        last_eval = evaluate_row(cache_row_from_repair(original, None))
    return {
        **last_eval,
        "original_verdict": original["verdict"],
        "original_reason": original["checker_reason"],
        "original_raw_output": original["raw_output"],
        "original_extracted_content": original["extracted_content"],
        "repair_round_used": "" if last_repair is None else last_repair["round"],
        "repair_status": "missing" if last_repair is None else last_repair["status"],
        "repair_raw_output": "" if last_repair is None else last_repair.get("raw_output", ""),
        "checker_pass_after_repair": "1" if last_eval["verdict"] == NOT_RULED_OUT else "0",
        "actual_correct_after_repair": last_eval["actually_valid_checkable_property"],
        "passes_but_wrong": "1" if last_eval["verdict"] == NOT_RULED_OUT and last_eval["actually_valid_checkable_property"] != "1" else "0",
    }


def summarize(flagged: list[dict[str, Any]], final_rows: list[dict[str, Any]], original_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for domain in DOMAINS:
        domain_flagged = [row for row in flagged if row["domain"] == domain]
        domain_final = [row for row in final_rows if row["domain"] == domain]
        domain_original = [row for row in original_rows if row["domain"] == domain]
        before_bad = [row for row in domain_original if row["verdict"] in (RULED_OUT_WRONG, UNCHECKABLE)]
        after_bad = [row for row in domain_final if row["verdict"] in (RULED_OUT_WRONG, UNCHECKABLE)]
        passed = [row for row in domain_final if row["checker_pass_after_repair"] == "1"]
        correct = [row for row in domain_final if row["actual_correct_after_repair"] == "1"]
        blind = [row for row in domain_final if row["passes_but_wrong"] == "1"]
        residual = [row for row in domain_final if row["verdict"] in (RULED_OUT_WRONG, UNCHECKABLE)]
        summary.append(
            {
                "domain": domain,
                "flagged_n": len(domain_flagged),
                "repair_attempted_n": len(domain_final),
                "checker_pass_rate_after_repair": rate(len(passed), len(domain_final)),
                "actual_correct_rate_after_repair": rate(len(correct), len(domain_final)),
                "passes_but_wrong_n": len(blind),
                "residual_after_k_n": len(residual),
                "before_error_rate": rate(len(before_bad), len(domain_original)),
                "after_error_rate_on_flagged": rate(len(after_bad), len(domain_final)),
            }
        )
    return summary


def write_spot_check(final_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in final_rows:
        rows.append(
            {
                "task_id": row["task_id"],
                "domain": row["domain"],
                "original_verdict": row["original_verdict"],
                "original_reason": row["original_reason"],
                "original_raw_output": row["original_raw_output"],
                "original_extracted_content": row["original_extracted_content"],
                "repair_round_used": row["repair_round_used"],
                "repair_raw_output": row["repair_raw_output"],
                "final_verdict": row["verdict"],
                "final_reason": row["checker_reason"],
                "final_extracted_content": row["extracted_content"],
                "actual_correct_after_repair": row["actual_correct_after_repair"],
                "passes_but_wrong": row["passes_but_wrong"],
            }
        )
    write_csv(OUT_DIR / "repair_spot_check.csv", rows)
    return rows


def write_record(summary: list[dict[str, Any]], spot_rows: list[dict[str, Any]], rounds: int) -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "| Domain | Flagged | Checker pass | Actual correct | Pass-but-wrong | Residual | Before error | After flagged error |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary:
        lines.append(
            f"| {row['domain']} | {row['flagged_n']} | {row['checker_pass_rate_after_repair']} | {row['actual_correct_rate_after_repair']} | {row['passes_but_wrong_n']} | {row['residual_after_k_n']} | {row['before_error_rate']} | {row['after_error_rate_on_flagged']} |"
        )
    record = f"""# Phase 3 Slice 6 - Repair Wrapper

Date: {date.today().isoformat()}

## Purpose

Turn sound detection into an improvement loop: detect, diagnose, repair, re-extract, and re-verify while preserving the one-sided checker caveat.

## Files created

- `src/dr_repair_wrapper_v1.py`
- `src/dr_run_repair_eval_v1.py`
- `data/v1/digital_route/slice_06_repair/repair_cache.jsonl`
- `data/v1/digital_route/slice_06_repair/repair_results.csv`
- `data/v1/digital_route/slice_06_repair/repair_summary.csv`
- `data/v1/digital_route/slice_06_repair/repair_summary.json`
- `data/v1/digital_route/slice_06_repair/repair_spot_check.csv`
- `data/v1/digital_route/records/SLICE_06_repair_wrapper.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_repair_eval_v1.py --rounds {rounds}`
- `python -m py_compile src/dr_repair_wrapper_v1.py src/dr_run_repair_eval_v1.py`
- `git -C . diff --check`

## Per-Domain Results

{chr(10).join(lines)}

## Soundness Guard

`NOT_RULED_OUT` after repair is reported only as checker pass, not correctness. Actual correctness is tracked separately where available: arithmetic exact value, JSON schema validity, and Python parseability only. The `passes_but_wrong` column measures repaired outputs that pass the checker but still fail the available truth/property check.

## Spot-Check Notes

Exported {len(spot_rows)} repaired cases with original output, diagnostic, repaired output, final verdict, and actual-correct flag.

## Conclusion

Repair effectiveness is domain-specific. JSON schema violations are expected to be repairable from targeted diagnostics; hard arithmetic may remain weak because the model must recompute, not just satisfy a local structural constraint.

## Next Slice

Add a two-stage repair policy that routes arithmetic repairs to structured scratchpad generation plus residue self-check, while keeping JSON/code repairs terse and schema-directed.
"""
    RECORD_PATH.write_text(record, encoding="utf-8")
    index_line = (
        f"- {date.today().isoformat()} - Slice 06: repair wrapper; "
        f"pass rates {summary[0]['checker_pass_rate_after_repair']}/"
        f"{summary[1]['checker_pass_rate_after_repair']}/"
        f"{summary[2]['checker_pass_rate_after_repair']}, blind leaks "
        f"{summary[0]['passes_but_wrong_n'] + summary[1]['passes_but_wrong_n'] + summary[2]['passes_but_wrong_n']}."
    )
    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text(encoding="utf-8")
        if index_line not in existing:
            INDEX_PATH.write_text(existing.rstrip() + "\n" + index_line + "\n", encoding="utf-8")
    else:
        INDEX_PATH.write_text("# Phase 3 Digital Route Index\n\n" + index_line + "\n", encoding="utf-8")


def run(rounds: int, timeout: int, retries: int) -> list[dict[str, Any]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cache_rows = read_cache(SLICE5_CACHE)
    original_all = [evaluate_row(row) for row in cache_rows.values()]
    flagged = flagged_rows(cache_rows)
    repair_to_cache(flagged, rounds, timeout, retries)
    repairs = existing_repairs()
    final_rows = [final_repair_result(row, repairs, rounds) for row in flagged]
    summary = summarize(flagged, final_rows, original_all)
    write_csv(OUT_DIR / "repair_results.csv", final_rows)
    write_csv(OUT_DIR / "repair_summary.csv", summary)
    (OUT_DIR / "repair_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    spot_rows = write_spot_check(final_rows)
    write_record(summary, spot_rows, rounds)
    return summary


def print_summary(summary: list[dict[str, Any]]) -> None:
    print("domain,flagged,checker_pass_after_repair,actual_correct_after_repair,passes_but_wrong,residual,before_error,after_flagged_error")
    for row in summary:
        print(
            f"{row['domain']},{row['flagged_n']},{row['checker_pass_rate_after_repair']},"
            f"{row['actual_correct_rate_after_repair']},{row['passes_but_wrong_n']},"
            f"{row['residual_after_k_n']},{row['before_error_rate']},{row['after_error_rate_on_flagged']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()
    summary = run(args.rounds, args.timeout, args.retries)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
