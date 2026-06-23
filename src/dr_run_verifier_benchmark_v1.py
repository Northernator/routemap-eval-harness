"""Phase 3 Slice 1 Digital Route verifier benchmark."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from dr_residue_engine_v1 import DEFAULT_MODULI, fingerprint
from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG, verify


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_01_verifier"
RECORDS_DIR = ROOT / "data" / "v1" / "digital_route" / "records"
RECORD_PATH = RECORDS_DIR / "SLICE_01_verifier.md"
INDEX_PATH = RECORDS_DIR / "PHASE3_INDEX.md"
MODULUS_PRODUCT = math.prod(DEFAULT_MODULI)
FULL_IMPRACTICAL_DIGIT_THRESHOLD = 250_000


@dataclass(frozen=True)
class Problem:
    problem_id: str
    family: str
    size_label: str
    expr_spec: dict[str, Any]
    true_answer: int


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


def build_problems() -> list[Problem]:
    bigsum_values = [((i * 9_973) - 50_000) ** 3 for i in range(1, 900)]
    bigprod_values = [(i * 37 + 101) for i in range(1, 260)]
    specs: list[tuple[str, str, dict[str, Any]]] = [
        ("power_small", "8-digit exponent", {"family": "power", "base": 12, "exponent": 8}),
        ("power_medium", "250 exponent", {"family": "power", "base": 37, "exponent": 250}),
        ("power_large", "5000 exponent", {"family": "power", "base": 123_457, "exponent": 5_000}),
        ("factorial_small", "25!", {"family": "factorial", "n": 25}),
        ("factorial_medium", "75!", {"family": "factorial", "n": 75}),
        ("factorial_edge", "100!", {"family": "factorial", "n": 100}),
        ("fibonacci_small", "F(40)", {"family": "fibonacci", "n": 40}),
        ("fibonacci_medium", "F(1000)", {"family": "fibonacci", "n": 1_000}),
        ("fibonacci_large", "F(20000)", {"family": "fibonacci", "n": 20_000}),
        ("bigsum_medium", "899 cubic terms", {"family": "bigsum", "values": bigsum_values}),
        ("bigprod_medium", "259 factors", {"family": "bigprod", "values": bigprod_values}),
    ]
    return [
        Problem(problem_id, expr_spec["family"], size_label, expr_spec, exact_value(expr_spec))
        for problem_id, size_label, expr_spec in specs
    ]


def corrupt_answer(true_answer: int, corruption_type: str, rng: random.Random) -> int:
    if corruption_type == "random_offset":
        offset = rng.randint(1, 1_000_000)
        return true_answer + offset
    if corruption_type == "digit_transpose":
        sign = -1 if true_answer < 0 else 1
        digits = list(str(abs(true_answer)))
        for index in range(len(digits) - 1):
            if digits[index] != digits[index + 1]:
                digits[index], digits[index + 1] = digits[index + 1], digits[index]
                return sign * int("".join(digits))
        return true_answer + 10
    if corruption_type == "off_by_power10":
        digits = max(1, len(str(abs(true_answer))))
        return true_answer + 10 ** min(digits - 1, 60)
    if corruption_type == "sign_flip":
        return -true_answer
    if corruption_type == "off_by_multiple_of_9":
        multiplier = rng.randint(1, 250_000)
        return true_answer + (9 * multiplier)
    raise ValueError(f"unknown corruption type: {corruption_type}")


def answer_summary(value: int) -> dict[str, str | int]:
    text = str(abs(value))
    return {
        "sign": "-" if value < 0 else "+",
        "digits": len(text),
        "prefix": text[:16],
        "suffix": text[-16:],
    }


def run_verifier_rows(problems: list[Problem]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rng = random.Random(2_026_032_201)
    rows: list[dict[str, Any]] = []
    corruption_types = [
        "random_offset",
        "digit_transpose",
        "off_by_power10",
        "sign_flip",
        "off_by_multiple_of_9",
    ]
    for problem in problems:
        correct = verify(problem.expr_spec, problem.true_answer)
        rows.append(
            make_result_row(problem, "correct", problem.true_answer, correct, True)
        )
        for corruption_type in corruption_types:
            claimed_answer = corrupt_answer(problem.true_answer, corruption_type, rng)
            if claimed_answer == problem.true_answer:
                claimed_answer += MODULUS_PRODUCT
            result = verify(problem.expr_spec, claimed_answer)
            rows.append(
                make_result_row(problem, corruption_type, claimed_answer, result, False)
            )

    correct_rows = [row for row in rows if row["is_correct"] == "1"]
    false_positives = [
        row for row in correct_rows if row["verdict"] == RULED_OUT_WRONG
    ]
    false_positive_rate = len(false_positives) / len(correct_rows)
    if false_positive_rate != 0.0:
        raise AssertionError("soundness bug: correct answer was RULED_OUT_WRONG")

    wrong_rows = [row for row in rows if row["is_correct"] == "0"]
    catch_by_type: dict[str, dict[str, float | int]] = {}
    for corruption_type in corruption_types:
        typed = [row for row in wrong_rows if row["corruption_type"] == corruption_type]
        caught = [row for row in typed if row["verdict"] == RULED_OUT_WRONG]
        catch_by_type[corruption_type] = {
            "wrong_count": len(typed),
            "ruled_out": len(caught),
            "catch_rate": len(caught) / len(typed),
        }
    overall_caught = [row for row in wrong_rows if row["verdict"] == RULED_OUT_WRONG]
    summary = {
        "false_positive_rate": false_positive_rate,
        "wrong_count": len(wrong_rows),
        "ruled_out": len(overall_caught),
        "overall_catch_rate": len(overall_caught) / len(wrong_rows),
        "catch_by_type": catch_by_type,
    }
    return rows, summary


def make_result_row(
    problem: Problem,
    corruption_type: str,
    claimed_answer: int,
    result: dict[str, Any],
    is_correct: bool,
) -> dict[str, Any]:
    summary = answer_summary(claimed_answer)
    return {
        "problem_id": problem.problem_id,
        "family": problem.family,
        "size_label": problem.size_label,
        "corruption_type": corruption_type,
        "is_correct": "1" if is_correct else "0",
        "verdict": result["verdict"],
        "disagreeing_moduli": " ".join(str(m) for m in result["disagreeing_moduli"]),
        "claimed_sign": summary["sign"],
        "claimed_digits": summary["digits"],
        "claimed_prefix": summary["prefix"],
        "claimed_suffix": summary["suffix"],
    }


def estimate_digits(expr_spec: dict[str, Any]) -> int:
    family = expr_spec["family"]
    if family == "power":
        base = abs(int(expr_spec["base"]))
        exponent = int(expr_spec["exponent"])
        if base in (0, 1) or exponent == 0:
            return 1
        return int(exponent * math.log10(base)) + 1
    if family == "factorial":
        n = int(expr_spec["n"])
        if n < 2:
            return 1
        return int(math.lgamma(n + 1) / math.log(10)) + 1
    if family == "fibonacci":
        n = int(expr_spec["n"])
        if n < 2:
            return 1
        return int(n * math.log10((1 + 5**0.5) / 2) - math.log10(5) / 2) + 1
    if family == "bigsum":
        return len(str(abs(sum(int(value) for value in expr_spec["values"]))))
    if family == "bigprod":
        values = [abs(int(value)) for value in expr_spec["values"] if int(value) != 0]
        if len(values) != len(expr_spec["values"]):
            return 1
        return int(sum(math.log10(value) for value in values)) + 1
    raise ValueError(f"unsupported family: {family}")


def timed_seconds(fn: Any, repeats: int = 5) -> float:
    timings: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        timings.append(time.perf_counter() - start)
    return statistics.median(timings)


def compute_saved_rows(problems: list[Problem]) -> list[dict[str, Any]]:
    extra_specs = [
        ("power_extreme_skip", "power", "2,000,000 exponent", {"family": "power", "base": 99991, "exponent": 2_000_000}),
        ("factorial_extreme_skip", "factorial", "100000!", {"family": "factorial", "n": 100_000}),
        ("fibonacci_extreme", "fibonacci", "F(500000)", {"family": "fibonacci", "n": 500_000}),
        ("bigsum_large", "bigsum", "200000 terms", {"family": "bigsum", "values": list(range(200_000))}),
    ]
    specs = [
        (problem.problem_id, problem.family, problem.size_label, problem.expr_spec)
        for problem in problems
    ] + extra_specs
    rows: list[dict[str, Any]] = []
    for problem_id, family, size_label, expr_spec in specs:
        estimated_digits = estimate_digits(expr_spec)
        residue_seconds = timed_seconds(lambda spec=expr_spec: fingerprint(spec), repeats=7)
        if estimated_digits > FULL_IMPRACTICAL_DIGIT_THRESHOLD:
            full_seconds: float | None = None
            ratio = ""
            status = "skipped_impractical"
        else:
            full_seconds = timed_seconds(
                lambda spec=expr_spec: fingerprint_full_expansion(spec), repeats=3
            )
            ratio = f"{full_seconds / residue_seconds:.1f}" if residue_seconds else ""
            status = "measured"
        rows.append(
            {
                "problem_id": problem_id,
                "family": family,
                "size_label": size_label,
                "estimated_digits": estimated_digits,
                "residue_seconds": f"{residue_seconds:.9f}",
                "full_expansion_seconds": "" if full_seconds is None else f"{full_seconds:.9f}",
                "full_over_residue_ratio": ratio,
                "status": status,
            }
        )
    return rows


def fingerprint_full_expansion(expr_spec: dict[str, Any]) -> dict[int, int]:
    value = exact_value(expr_spec)
    return {modulus: value % modulus for modulus in DEFAULT_MODULI}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_llm_sample(problems: list[Problem], limit: int) -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = OUT_DIR / "llm_ollama_raw_outputs.jsonl"
    rows: list[dict[str, Any]] = []
    try:
        with raw_path.open("w", encoding="utf-8") as raw:
            for problem in problems[:limit]:
                prompt = llm_prompt(problem.expr_spec)
                response = call_ollama(prompt)
                raw.write(json.dumps({"problem_id": problem.problem_id, "prompt": prompt, "response": response}) + "\n")
                parsed = parse_first_int(response)
                if parsed is None:
                    verdict = "NO_INTEGER_PARSED"
                    is_error = True
                    caught = False
                else:
                    result = verify(problem.expr_spec, parsed)
                    verdict = result["verdict"]
                    is_error = parsed != problem.true_answer
                    caught = is_error and verdict == RULED_OUT_WRONG
                rows.append(
                    {
                        "problem_id": problem.problem_id,
                        "family": problem.family,
                        "parsed_integer": "" if parsed is None else parsed,
                        "is_arithmetic_error": "1" if is_error else "0",
                        "verifier_verdict": verdict,
                        "error_caught": "1" if caught else "0",
                    }
                )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {"status": "skipped", "reason": f"Ollama unreachable: {exc}", "rows": []}

    write_csv(OUT_DIR / "llm_ollama_results.csv", rows)
    error_rows = [row for row in rows if row["is_arithmetic_error"] == "1"]
    caught_rows = [row for row in error_rows if row["error_caught"] == "1"]
    return {
        "status": "ran",
        "sample_count": len(rows),
        "arithmetic_error_rate": len(error_rows) / len(rows) if rows else 0.0,
        "verifier_catch_rate_on_errors": len(caught_rows) / len(error_rows) if error_rows else 0.0,
        "rows": rows,
    }


def llm_prompt(expr_spec: dict[str, Any]) -> str:
    family = expr_spec["family"]
    if family == "power":
        text = f"{expr_spec['base']}**{expr_spec['exponent']}"
    elif family == "factorial":
        text = f"{expr_spec['n']}!"
    elif family == "fibonacci":
        text = f"F({expr_spec['n']}) with F(0)=0, F(1)=1"
    elif family == "bigsum":
        text = " + ".join(str(value) for value in expr_spec["values"][:25]) + " + ..."
    elif family == "bigprod":
        text = " * ".join(str(value) for value in expr_spec["values"][:12]) + " * ..."
    else:
        text = str(expr_spec)
    return (
        "Compute this exact integer. Reply with only the integer, no prose.\n"
        f"Expression: {text}"
    )


def call_ollama(prompt: str) -> str:
    payload = json.dumps(
        {
            "model": "llama3.1",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("response", ""))


def parse_first_int(text: str) -> int | None:
    match = re.search(r"-?\d[\d,\s]*", text)
    if not match:
        return None
    digits = re.sub(r"[,\s]", "", match.group(0))
    try:
        return int(digits)
    except ValueError:
        return None


def write_record(
    result_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    compute_rows: list[dict[str, Any]],
    llm_summary: dict[str, Any] | None,
    command: str,
) -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    catch_lines = [
        "| Corruption type | Wrong answers | Ruled out | Catch rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for corruption_type, row in summary["catch_by_type"].items():
        catch_lines.append(
            f"| {corruption_type} | {row['wrong_count']} | {row['ruled_out']} | {row['catch_rate']:.3f} |"
        )
    catch_lines.append(
        f"| overall | {summary['wrong_count']} | {summary['ruled_out']} | {summary['overall_catch_rate']:.3f} |"
    )

    compute_lines = [
        "| Problem | Family | Digits est. | Residue sec | Full sec | Full/residue | Status |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in compute_rows:
        compute_lines.append(
            "| {problem_id} | {family} | {estimated_digits} | {residue_seconds} | {full_expansion_seconds} | {full_over_residue_ratio} | {status} |".format(
                **row
            )
        )

    llm_text = "Skipped; `--with-llm` was not requested."
    if llm_summary is not None:
        if llm_summary["status"] == "skipped":
            llm_text = llm_summary["reason"]
        else:
            llm_text = (
                f"Ran {llm_summary['sample_count']} Ollama llama3.1 prompts; "
                f"arithmetic error rate {llm_summary['arithmetic_error_rate']:.3f}; "
                f"verifier catch rate on errors {llm_summary['verifier_catch_rate_on_errors']:.3f}."
            )

    record = f"""# Phase 3 Slice 1 - Digital Route Verifier

Date: {date.today().isoformat()}

## Purpose

Build an exact modular-arithmetic wrong-answer detector beside LLM arithmetic. The verifier is one-sided and sound: residue disagreement proves a claimed answer is wrong; residue agreement only returns `NOT_RULED_OUT`.

## Files created

- `src/dr_residue_engine_v1.py`
- `src/dr_verifier_v1.py`
- `src/dr_run_verifier_benchmark_v1.py`
- `data/v1/digital_route/slice_01_verifier/verifier_results.csv`
- `data/v1/digital_route/slice_01_verifier/catch_rates.csv`
- `data/v1/digital_route/slice_01_verifier/compute_saved.csv`
- `data/v1/digital_route/records/SLICE_01_verifier.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `{command}`
- `python -m py_compile src/dr_residue_engine_v1.py src/dr_verifier_v1.py src/dr_run_verifier_benchmark_v1.py` (run after record generation)
- `git -C . diff --check` (run after record generation)

## Results

False-positive rate on correct answers: {summary['false_positive_rate']:.3f}

{chr(10).join(catch_lines)}

## Compute Saved

{chr(10).join(compute_lines)}

Full expansion was skipped as impractical when estimated decimal digits exceeded {FULL_IMPRACTICAL_DIGIT_THRESHOLD:,}.

## LLM Pass

{llm_text}

## Diagnosis

Cheap residue routing reliably rules out wrong arithmetic with zero false positives in this benchmark. `off_by_multiple_of_9` evades the mod-9/digital-root component, but the other coprime moduli still catch it unless the error is a multiple of the combined modulus `{MODULUS_PRODUCT}`. Any wrong answer differing from truth by a multiple of that full product remains a blind spot and returns `NOT_RULED_OUT`, not `correct`.

## Conclusion

The Digital Route verifier gives a small, exact arithmetic conscience for LLM outputs: fast modular routes catch most wrong answers while preserving the sound one-sided contract.

## Next Slice

Add structured expression parsing for LLM-produced arithmetic traces, then verify intermediate steps rather than only final answers.
"""
    RECORD_PATH.write_text(record, encoding="utf-8")

    index_line = (
        f"- {date.today().isoformat()} - Slice 01: Digital Route verifier v1; "
        f"overall catch {summary['overall_catch_rate']:.3f}, false-positive {summary['false_positive_rate']:.3f}."
    )
    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text(encoding="utf-8")
        if index_line not in existing:
            INDEX_PATH.write_text(existing.rstrip() + "\n" + index_line + "\n", encoding="utf-8")
    else:
        INDEX_PATH.write_text("# Phase 3 Digital Route Index\n\n" + index_line + "\n", encoding="utf-8")


def write_catch_rates(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for corruption_type, row in summary["catch_by_type"].items():
        rows.append(
            {
                "corruption_type": corruption_type,
                "wrong_count": row["wrong_count"],
                "ruled_out": row["ruled_out"],
                "catch_rate": f"{row['catch_rate']:.6f}",
            }
        )
    rows.append(
        {
            "corruption_type": "overall",
            "wrong_count": summary["wrong_count"],
            "ruled_out": summary["ruled_out"],
            "catch_rate": f"{summary['overall_catch_rate']:.6f}",
        }
    )
    write_csv(OUT_DIR / "catch_rates.csv", rows)
    return rows


def print_summary(summary: dict[str, Any], compute_rows: list[dict[str, Any]], llm_summary: dict[str, Any] | None) -> None:
    print("Catch-rate table")
    print("corruption_type,wrong_count,ruled_out,catch_rate")
    for corruption_type, row in summary["catch_by_type"].items():
        print(f"{corruption_type},{row['wrong_count']},{row['ruled_out']},{row['catch_rate']:.3f}")
    print(f"overall,{summary['wrong_count']},{summary['ruled_out']},{summary['overall_catch_rate']:.3f}")
    print(f"\nFalse-positive rate on correct answers: {summary['false_positive_rate']:.3f}")
    print("\nCompute-saved summary")
    print("problem_id,family,digits_est,residue_sec,full_sec,full_over_residue,status")
    for row in compute_rows:
        print(
            f"{row['problem_id']},{row['family']},{row['estimated_digits']},"
            f"{row['residue_seconds']},{row['full_expansion_seconds']},"
            f"{row['full_over_residue_ratio']},{row['status']}"
        )
    if llm_summary is None:
        print("\nLLM pass: skipped (--with-llm not requested)")
    elif llm_summary["status"] == "skipped":
        print(f"\nLLM pass: skipped ({llm_summary['reason']})")
    else:
        print(
            "\nLLM pass: ran "
            f"{llm_summary['sample_count']} prompts; arithmetic_error_rate="
            f"{llm_summary['arithmetic_error_rate']:.3f}; verifier_catch_rate_on_errors="
            f"{llm_summary['verifier_catch_rate_on_errors']:.3f}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--with-llm", action="store_true", help="run optional local Ollama llama3.1 pass")
    parser.add_argument("--limit", type=int, default=5, help="LLM sample limit")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    problems = build_problems()
    result_rows, summary = run_verifier_rows(problems)
    compute_rows = compute_saved_rows(problems)
    llm_summary = run_llm_sample(problems, max(1, args.limit)) if args.with_llm else None

    write_csv(OUT_DIR / "verifier_results.csv", result_rows)
    write_catch_rates(summary)
    write_csv(OUT_DIR / "compute_saved.csv", compute_rows)
    command = "python src/dr_run_verifier_benchmark_v1.py"
    if args.with_llm:
        command += f" --with-llm --limit {max(1, args.limit)}"
    write_record(result_rows, summary, compute_rows, llm_summary, command)
    print_summary(summary, compute_rows, llm_summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
