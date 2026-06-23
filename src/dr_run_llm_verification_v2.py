"""Phase 3 Slice 2: real llama 3.1 arithmetic verification."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dr_residue_engine_v1 import DEFAULT_MODULI
from dr_verifier_v1 import RULED_OUT_WRONG, verify


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_02_real_model"
MODEL = "llama3.1"
MODULUS_PRODUCT = math.prod(DEFAULT_MODULI)


@dataclass(frozen=True)
class LlmProblem:
    problem_id: str
    family: str
    prompt: str
    expr_spec: dict[str, Any]
    true_answer: int


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


def build_problem_battery() -> list[LlmProblem]:
    specs: list[tuple[str, str, str, dict[str, Any]]] = []
    specs.extend(
        [
            ("pow_17_19", "power", "Compute 17^19 exactly.", {"family": "power", "base": 17, "exponent": 19}),
            ("pow_97_13", "power", "Compute 97^13 exactly.", {"family": "power", "base": 97, "exponent": 13}),
            ("pow_12345_9", "power", "Compute 12345^9 exactly.", {"family": "power", "base": 12_345, "exponent": 9}),
            ("pow_99991_7", "power", "Compute 99991^7 exactly.", {"family": "power", "base": 99_991, "exponent": 7}),
            ("pow_2_256", "power", "Compute 2^256 exactly.", {"family": "power", "base": 2, "exponent": 256}),
            ("pow_37_31", "power", "Compute 37^31 exactly.", {"family": "power", "base": 37, "exponent": 31}),
        ]
    )
    specs.extend(
        [
            ("fact_18", "factorial", "Compute 18! exactly.", {"family": "factorial", "n": 18}),
            ("fact_25", "factorial", "Compute 25! exactly.", {"family": "factorial", "n": 25}),
            ("fact_30", "factorial", "Compute 30! exactly.", {"family": "factorial", "n": 30}),
            ("fact_40", "factorial", "Compute 40! exactly.", {"family": "factorial", "n": 40}),
            ("fact_50", "factorial", "Compute 50! exactly.", {"family": "factorial", "n": 50}),
            ("fact_75", "factorial", "Compute 75! exactly.", {"family": "factorial", "n": 75}),
        ]
    )
    sum_cases = [
        [918_273_645_546, 837_465_129_102, 746_382_915_011, 665_544_332_211, 554_433_221_100],
        [10_000_000_019, 20_000_000_033, 30_000_000_057, 40_000_000_091, 50_000_000_123, 60_000_000_177],
        [987_654_321_987, -123_456_789_123, 456_789_123_456, -222_222_222_222, 333_333_333_333],
        [7_654_321_001, 8_765_432_011, 9_876_543_021, 1_234_567_891, 2_345_678_902, 3_456_789_013],
    ]
    for index, values in enumerate(sum_cases, start=1):
        specs.append(
            (
                f"sum_big_{index}",
                "bigsum",
                "Compute this integer sum exactly: " + " + ".join(str(v) for v in values) + ".",
                {"family": "bigsum", "values": values},
            )
        )
    prod_cases = [
        [123_457, 234_569, 345_679, 456_791],
        [1_003, 10_007, 100_003, 1_000_003],
        [37_037, 74_081, 111_121, 148_149, 185_183],
        [999_983, 999_979, 999_961],
    ]
    for index, values in enumerate(prod_cases, start=1):
        specs.append(
            (
                f"prod_big_{index}",
                "bigprod",
                "Compute this integer product exactly: " + " x ".join(str(v) for v in values) + ".",
                {"family": "bigprod", "values": values},
            )
        )
    fib_specs = [
        ("fib_80", 80),
        ("fib_120", 120),
        ("fib_200", 200),
    ]
    for problem_id, n in fib_specs:
        specs.append(
            (
                problem_id,
                "fibonacci",
                f"Compute Fibonacci F({n}) exactly, where F(0)=0 and F(1)=1.",
                {"family": "fibonacci", "n": n},
            )
        )
    modular_cases = [
        ("mod_route_1", [pow(97, 13, 101), pow(41, 9, 101), 58], "A route checksum adds residues (97^13 mod 101), (41^9 mod 101), and 58. Compute that exact checksum."),
        ("mod_route_2", [pow(12345, 7, 37), pow(24691, 5, 37), 19], "A cyclic route adds residues (12345^7 mod 37), (24691^5 mod 37), and 19. Compute that exact checksum."),
        ("mod_route_3", [pow(88, 17, 89), pow(144, 11, 89), pow(233, 7, 89)], "A modular word problem asks for the sum of residues (88^17 mod 89), (144^11 mod 89), and (233^7 mod 89). Give the exact sum."),
    ]
    for problem_id, values, prompt in modular_cases:
        specs.append((problem_id, "modular_word_bigsum", prompt, {"family": "bigsum", "values": values}))
    specs.extend(
        [
            ("easy_sum_1", "bigsum", "Compute 2 + 3 exactly.", {"family": "bigsum", "values": [2, 3]}),
            ("easy_sum_2", "bigsum", "Compute 123 + 456 + 789 exactly.", {"family": "bigsum", "values": [123, 456, 789]}),
            ("easy_prod_1", "bigprod", "Compute 12 x 13 exactly.", {"family": "bigprod", "values": [12, 13]}),
            ("easy_fact_1", "factorial", "Compute 8! exactly.", {"family": "factorial", "n": 8}),
            ("easy_power_1", "power", "Compute 9^5 exactly.", {"family": "power", "base": 9, "exponent": 5}),
            ("easy_fib_1", "fibonacci", "Compute Fibonacci F(12) exactly, where F(0)=0 and F(1)=1.", {"family": "fibonacci", "n": 12}),
        ]
    )

    return [
        LlmProblem(problem_id, family, prompt, expr_spec, exact_value(expr_spec))
        for problem_id, family, prompt, expr_spec in specs
    ]


def call_ollama(prompt: str) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "stream": False,
            "prompt": (
                "Return only the final integer answer. Do not show work. "
                "No commas unless needed for readability.\n\n"
                + prompt
            ),
            "options": {"temperature": 0},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("response", ""))


def assert_ollama_reachable() -> None:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
            tags = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError) as exc:
        raise SystemExit(f"Ollama unreachable; Slice 2 real-model pass requires llama3.1: {exc}") from exc
    models = {str(model.get("name", "")) for model in tags.get("models", [])}
    if not any(name == "llama3.1" or name.startswith("llama3.1:") for name in models):
        raise SystemExit(f"Ollama reachable but llama3.1 is not installed; found {sorted(models)}")


def parse_numeric_answer(text: str) -> tuple[int | None, str]:
    answer_match = re.search(r'"answer"\s*:\s*"?(?P<answer>-?\d[\d,\s]*)"?', text, flags=re.I)
    if answer_match:
        token = answer_match.group("answer")
    else:
        final_match = re.search(r"(?:answer|final)\D+(-?\d[\d,]*)", text, flags=re.I)
        if final_match:
            token = final_match.group(1)
        else:
            tokens = re.findall(r"-?\d[\d,]*", text)
            if not tokens:
                return None, "no_integer"
            token = tokens[-1]
    try:
        return int(re.sub(r"[,\s]", "", token)), "parsed"
    except ValueError:
        return None, "parse_error"


def timed_seconds(fn: Any) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def run(limit: int | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    assert_ollama_reachable()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    problems = build_problem_battery()
    selected = problems if limit is None else problems[:limit]
    raw_path = OUT_DIR / ("llm_raw_outputs_full.jsonl" if limit is None else f"llm_raw_outputs_limit_{limit}.jsonl")
    rows: list[dict[str, Any]] = []
    with raw_path.open("w", encoding="utf-8") as raw:
        for problem in selected:
            response = call_ollama(problem.prompt)
            raw.write(json.dumps({"problem_id": problem.problem_id, "prompt": problem.prompt, "response": response}, ensure_ascii=True) + "\n")
            parsed, parse_status = parse_numeric_answer(response)
            if parsed is None:
                rows.append(
                    {
                        "problem_id": problem.problem_id,
                        "family": problem.family,
                        "parse_status": parse_status,
                        "is_arithmetic_error": "",
                        "verifier_verdict": "NOT_RUN_PARSE_FAILURE",
                        "error_caught": "",
                        "difference_multiple_of_M": "",
                        "difference": "",
                        "verifier_seconds": "",
                        "exact_check_seconds": "",
                        "true_digits": len(str(abs(problem.true_answer))),
                        "claimed_digits": "",
                    }
                )
                continue
            verifier_seconds = timed_seconds(lambda: verify(problem.expr_spec, parsed))
            result = verify(problem.expr_spec, parsed)
            exact_check_seconds = timed_seconds(lambda: exact_value(problem.expr_spec) == parsed)
            is_error = parsed != problem.true_answer
            difference = problem.true_answer - parsed
            rows.append(
                {
                    "problem_id": problem.problem_id,
                    "family": problem.family,
                    "parse_status": parse_status,
                    "is_arithmetic_error": "1" if is_error else "0",
                    "verifier_verdict": result["verdict"],
                    "error_caught": "1" if is_error and result["verdict"] == RULED_OUT_WRONG else "0",
                    "difference_multiple_of_M": "1" if difference % MODULUS_PRODUCT == 0 else "0",
                    "difference": difference,
                    "verifier_seconds": f"{verifier_seconds:.9f}",
                    "exact_check_seconds": f"{exact_check_seconds:.9f}",
                    "true_digits": len(str(abs(problem.true_answer))),
                    "claimed_digits": len(str(abs(parsed))),
                }
            )
    summary = summarize(rows, limit)
    write_csv(OUT_DIR / ("llm_results_full.csv" if limit is None else f"llm_results_limit_{limit}.csv"), rows)
    summary_path = OUT_DIR / ("llm_summary_full.json" if limit is None else f"llm_summary_limit_{limit}.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return rows, summary


def summarize(rows: list[dict[str, Any]], limit: int | None) -> dict[str, Any]:
    parsed_rows = [row for row in rows if row["parse_status"] == "parsed"]
    parse_failures = [row for row in rows if row["parse_status"] != "parsed"]
    error_rows = [row for row in parsed_rows if row["is_arithmetic_error"] == "1"]
    correct_rows = [row for row in parsed_rows if row["is_arithmetic_error"] == "0"]
    caught_rows = [row for row in error_rows if row["verifier_verdict"] == RULED_OUT_WRONG]
    false_positive_rows = [row for row in correct_rows if row["verifier_verdict"] == RULED_OUT_WRONG]
    missed_rows = [row for row in error_rows if row["verifier_verdict"] != RULED_OUT_WRONG]
    if false_positive_rows:
        raise AssertionError("soundness bug: verifier ruled out a correct model answer")
    verifier_total = sum(float(row["verifier_seconds"]) for row in parsed_rows)
    exact_total = sum(float(row["exact_check_seconds"]) for row in parsed_rows)
    return {
        "mode": "full" if limit is None else f"limit_{limit}",
        "model": MODEL,
        "modulus_product": MODULUS_PRODUCT,
        "problem_count": len(rows),
        "parsed_count": len(parsed_rows),
        "parse_failure_count": len(parse_failures),
        "parse_failure_rate": len(parse_failures) / len(rows) if rows else 0.0,
        "arithmetic_error_count": len(error_rows),
        "arithmetic_error_rate": len(error_rows) / len(parsed_rows) if parsed_rows else 0.0,
        "verifier_caught_error_count": len(caught_rows),
        "verifier_catch_rate_on_errors": len(caught_rows) / len(error_rows) if error_rows else 0.0,
        "correct_count": len(correct_rows),
        "false_positive_count": len(false_positive_rows),
        "false_positive_rate": 0.0,
        "missed_error_count": len(missed_rows),
        "missed_errors": [
            {
                "problem_id": row["problem_id"],
                "family": row["family"],
                "difference": row["difference"],
                "difference_multiple_of_M": row["difference_multiple_of_M"],
            }
            for row in missed_rows
        ],
        "verifier_seconds_total": verifier_total,
        "exact_check_seconds_total": exact_total,
        "verified_throughput_ratio_exact_over_residue": exact_total / verifier_total if verifier_total else None,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def print_summary(summary: dict[str, Any]) -> None:
    print("Real llama 3.1 verification")
    print(f"mode: {summary['mode']}")
    print(f"problems: {summary['problem_count']}")
    print(f"parsed: {summary['parsed_count']}")
    print(f"parse_failures: {summary['parse_failure_count']} ({summary['parse_failure_rate']:.3f})")
    print(f"LLM arithmetic error rate: {summary['arithmetic_error_rate']:.3f}")
    print(f"Verifier catch rate on real errors: {summary['verifier_catch_rate_on_errors']:.3f}")
    print(f"False-positive rate on correct answers: {summary['false_positive_rate']:.3f}")
    print(f"Missed errors: {summary['missed_error_count']}")
    for missed in summary["missed_errors"]:
        print(
            "missed,"
            f"{missed['problem_id']},{missed['family']},"
            f"difference_multiple_of_M={missed['difference_multiple_of_M']},"
            f"difference={missed['difference']}"
        )
    print(
        "Verified-throughput exact/residue ratio: "
        f"{summary['verified_throughput_ratio_exact_over_residue']:.3f}"
        if summary["verified_throughput_ratio_exact_over_residue"] is not None
        else "Verified-throughput exact/residue ratio: n/a"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="smoke limit; omit for full battery")
    args = parser.parse_args()
    _, summary = run(args.limit)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
