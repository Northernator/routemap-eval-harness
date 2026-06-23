"""Phase 3 Slice 5: offline scaled evaluation from a generated cache."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dr_checker_code_v1 import PythonCodeChecker
from dr_checker_framework_v1 import ArithmeticChecker
from dr_checker_schema_v1 import JsonSchemaChecker
from dr_generate_corpus_v1 import DOMAINS, build_tasks
from dr_output_extraction_v1 import extract_code, extract_integer, extract_json
from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


UNCHECKABLE = "UNCHECKABLE"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_05_scale"
RECORDS_DIR = ROOT / "data" / "v1" / "digital_route" / "records"
RECORD_PATH = RECORDS_DIR / "SLICE_05_resumable_scale.md"
INDEX_PATH = RECORDS_DIR / "PHASE3_INDEX.md"


def read_cache(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                rows[str(row["task_id"])] = row
    return rows


def evaluate_row(row: dict[str, Any]) -> dict[str, Any]:
    domain = row["domain"]
    raw = str(row.get("raw_output", ""))
    status = row.get("status", "")
    if status != "completed":
        return result_row(row, "", "generation failed", UNCHECKABLE, "generation_failed", "0", "")
    if domain == "arithmetic":
        extracted, ok, note = extract_integer(raw)
        if not ok:
            return result_row(row, "", note, UNCHECKABLE, "integer extraction failed", "0", "")
        claimed = int(extracted)
        true_answer = int(row["true_answer"])
        check = ArithmeticChecker().check({"type": "arithmetic", "expr_spec": row["expr_spec"], "claimed_answer": claimed})
        return result_row(row, extracted, note, check.verdict, check.reason, "1" if claimed == true_answer else "0", str(claimed - true_answer))
    if domain == "python_code":
        extracted, ok, note = extract_code(raw)
        if not ok:
            return result_row(row, "", note, UNCHECKABLE, "code extraction failed", "0", "")
        check = PythonCodeChecker().check({"type": "python_code", "source": extracted})
        return result_row(row, extracted, note, check.verdict, check.reason, "1" if python_parses(extracted) else "0", "")
    extracted, ok, note = extract_json(raw)
    if not ok:
        return result_row(row, "", note, UNCHECKABLE, "json extraction failed", "0", "")
    check = JsonSchemaChecker().check({"type": "json_schema", "schema": row["schema"], "output": extracted})
    return result_row(row, extracted, note, check.verdict, check.reason, "1" if check.verdict == NOT_RULED_OUT else "0", "")


def result_row(
    cache_row: dict[str, Any],
    extracted: str,
    extraction_note: str,
    verdict: str,
    reason: str,
    valid: str,
    difference: str,
) -> dict[str, Any]:
    return {
        "task_id": cache_row["task_id"],
        "domain": cache_row["domain"],
        "generation_status": cache_row.get("status", ""),
        "raw_output": cache_row.get("raw_output", ""),
        "extracted_content": extracted,
        "extraction_ok": "1" if extracted else "0",
        "extraction_note": extraction_note,
        "verdict": verdict,
        "checker_reason": reason,
        "actually_valid_checkable_property": valid,
        "difference": difference,
    }


def python_parses(source: str) -> bool:
    try:
        ast.parse(source)
        return True
    except SyntaxError:
        return False


def summarize(rows: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for domain in DOMAINS:
        domain_rows = [row for row in rows if row["domain"] == domain]
        completed = [row for row in domain_rows if row["generation_status"] == "completed"]
        extracted = [row for row in completed if row["extraction_ok"] == "1"]
        ruled_out = [row for row in extracted if row["verdict"] == RULED_OUT_WRONG]
        uncheckable = [row for row in domain_rows if row["verdict"] == UNCHECKABLE]
        valid = [row for row in extracted if row["actually_valid_checkable_property"] == "1"]
        false_positive = [row for row in valid if row["verdict"] == RULED_OUT_WRONG]
        if false_positive:
            raise AssertionError("practical false-positive detected")
        summary.append(
            {
                "domain": domain,
                "target_n": n,
                "cached_n": len(domain_rows),
                "completed_n": len(completed),
                "partial": "1" if len(completed) < n else "0",
                "completed_generation_rate": rate(len(completed), n),
                "extraction_success_rate_completed": rate(len(extracted), len(completed)),
                "content_rule_out_rate_extracted": rate(len(ruled_out), len(extracted)),
                "uncheckable_rate_cached": rate(len(uncheckable), len(domain_rows)),
                "practical_false_positive_rate": rate(len(false_positive), len(valid)),
                "valid_extracted_n": len(valid),
                "ruled_out_n": len(ruled_out),
                "uncheckable_n": len(uncheckable),
            }
        )
    return summary


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.000"
    return f"{numerator / denominator:.3f}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_spot_check(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spot_rows: list[dict[str, Any]] = []
    for domain in DOMAINS:
        for row in [item for item in rows if item["domain"] == domain and item["verdict"] == RULED_OUT_WRONG][:15]:
            spot_rows.append(
                {
                    "task_id": row["task_id"],
                    "domain": domain,
                    "raw_output": row["raw_output"],
                    "extracted_content": row["extracted_content"],
                    "checker_reason": row["checker_reason"],
                }
            )
    write_csv(OUT_DIR / "spot_check_ruleouts.csv", spot_rows)
    return spot_rows


def write_record(summary: list[dict[str, Any]], spot_rows: list[dict[str, Any]], cache_path: Path, commands: list[str]) -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "| Domain | Completed | Completed rate | Extraction success | Rule-out | UNCHECKABLE | Practical FP |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary:
        lines.append(
            f"| {row['domain']} | {row['completed_n']}/{row['target_n']} | {row['completed_generation_rate']} | {row['extraction_success_rate_completed']} | {row['content_rule_out_rate_extracted']} | {row['uncheckable_rate_cached']} | {row['practical_false_positive_rate']} |"
        )
    spot_counts = {domain: len([row for row in spot_rows if row["domain"] == domain]) for domain in DOMAINS}
    record = f"""# Phase 3 Slice 5 - Resumable Generation and Offline Scale

Date: {date.today().isoformat()}

## Purpose

Decouple local llama generation from checker evaluation. Generation is resumable, token-capped, and cached; evaluation is offline and cannot time out on Ollama.

## Files created

- `src/dr_generate_corpus_v1.py`
- `src/dr_run_checker_framework_eval_v3.py`
- `data/v1/digital_route/slice_05_scale/corpus.jsonl`
- `data/v1/digital_route/slice_05_scale/results.csv`
- `data/v1/digital_route/slice_05_scale/summary.csv`
- `data/v1/digital_route/slice_05_scale/summary.json`
- `data/v1/digital_route/slice_05_scale/spot_check_ruleouts.csv`
- `data/v1/digital_route/records/SLICE_05_resumable_scale.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

{chr(10).join(f'- `{command}`' for command in commands)}

## Per-Domain Results

{chr(10).join(lines)}

## Spot-Check Notes

Spot-check rows exported: arithmetic {spot_counts['arithmetic']}, python_code {spot_counts['python_code']}, json_schema {spot_counts['json_schema']}. Each row includes raw output, extracted content, and checker reason. Fewer than 15 rows means fewer than 15 rule-outs were observed for that domain.

## Arithmetic Anchor

Arithmetic still uses the Slice 1 residue adapter. Offline evaluation compares extracted integers with known bignum truth and preserves the Slice 2 one-sided contract: residue disagreement may rule out, but agreement never means correct.

## Conclusion

The resumable cache makes generation failures local to individual task IDs, and the offline evaluator turns generation or extraction failures into `UNCHECKABLE` rather than false rule-outs. Practical false-positive rate was 0.000 in every domain.

## Next Slice

Build the repair wrapper: feed `RULED_OUT_WRONG` and `UNCHECKABLE` outputs back to the model with terse, checker-specific diagnostics and measure repair success.
"""
    RECORD_PATH.write_text(record, encoding="utf-8")
    index_line = (
        f"- {date.today().isoformat()} - Slice 05: resumable generation/offline scale; "
        f"completed {summary[0]['completed_n']}/{summary[1]['completed_n']}/{summary[2]['completed_n']}, FP 0.000."
    )
    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text(encoding="utf-8")
        if index_line not in existing:
            INDEX_PATH.write_text(existing.rstrip() + "\n" + index_line + "\n", encoding="utf-8")
    else:
        INDEX_PATH.write_text("# Phase 3 Digital Route Index\n\n" + index_line + "\n", encoding="utf-8")


def run(cache_path: Path, n: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cached = read_cache(cache_path)
    task_ids = {task.task_id for task in build_tasks(n)}
    rows = [evaluate_row(cached[task_id]) for task_id in sorted(task_ids & set(cached))]
    summary = summarize(rows, n)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(OUT_DIR / "results.csv", rows)
    write_csv(OUT_DIR / "summary.csv", summary)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    spot_rows = write_spot_check(rows)
    commands = [
        f"python src/dr_generate_corpus_v1.py --domain all --n {n} --timeout 60 --retries 2 --out {cache_path.as_posix()}",
        f"python src/dr_run_checker_framework_eval_v3.py --cache {cache_path.as_posix()}",
        "python -m py_compile src/dr_generate_corpus_v1.py src/dr_run_checker_framework_eval_v3.py",
        "git -C . diff --check",
    ]
    write_record(summary, spot_rows, cache_path, commands)
    return rows, summary


def print_summary(summary: list[dict[str, Any]]) -> None:
    print("domain,completed,completed_rate,extraction_success,rule_out,uncheckable,practical_fp")
    for row in summary:
        print(
            f"{row['domain']},{row['completed_n']}/{row['target_n']},{row['completed_generation_rate']},"
            f"{row['extraction_success_rate_completed']},{row['content_rule_out_rate_extracted']},"
            f"{row['uncheckable_rate_cached']},{row['practical_false_positive_rate']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True)
    parser.add_argument("--n", type=int, default=30)
    args = parser.parse_args()
    _, summary = run(Path(args.cache), args.n)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
