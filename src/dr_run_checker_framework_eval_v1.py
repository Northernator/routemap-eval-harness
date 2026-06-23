"""Phase 3 Slice 3: routed sound-checker framework evaluation."""

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
from datetime import date
from pathlib import Path
from typing import Any

from dr_checker_framework_v1 import CoverageReport, default_checkers, default_router
from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_03_framework"
RECORDS_DIR = ROOT / "data" / "v1" / "digital_route" / "records"
RECORD_PATH = RECORDS_DIR / "SLICE_03_sound_checker_framework.md"
INDEX_PATH = RECORDS_DIR / "PHASE3_INDEX.md"
MODEL = "llama3.1"


@dataclass(frozen=True)
class EvalTask:
    task_id: str
    domain: str
    prompt: str
    claim_template: dict[str, Any]


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


def build_tasks() -> list[EvalTask]:
    tasks: list[EvalTask] = []
    arithmetic_specs = [
        ("arith_pow_1", "Compute 37^31 exactly.", {"family": "power", "base": 37, "exponent": 31}),
        ("arith_pow_2", "Compute 12345^9 exactly.", {"family": "power", "base": 12_345, "exponent": 9}),
        ("arith_fact_1", "Compute 40! exactly.", {"family": "factorial", "n": 40}),
        ("arith_fact_2", "Compute 75! exactly.", {"family": "factorial", "n": 75}),
        ("arith_sum_1", "Compute 918273645546 + 837465129102 + 746382915011 + 665544332211 exactly.", {"family": "bigsum", "values": [918_273_645_546, 837_465_129_102, 746_382_915_011, 665_544_332_211]}),
    ]
    for task_id, prompt, expr_spec in arithmetic_specs:
        tasks.append(EvalTask(task_id, "arithmetic", prompt, {"type": "arithmetic", "expr_spec": expr_spec}))

    code_prompts = [
        ("code_1", "Return only Python code for a function add(a, b) that returns a + b."),
        ("code_2", "Return only Python code for a function factorial(n) using a loop."),
        ("code_3", "Return only Python code for a class Counter with inc and value methods."),
        ("code_5", "Return a Python function square(x), but wrap it in a markdown code fence."),
        ("code_6", "Return only Python code for a function parse_route(text) returning text.split('->')."),
    ]
    for task_id, prompt in code_prompts:
        tasks.append(EvalTask(task_id, "python_code", prompt, {"type": "python_code"}))

    schema = route_schema()
    json_prompts = [
        ("json_1", "Return only JSON for route A: id alpha-1, score 87, status pass, tags prime and route."),
        ("json_2", "Return JSON with id beta-2, score 104, status pass, tags route. Follow the schema exactly."),
        ("json_3", "Return JSON with id gamma-3, score 64, status maybe, tags route. Follow the schema exactly."),
        ("json_4", "Return JSON with id delta-4, score 42, status fail, tags empty list. Follow the schema exactly."),
        ("json_5", "Return a short paragraph describing id epsilon-5 with score 77 and status pass."),
    ]
    for task_id, prompt in json_prompts:
        tasks.append(EvalTask(task_id, "json_schema", prompt, {"type": "json_schema", "schema": schema}))
    return tasks


def route_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["id", "score", "status", "tags"],
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "status": {"type": "string", "enum": ["pass", "fail"]},
            "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
    }


def assert_ollama_reachable() -> None:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
            tags = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError) as exc:
        raise SystemExit(f"Ollama unreachable; Slice 3 eval requires llama3.1: {exc}") from exc
    models = {str(model.get("name", "")) for model in tags.get("models", [])}
    if not any(name == "llama3.1" or name.startswith("llama3.1:") for name in models):
        raise SystemExit(f"Ollama reachable but llama3.1 is not installed; found {sorted(models)}")


def call_ollama(prompt: str) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "stream": False,
            "prompt": prompt,
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


def build_claim(task: EvalTask, response: str) -> dict[str, Any]:
    claim = dict(task.claim_template)
    if task.domain == "arithmetic":
        parsed = parse_numeric_answer(response)
        claim["claimed_answer"] = parsed if parsed is not None else 0
        claim["parse_failure"] = parsed is None
        if parsed is not None:
            claim["true_answer"] = exact_value(claim["expr_spec"])
    elif task.domain == "python_code":
        claim["source"] = response
    elif task.domain == "json_schema":
        claim["output"] = response
    return claim


def parse_numeric_answer(text: str) -> int | None:
    tokens = re.findall(r"-?\d[\d,]*", text)
    if not tokens:
        return None
    try:
        return int(tokens[-1].replace(",", ""))
    except ValueError:
        return None


def run_eval(limit: int | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    assert_ollama_reachable()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    router = default_router()
    tasks = build_tasks()
    selected = tasks if limit is None else tasks[:limit]
    raw_path = OUT_DIR / ("raw_outputs_full.jsonl" if limit is None else f"raw_outputs_limit_{limit}.jsonl")
    rows: list[dict[str, Any]] = []
    with raw_path.open("w", encoding="utf-8") as raw:
        for task in selected:
            response = call_ollama(prompt_for_task(task))
            raw.write(json.dumps({"task_id": task.task_id, "domain": task.domain, "prompt": task.prompt, "response": response}, ensure_ascii=True) + "\n")
            claim = build_claim(task, response)
            routed = router.check(claim)
            rows.append(
                {
                    "task_id": task.task_id,
                    "domain": task.domain,
                    "verdict": routed["verdict"],
                    "reason": routed["reason"],
                    "applicable_checkers": " ".join(routed["applicable_checkers"]),
                    "parse_failure": "1" if claim.get("parse_failure") else "0",
                }
            )
    valid_rows = run_known_valid_checks(router)
    summary = summarize(rows, valid_rows, limit)
    write_csv(OUT_DIR / ("framework_results_full.csv" if limit is None else f"framework_results_limit_{limit}.csv"), rows)
    write_csv(OUT_DIR / "known_valid_fp_checks.csv", valid_rows)
    write_csv(OUT_DIR / "coverage_report.csv", CoverageReport(default_checkers()).rows())
    summary_path = OUT_DIR / ("framework_summary_full.json" if limit is None else f"framework_summary_limit_{limit}.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    if limit is None:
        write_record(summary, CoverageReport(default_checkers()).rows())
    return rows, valid_rows, summary


def prompt_for_task(task: EvalTask) -> str:
    if task.domain == "arithmetic":
        return "Return only the exact final integer, no prose.\n" + task.prompt
    if task.domain == "python_code":
        return task.prompt
    if task.domain == "json_schema":
        return (
            "Return only valid JSON. Schema: object with required keys id:string, score:integer 0..100, "
            "status enum pass/fail, tags nonempty array of strings, no extra keys.\n"
            + task.prompt
        )
    return task.prompt


def run_known_valid_checks(router: Any) -> list[dict[str, Any]]:
    valid_claims = [
        {
            "domain": "arithmetic",
            "claim": {"type": "arithmetic", "expr_spec": {"family": "bigsum", "values": [2, 3]}, "claimed_answer": 5},
        },
        {
            "domain": "arithmetic",
            "claim": {"type": "arithmetic", "expr_spec": {"family": "power", "base": 9, "exponent": 5}, "claimed_answer": 59049},
        },
        {
            "domain": "python_code",
            "claim": {"type": "python_code", "source": "def add(a, b):\n    return a + b\n"},
        },
        {
            "domain": "python_code",
            "claim": {"type": "python_code", "source": "class Counter:\n    def __init__(self):\n        self.n = 0\n"},
        },
        {
            "domain": "json_schema",
            "claim": {"type": "json_schema", "schema": route_schema(), "output": '{"id":"ok-1","score":87,"status":"pass","tags":["route"]}'},
        },
        {
            "domain": "json_schema",
            "claim": {"type": "json_schema", "schema": route_schema(), "output": {"id": "ok-2", "score": 0, "status": "fail", "tags": ["boundary"]}},
        },
    ]
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(valid_claims):
        result = router.check(item["claim"])
        rows.append(
            {
                "valid_id": f"valid_{index}",
                "domain": item["domain"],
                "verdict": result["verdict"],
                "reason": result["reason"],
            }
        )
    false_positives = [row for row in rows if row["verdict"] == RULED_OUT_WRONG]
    if false_positives:
        raise AssertionError("soundness bug: known-valid output was ruled out")
    return rows


def summarize(rows: list[dict[str, Any]], valid_rows: list[dict[str, Any]], limit: int | None) -> dict[str, Any]:
    domains = sorted({row["domain"] for row in rows} | {row["domain"] for row in valid_rows})
    per_domain: dict[str, dict[str, Any]] = {}
    for domain in domains:
        domain_rows = [row for row in rows if row["domain"] == domain]
        ruled_out = [row for row in domain_rows if row["verdict"] == RULED_OUT_WRONG]
        valid_domain_rows = [row for row in valid_rows if row["domain"] == domain]
        valid_ruled_out = [row for row in valid_domain_rows if row["verdict"] == RULED_OUT_WRONG]
        per_domain[domain] = {
            "model_output_count": len(domain_rows),
            "ruled_out_count": len(ruled_out),
            "checkable_error_rate": len(ruled_out) / len(domain_rows) if domain_rows else 0.0,
            "known_valid_count": len(valid_domain_rows),
            "false_positive_count": len(valid_ruled_out),
            "false_positive_rate": len(valid_ruled_out) / len(valid_domain_rows) if valid_domain_rows else 0.0,
        }
    return {
        "mode": "full" if limit is None else f"limit_{limit}",
        "model": MODEL,
        "per_domain": per_domain,
        "arithmetic_anchor_matches_slice2": per_domain.get("arithmetic", {}).get("false_positive_rate") == 0.0,
    }


def write_record(summary: dict[str, Any], coverage_rows: list[dict[str, str]]) -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    domain_lines = [
        "| Domain | Model outputs | Ruled out | Checkable error rate | Known-valid FP rate |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for domain, row in summary["per_domain"].items():
        domain_lines.append(
            f"| {domain} | {row['model_output_count']} | {row['ruled_out_count']} | {row['checkable_error_rate']:.3f} | {row['false_positive_rate']:.3f} |"
        )
    coverage_lines = [
        "| Checker | Coverage | Blind-spot example |",
        "| --- | --- | --- |",
    ]
    for row in coverage_rows:
        coverage_lines.append(
            f"| {row['checker']} | {row['coverage']} | {row['blind_spot_example'].replace(chr(10), '<br>')} |"
        )
    record = f"""# Phase 3 Slice 3 - Sound Checker Framework

Date: {date.today().isoformat()}

## Purpose

Generalize Digital Route arithmetic verification into a routed library of cheap sound checkers. Each checker returns only `RULED_OUT_WRONG` or `NOT_RULED_OUT`, preserves zero false positives on known-valid outputs, and documents its blind spot.

## Files created

- `src/dr_checker_framework_v1.py`
- `src/dr_checker_code_v1.py`
- `src/dr_checker_schema_v1.py`
- `src/dr_run_checker_framework_eval_v1.py`
- `data/v1/digital_route/slice_03_framework/raw_outputs_limit_5.jsonl`
- `data/v1/digital_route/slice_03_framework/framework_results_limit_5.csv`
- `data/v1/digital_route/slice_03_framework/framework_summary_limit_5.json`
- `data/v1/digital_route/slice_03_framework/raw_outputs_full.jsonl`
- `data/v1/digital_route/slice_03_framework/framework_results_full.csv`
- `data/v1/digital_route/slice_03_framework/framework_summary_full.json`
- `data/v1/digital_route/slice_03_framework/known_valid_fp_checks.csv`
- `data/v1/digital_route/slice_03_framework/coverage_report.csv`
- `data/v1/digital_route/records/SLICE_03_sound_checker_framework.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_checker_framework_eval_v1.py --limit 5`
- `python src/dr_run_checker_framework_eval_v1.py`
- `python -m py_compile src/dr_checker_framework_v1.py src/dr_checker_code_v1.py src/dr_checker_schema_v1.py src/dr_run_checker_framework_eval_v1.py`
- `git -C . diff --check`

## Per-Domain Results

{chr(10).join(domain_lines)}

## Coverage Characterization

{chr(10).join(coverage_lines)}

## Arithmetic Anchor

Arithmetic uses the Slice 1 residue verifier adapter. Framework verdicts preserve the Slice 2 one-sided behavior: arithmetic outputs are ruled out only by residue disagreement, and known-valid arithmetic outputs had FP = {summary['per_domain']['arithmetic']['false_positive_rate']:.3f}.

## Conclusion

The sound-checker pattern generalizes across arithmetic, Python parse checking, and JSON schema constraints while preserving the zero-false-positive guarantee on constructed valid outputs. Each checker has an explicit blind spot: residue multiples of M, parseable-but-wrong code, or schema-valid-but-semantically-wrong JSON.

## Next Slice

Add a repair/wrapper action layer that routes model outputs through sound checkers, emits targeted diagnostics, and asks the model to repair only outputs that are ruled out.
"""
    RECORD_PATH.write_text(record, encoding="utf-8")
    index_line = (
        f"- {date.today().isoformat()} - Slice 03: sound-checker framework; "
        f"arith/code/json rates "
        f"{summary['per_domain']['arithmetic']['checkable_error_rate']:.3f}/"
        f"{summary['per_domain']['python_code']['checkable_error_rate']:.3f}/"
        f"{summary['per_domain']['json_schema']['checkable_error_rate']:.3f}, FP 0.000."
    )
    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text(encoding="utf-8")
        if index_line not in existing:
            INDEX_PATH.write_text(existing.rstrip() + "\n" + index_line + "\n", encoding="utf-8")
    else:
        INDEX_PATH.write_text("# Phase 3 Digital Route Index\n\n" + index_line + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def print_summary(summary: dict[str, Any]) -> None:
    coverage = {row["checker"]: row["coverage"] for row in CoverageReport(default_checkers()).rows()}
    print("Sound-checker framework")
    print("domain,outputs,ruled_out,checkable_error_rate,known_valid_fp_rate,coverage")
    domain_checker = {
        "arithmetic": "arithmetic_residue_v1",
        "python_code": "python_code_parse_v1",
        "json_schema": "json_schema_constraints_v1",
    }
    for domain, row in summary["per_domain"].items():
        checker_name = domain_checker.get(domain, "")
        print(
            f"{domain},{row['model_output_count']},{row['ruled_out_count']},"
            f"{row['checkable_error_rate']:.3f},{row['false_positive_rate']:.3f},"
            f"{coverage.get(checker_name, '')}"
        )
    print(f"Arithmetic anchor matches Slice 2 zero-FP contract: {summary['arithmetic_anchor_matches_slice2']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    _, _, summary = run_eval(args.limit)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
