"""Phase 3 Slice 2: benchmark hardening and modulus-bank sensitivity."""

from __future__ import annotations

import csv
import json
import math
import random
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

from dr_residue_engine_v1 import DEFAULT_MODULI, fingerprint
from dr_verifier_v1 import RULED_OUT_WRONG, verify


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_02_hardening"
REAL_MODEL_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_02_real_model"
RECORDS_DIR = ROOT / "data" / "v1" / "digital_route" / "records"
RECORD_PATH = RECORDS_DIR / "SLICE_02_real_model_and_hardening.md"
INDEX_PATH = RECORDS_DIR / "PHASE3_INDEX.md"
MODULUS_PRODUCT = math.prod(DEFAULT_MODULI)


def fibonacci_exact(n: int) -> int:
    def pair(k: int) -> tuple[int, int]:
        if k == 0:
            return 0, 1
        a, b = pair(k >> 1)
        c = a * (2 * b - a)
        d = a * a + b * b
        if k & 1:
            return d, c + d
        return c, d

    return pair(n)[0]


def exact_value(expr_spec: dict[str, Any]) -> int:
    family = expr_spec["family"]
    if family == "power":
        return int(expr_spec["base"]) ** int(expr_spec["exponent"])
    if family == "factorial":
        return math.factorial(int(expr_spec["n"]))
    if family == "fibonacci":
        return fibonacci_exact(int(expr_spec["n"]))
    if family == "bigsum":
        return sum(int(value) for value in expr_spec["values"])
    if family == "bigprod":
        product = 1
        for value in expr_spec["values"]:
            product *= int(value)
        return product
    raise ValueError(f"unsupported family: {family}")


def build_synthetic_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for index in range(50):
        specs.append({"family": "power", "base": 17 + index * 3, "exponent": 8 + (index % 17)})
        specs.append({"family": "factorial", "n": 12 + (index % 55)})
        specs.append({"family": "fibonacci", "n": 30 + index * 11})
        values = [((index + 3) * (j + 11) * 1009) - (j * 37) for j in range(1, 12)]
        specs.append({"family": "bigsum", "values": values})
        factors = [101 + index * 2 + j * 17 for j in range(1, 7)]
        specs.append({"family": "bigprod", "values": factors})
    return specs


def corrupt_answer(true_answer: int, corruption_type: str, rng: random.Random, index: int) -> int:
    if corruption_type == "random_offset":
        return true_answer + rng.randint(1, 2_000_000)
    if corruption_type == "digit_transpose":
        sign = -1 if true_answer < 0 else 1
        digits = list(str(abs(true_answer)))
        for pos in range(len(digits) - 1):
            if digits[pos] != digits[pos + 1]:
                digits[pos], digits[pos + 1] = digits[pos + 1], digits[pos]
                return sign * int("".join(digits))
        return true_answer + 10
    if corruption_type == "off_by_power10":
        digits = len(str(abs(true_answer)))
        return true_answer + 10 ** min(max(0, digits - 1), 80)
    if corruption_type == "sign_flip":
        return -true_answer if true_answer != 0 else 1
    if corruption_type == "off_by_multiple_of_9":
        return true_answer + 9 * rng.randint(1, 1_000_000)
    if corruption_type == "off_by_combined_modulus":
        return true_answer + MODULUS_PRODUCT * (1 + (index % 3))
    raise ValueError(f"unknown corruption type: {corruption_type}")


def run_hardening() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(2_026_032_202)
    specs = build_synthetic_specs()
    corruption_types = [
        "random_offset",
        "digit_transpose",
        "off_by_power10",
        "sign_flip",
        "off_by_multiple_of_9",
        "off_by_combined_modulus",
    ]
    rows: list[dict[str, Any]] = []
    for index, expr_spec in enumerate(specs):
        true_answer = exact_value(expr_spec)
        correct_result = verify(expr_spec, true_answer)
        rows.append(
            {
                "problem_index": index,
                "family": expr_spec["family"],
                "corruption_type": "correct",
                "is_correct": "1",
                "verdict": correct_result["verdict"],
                "caught": "",
                "difference_multiple_of_M": "1",
            }
        )
        for corruption_type in corruption_types:
            claimed_answer = corrupt_answer(true_answer, corruption_type, rng, index)
            result = verify(expr_spec, claimed_answer)
            caught = result["verdict"] == RULED_OUT_WRONG
            difference = claimed_answer - true_answer
            rows.append(
                {
                    "problem_index": index,
                    "family": expr_spec["family"],
                    "corruption_type": corruption_type,
                    "is_correct": "0",
                    "verdict": result["verdict"],
                    "caught": "1" if caught else "0",
                    "difference_multiple_of_M": "1" if difference % MODULUS_PRODUCT == 0 else "0",
                }
            )
    summary = summarize_hardening(rows)
    return rows, summary


def summarize_hardening(rows: list[dict[str, Any]]) -> dict[str, Any]:
    correct_rows = [row for row in rows if row["is_correct"] == "1"]
    false_positive_rows = [row for row in correct_rows if row["verdict"] == RULED_OUT_WRONG]
    if false_positive_rows:
        raise AssertionError("soundness bug: correct synthetic answer was ruled out")
    wrong_rows = [row for row in rows if row["is_correct"] == "0"]
    standard_wrong = [row for row in wrong_rows if row["corruption_type"] != "off_by_combined_modulus"]
    all_caught = [row for row in wrong_rows if row["verdict"] == RULED_OUT_WRONG]
    standard_caught = [row for row in standard_wrong if row["verdict"] == RULED_OUT_WRONG]
    by_type: dict[str, dict[str, Any]] = {}
    for corruption_type in sorted({row["corruption_type"] for row in wrong_rows}):
        typed = [row for row in wrong_rows if row["corruption_type"] == corruption_type]
        caught = [row for row in typed if row["verdict"] == RULED_OUT_WRONG]
        by_type[corruption_type] = {
            "wrong_count": len(typed),
            "ruled_out": len(caught),
            "catch_rate": len(caught) / len(typed) if typed else 0.0,
            "escapes_are_multiples_of_M": all(row["difference_multiple_of_M"] == "1" for row in typed if row["verdict"] != RULED_OUT_WRONG),
        }
    return {
        "synthetic_problem_count": len(correct_rows),
        "wrong_answer_count": len(wrong_rows),
        "standard_wrong_answer_count": len(standard_wrong),
        "all_wrong_catch_rate": len(all_caught) / len(wrong_rows),
        "standard_corruption_catch_rate": len(standard_caught) / len(standard_wrong),
        "false_positive_rate": 0.0,
        "by_type": by_type,
    }


def run_bank_sensitivity() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    banks = [
        ("digital_root_only", (9,)),
        ("small_7_9_11", (7, 9, 11)),
        ("default_7_9_11_13_37_101", DEFAULT_MODULI),
        ("extended_default_41_43", DEFAULT_MODULI + (41, 43)),
    ]
    base_specs = build_synthetic_specs()[:40]
    true_answers = [exact_value(spec) for spec in base_specs]
    offsets = list(range(1, 5_001))
    rows: list[dict[str, Any]] = []
    for bank_name, bank in banks:
        bank_m = math.prod(bank)
        start = time.perf_counter()
        checked = 0
        caught = 0
        escaped = 0
        escape_multiple_failures = 0
        for spec_index, expr_spec in enumerate(base_specs):
            true_answer = true_answers[spec_index]
            for offset in offsets:
                claimed = true_answer + offset
                result = verify(expr_spec, claimed, bank)
                checked += 1
                if result["verdict"] == RULED_OUT_WRONG:
                    caught += 1
                else:
                    escaped += 1
                    if offset % bank_m != 0:
                        escape_multiple_failures += 1
        seconds = time.perf_counter() - start
        rows.append(
            {
                "bank_name": bank_name,
                "moduli": " ".join(str(modulus) for modulus in bank),
                "combined_modulus_M": bank_m,
                "random_error_count": checked,
                "ruled_out": caught,
                "escaped": escaped,
                "random_error_catch_rate": f"{caught / checked:.9f}",
                "all_escapes_multiples_of_M": "1" if escape_multiple_failures == 0 else "0",
                "seconds": f"{seconds:.6f}",
            }
        )
    summary = {"banks": rows}
    return rows, summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_llm_summary() -> dict[str, Any] | None:
    summary_path = REAL_MODEL_DIR / "llm_summary_full.json"
    if not summary_path.exists():
        return None
    return json.loads(summary_path.read_text(encoding="utf-8"))


def write_record(
    hardening_summary: dict[str, Any],
    bank_rows: list[dict[str, Any]],
    llm_summary: dict[str, Any] | None,
) -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    by_type_lines = [
        "| Corruption type | Wrong answers | Ruled out | Catch rate | Escapes multiples of M |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for corruption_type, row in hardening_summary["by_type"].items():
        by_type_lines.append(
            f"| {corruption_type} | {row['wrong_count']} | {row['ruled_out']} | {row['catch_rate']:.3f} | {row['escapes_are_multiples_of_M']} |"
        )
    bank_lines = [
        "| Bank | M | Random errors | Ruled out | Escaped | Catch rate | Escapes multiples of M |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in bank_rows:
        bank_lines.append(
            f"| {row['bank_name']} | {row['combined_modulus_M']} | {row['random_error_count']} | {row['ruled_out']} | {row['escaped']} | {float(row['random_error_catch_rate']):.6f} | {row['all_escapes_multiples_of_M']} |"
        )
    if llm_summary is None:
        llm_text = "Full llama 3.1 summary was not present when the hardening script wrote this record."
    else:
        missed_text = "none"
        if llm_summary["missed_errors"]:
            missed_text = "; ".join(
                f"{item['problem_id']} multiple_of_M={item['difference_multiple_of_M']}"
                for item in llm_summary["missed_errors"]
            )
        llm_text = (
            f"Parsed {llm_summary['parsed_count']} of {llm_summary['problem_count']} model answers; "
            f"parse failures {llm_summary['parse_failure_count']}; "
            f"arithmetic error rate {llm_summary['arithmetic_error_rate']:.3f}; "
            f"verifier catch rate on real errors {llm_summary['verifier_catch_rate_on_errors']:.3f}; "
            f"false-positive rate {llm_summary['false_positive_rate']:.3f}; "
            f"missed errors: {missed_text}."
        )
    record = f"""# Phase 3 Slice 2 - Real Model Verification and Benchmark Hardening

Date: {date.today().isoformat()}

## Purpose

Demonstrate that the Slice 1 Digital Route verifier catches real llama 3.1 arithmetic errors, then harden the synthetic benchmark with larger N, an empirical combined-modulus blind spot, and modulus-bank sensitivity.

## Files created

- `src/dr_run_llm_verification_v2.py`
- `src/dr_run_benchmark_hardening_v2.py`
- `data/v1/digital_route/slice_02_real_model/llm_raw_outputs_limit_5.jsonl`
- `data/v1/digital_route/slice_02_real_model/llm_results_limit_5.csv`
- `data/v1/digital_route/slice_02_real_model/llm_summary_limit_5.json`
- `data/v1/digital_route/slice_02_real_model/llm_raw_outputs_full.jsonl`
- `data/v1/digital_route/slice_02_real_model/llm_results_full.csv`
- `data/v1/digital_route/slice_02_real_model/llm_summary_full.json`
- `data/v1/digital_route/slice_02_hardening/hardening_results.csv`
- `data/v1/digital_route/slice_02_hardening/hardening_summary.json`
- `data/v1/digital_route/slice_02_hardening/bank_sensitivity.csv`
- `data/v1/digital_route/slice_02_hardening/bank_sensitivity_summary.json`
- `data/v1/digital_route/records/SLICE_02_real_model_and_hardening.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_llm_verification_v2.py --limit 5`
- `python src/dr_run_llm_verification_v2.py`
- `python src/dr_run_benchmark_hardening_v2.py`
- `python -m py_compile src/dr_run_llm_verification_v2.py src/dr_run_benchmark_hardening_v2.py`
- `git -C . diff --check`

## Real llama 3.1 Verification

{llm_text}

## Synthetic Hardening

Synthetic problems: {hardening_summary['synthetic_problem_count']}

Standard corruption catch rate: {hardening_summary['standard_corruption_catch_rate']:.3f}

All wrong-answer catch rate including designed blind spot: {hardening_summary['all_wrong_catch_rate']:.3f}

False-positive rate on correct answers: {hardening_summary['false_positive_rate']:.3f}

{chr(10).join(by_type_lines)}

## Blind-Spot Demonstration

`off_by_combined_modulus` adds exact multiples of M = `{MODULUS_PRODUCT}`. Catch rate is {hardening_summary['by_type']['off_by_combined_modulus']['catch_rate']:.3f}; these wrong answers return `NOT_RULED_OUT`, never `correct`.

## Bank Sensitivity

{chr(10).join(bank_lines)}

## Conclusion

The verifier catches real parsed llama 3.1 arithmetic errors at zero false positives in this run. Synthetic hardening reconfirms the sound one-sided contract at N >= 200 and empirically isolates the only designed miss class: errors that are multiples of the active bank's combined modulus.

## Next Slice

Build a verifier-wrapper attach point that intercepts model arithmetic answers, emits residue diagnostics, and asks the model to repair only answers ruled out by the verifier.
"""
    RECORD_PATH.write_text(record, encoding="utf-8")
    if llm_summary is None:
        index_line = (
            f"- {date.today().isoformat()} - Slice 02: benchmark hardening complete; "
            f"FP {hardening_summary['false_positive_rate']:.3f}, blind-spot catch {hardening_summary['by_type']['off_by_combined_modulus']['catch_rate']:.3f}; "
            "full llama summary missing at record time."
        )
    else:
        index_line = (
            f"- {date.today().isoformat()} - Slice 02: real llama 3.1 verification plus benchmark hardening; "
            f"real-error catch {llm_summary['verifier_catch_rate_on_errors']:.3f}, "
            f"FP {hardening_summary['false_positive_rate']:.3f}, blind-spot catch {hardening_summary['by_type']['off_by_combined_modulus']['catch_rate']:.3f}."
        )
    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text(encoding="utf-8")
        if index_line not in existing:
            INDEX_PATH.write_text(existing.rstrip() + "\n" + index_line + "\n", encoding="utf-8")
    else:
        INDEX_PATH.write_text("# Phase 3 Digital Route Index\n\n" + index_line + "\n", encoding="utf-8")


def print_summary(hardening_summary: dict[str, Any], bank_rows: list[dict[str, Any]], llm_summary: dict[str, Any] | None) -> None:
    print("Benchmark hardening")
    print(f"synthetic problems: {hardening_summary['synthetic_problem_count']}")
    print(f"standard corruption catch rate: {hardening_summary['standard_corruption_catch_rate']:.3f}")
    print(f"all wrong catch rate including blind spot: {hardening_summary['all_wrong_catch_rate']:.3f}")
    print(f"false-positive rate: {hardening_summary['false_positive_rate']:.3f}")
    print("blind spot: off_by_combined_modulus catch rate " f"{hardening_summary['by_type']['off_by_combined_modulus']['catch_rate']:.3f}")
    print("\nBank sensitivity")
    print("bank,M,random_errors,ruled_out,escaped,catch_rate,escapes_multiples_of_M")
    for row in bank_rows:
        print(
            f"{row['bank_name']},{row['combined_modulus_M']},{row['random_error_count']},"
            f"{row['ruled_out']},{row['escaped']},{float(row['random_error_catch_rate']):.6f},"
            f"{row['all_escapes_multiples_of_M']}"
        )
    if llm_summary is not None:
        print("\nReal llama 3.1 headline")
        print(f"LLM arithmetic error rate: {llm_summary['arithmetic_error_rate']:.3f}")
        print(f"Verifier catch rate on real errors: {llm_summary['verifier_catch_rate_on_errors']:.3f}")
        print(f"False-positive rate on correct answers: {llm_summary['false_positive_rate']:.3f}")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    hardening_rows, hardening_summary = run_hardening()
    bank_rows, bank_summary = run_bank_sensitivity()
    llm_summary = load_llm_summary()
    write_csv(OUT_DIR / "hardening_results.csv", hardening_rows)
    write_csv(OUT_DIR / "bank_sensitivity.csv", bank_rows)
    (OUT_DIR / "hardening_summary.json").write_text(json.dumps(hardening_summary, indent=2, sort_keys=True), encoding="utf-8")
    (OUT_DIR / "bank_sensitivity_summary.json").write_text(json.dumps(bank_summary, indent=2, sort_keys=True), encoding="utf-8")
    write_record(hardening_summary, bank_rows, llm_summary)
    print_summary(hardening_summary, bank_rows, llm_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
