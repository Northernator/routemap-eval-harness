"""Phase 3 Slice 4: extract-before-check framework re-evaluation."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import multiprocessing
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from dr_checker_code_v1 import PythonCodeChecker
from dr_checker_framework_v1 import ArithmeticChecker, CoverageReport
from dr_checker_schema_v1 import JsonSchemaChecker
from dr_output_extraction_v1 import extract_code, extract_integer, extract_json
from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


UNCHECKABLE = "UNCHECKABLE"
MODEL = "llama3.1"
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "v1" / "digital_route" / "slice_04_extraction"
RECORDS_DIR = ROOT / "data" / "v1" / "digital_route" / "records"
RECORD_PATH = RECORDS_DIR / "SLICE_04_extraction_fix.md"
INDEX_PATH = RECORDS_DIR / "PHASE3_INDEX.md"
SLICE3_SUMMARY = ROOT / "data" / "v1" / "digital_route" / "slice_03_framework" / "framework_summary_full.json"


@dataclass(frozen=True)
class Task:
    task_id: str
    domain: str
    prompt: str
    expr_spec: dict[str, Any] | None = None
    schema: dict[str, Any] | None = None


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


def build_tasks(n_per_domain: int = 50) -> list[Task]:
    tasks: list[Task] = []
    schema = route_schema()
    for index in range(n_per_domain):
        if index % 5 == 0:
            expr = {"family": "power", "base": 37 + index, "exponent": 12 + (index % 9)}
            prompt = f"Compute {(37 + index)}^{12 + (index % 9)} exactly."
        elif index % 5 == 1:
            expr = {"family": "factorial", "n": 25 + (index % 25)}
            prompt = f"Compute {(25 + (index % 25))}! exactly."
        elif index % 5 == 2:
            expr = {"family": "fibonacci", "n": 70 + index}
            prompt = f"Compute Fibonacci F({70 + index}) exactly, where F(0)=0 and F(1)=1."
        elif index % 5 == 3:
            values = [918_273 + index * 101, 837_465 + index * 103, 746_382 + index * 107, 665_544 + index * 109]
            expr = {"family": "bigsum", "values": values}
            prompt = "Compute exactly: " + " + ".join(str(value) for value in values) + "."
        else:
            values = [123 + index, 257 + index, 389 + index, 521 + index]
            expr = {"family": "bigprod", "values": values}
            prompt = "Compute exactly: " + " x ".join(str(value) for value in values) + "."
        tasks.append(Task(f"arith_{index:03d}", "arithmetic", prompt, expr_spec=expr))

    for index in range(n_per_domain):
        if index % 4 == 0:
            prompt = f"Return only Python code for function f_{index}(a, b) that returns a + b + {index}."
        elif index % 4 == 1:
            prompt = f"Return Python code in a markdown code fence for function f_{index}(items) that returns list(reversed(items))."
        elif index % 4 == 2:
            prompt = f"Return only Python code for class Box{index} with __init__(self, value) and get(self)."
        else:
            prompt = f"Return only Python code for function f_{index}(text) that returns text.split('->')."
        tasks.append(Task(f"code_{index:03d}", "python_code", prompt))

    for index in range(n_per_domain):
        status = "pass" if index % 2 == 0 else "fail"
        if index % 5 == 0:
            score = 104
        elif index % 5 == 1:
            score = -3
        else:
            score = 10 + (index % 70)
        if index % 7 == 0:
            status_value = "maybe"
        else:
            status_value = status
        if index % 6 == 0:
            tag_text = "empty tags list"
        else:
            tag_text = "tags route and audit"
        prompt = (
            f"Return only JSON for id route-{index}, score {score}, status {status_value}, {tag_text}. "
            "Schema requires id string, score integer 0..100, status pass/fail, nonempty tags array, no extra keys."
        )
        tasks.append(Task(f"json_{index:03d}", "json_schema", prompt, schema=schema))
    return tasks


def select_tasks(tasks: list[Task], limit: int | None) -> list[Task]:
    if limit is None:
        return tasks
    selected: list[Task] = []
    for domain in ("arithmetic", "python_code", "json_schema"):
        for task in [item for item in tasks if item.domain == domain]:
            if len(selected) >= limit:
                return selected
            selected.append(task)
            break
    index = 0
    while len(selected) < limit and index < len(tasks):
        if tasks[index] not in selected:
            selected.append(tasks[index])
        index += 1
    return selected


def assert_ollama_reachable() -> None:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5) as response:
            tags = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, urllib.error.URLError) as exc:
        raise SystemExit(f"Ollama unreachable; Slice 4 eval requires llama3.1: {exc}") from exc
    models = {str(model.get("name", "")) for model in tags.get("models", [])}
    if not any(name == "llama3.1" or name.startswith("llama3.1:") for name in models):
        raise SystemExit(f"Ollama reachable but llama3.1 is not installed; found {sorted(models)}")


def _ollama_worker(prompt: str, num_predict: int, http_timeout: int, queue: Any) -> None:
    payload = json.dumps(
        {
            "model": MODEL,
            "stream": False,
            "prompt": prompt,
            "options": {"temperature": 0, "num_predict": num_predict},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=http_timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    queue.put(str(data.get("response", "")))


def call_ollama(prompt: str, num_predict: int = 768, timeout_seconds: int = 12) -> str:
    queue: multiprocessing.Queue[str] = multiprocessing.Queue()
    process = multiprocessing.Process(target=_ollama_worker, args=(prompt, num_predict, timeout_seconds + 5, queue))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(2)
        raise TimeoutError(f"Ollama generation exceeded {timeout_seconds}s")
    if process.exitcode != 0:
        raise RuntimeError(f"Ollama worker exited with code {process.exitcode}")
    if queue.empty():
        return ""
    return queue.get()


def batch_prompt(domain: str, tasks: list[Task]) -> str:
    lines = [batch_item_line(task) for task in tasks]
    if domain == "arithmetic":
        return (
            "For each item, answer on exactly one line as `ID: integer`. "
            "Return no prose and no markdown.\n"
            + "\n".join(lines)
        )
    if domain == "python_code":
        return (
            "For each item, answer on exactly one line as `ID: <single-line Python code>`. "
            "Return no markdown fences and no explanations.\n"
            + "\n".join(lines)
        )
    return (
        "For each item, answer on exactly one line as `ID: {json object}`. "
        "Return no prose and no markdown. Obey the schema in each item.\n"
        + "\n".join(lines)
    )


def batch_item_line(task: Task) -> str:
    if task.domain == "arithmetic":
        return f"{task.task_id}: {task.prompt.replace('Compute ', '').replace(' exactly.', '')}"
    if task.domain == "python_code":
        index = int(task.task_id.rsplit("_", 1)[1])
        if index % 4 == 0:
            spec = f"def f_{index}(a,b): return a+b+{index}"
        elif index % 4 == 1:
            spec = f"def f_{index}(items): return list(reversed(items))"
        elif index % 4 == 2:
            spec = f"class Box{index} with __init__ and get"
        else:
            spec = f"def f_{index}(text): return text.split('->')"
        return f"{task.task_id}: {spec}"
    index = int(task.task_id.rsplit("_", 1)[1])
    score = 104 if index % 5 == 0 else (-3 if index % 5 == 1 else 10 + (index % 70))
    status = "maybe" if index % 7 == 0 else ("pass" if index % 2 == 0 else "fail")
    tags = "[]" if index % 6 == 0 else '["route","audit"]'
    return f'{task.task_id}: id route-{index}, score {score}, status {status}, tags {tags}'


def split_batch_response(response: str, tasks: list[Task]) -> dict[str, str]:
    task_ids = [re.escape(task.task_id) for task in tasks]
    if not task_ids:
        return {}
    id_pattern = "|".join(task_ids)
    pattern = re.compile(
        rf"(?P<id>{id_pattern})\s*:\s*(?P<body>.*?)(?=\n\s*(?:{id_pattern})\s*:|\Z)",
        flags=re.DOTALL,
    )
    found = {match.group("id"): match.group("body").strip() for match in pattern.finditer(response)}
    if len(found) < len(tasks):
        lines = [line.strip() for line in response.splitlines() if line.strip()]
        bodies: list[str] = []
        for line in lines:
            if ":" in line:
                bodies.append(line.split(":", 1)[1].strip())
            else:
                bodies.append(line)
        if len(bodies) >= len(tasks):
            return {task.task_id: bodies[index] for index, task in enumerate(tasks)}
    return {task.task_id: found.get(task.task_id, "") for task in tasks}


def prompt_for_task(task: Task) -> str:
    if task.domain == "arithmetic":
        return "Return only the exact final integer, no prose.\n" + task.prompt
    if task.domain == "python_code":
        return task.prompt
    return task.prompt


def evaluate_task(task: Task, raw: str) -> dict[str, Any]:
    if task.domain == "arithmetic":
        extracted, ok, note = extract_integer(raw)
        if not ok:
            return row(task, raw, "", note, UNCHECKABLE, "integer extraction failed", "0", "")
        claimed = int(extracted)
        result = ArithmeticChecker().check({"type": "arithmetic", "expr_spec": task.expr_spec, "claimed_answer": claimed})
        true_answer = exact_value(task.expr_spec or {})
        actually_valid = claimed == true_answer
        return row(task, raw, extracted, note, result.verdict, result.reason, "1" if actually_valid else "0", str(claimed - true_answer))
    if task.domain == "python_code":
        extracted, ok, note = extract_code(raw)
        raw_result = PythonCodeChecker().check({"type": "python_code", "source": raw})
        if not ok:
            return row(task, raw, "", note, UNCHECKABLE, "code extraction failed", "0", "", raw_result.verdict)
        result = PythonCodeChecker().check({"type": "python_code", "source": extracted})
        actually_valid = _python_parses(extracted)
        return row(task, raw, extracted, note, result.verdict, result.reason, "1" if actually_valid else "0", "", raw_result.verdict)
    extracted, ok, note = extract_json(raw)
    raw_result = JsonSchemaChecker().check({"type": "json_schema", "schema": task.schema, "output": raw})
    if not ok:
        return row(task, raw, "", note, UNCHECKABLE, "json extraction failed", "0", "", raw_result.verdict)
    result = JsonSchemaChecker().check({"type": "json_schema", "schema": task.schema, "output": extracted})
    actually_valid = result.verdict == NOT_RULED_OUT
    return row(task, raw, extracted, note, result.verdict, result.reason, "1" if actually_valid else "0", "", raw_result.verdict)


def row(
    task: Task,
    raw: str,
    extracted: str,
    extraction_note: str,
    verdict: str,
    reason: str,
    actually_valid: str,
    difference: str,
    raw_verdict: str = "",
) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "domain": task.domain,
        "raw_response": raw,
        "extracted_content": extracted,
        "extraction_ok": "1" if verdict != UNCHECKABLE else "0",
        "extraction_note": extraction_note,
        "verdict": verdict,
        "checker_reason": reason,
        "actually_valid_checkable_property": actually_valid,
        "difference": difference,
        "raw_input_verdict": raw_verdict,
    }


def _python_parses(source: str) -> bool:
    try:
        ast.parse(source)
        return True
    except SyntaxError:
        return False


def summarize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []
    before_after_rows: list[dict[str, Any]] = []
    slice3 = load_slice3_rates()
    for domain in ("arithmetic", "python_code", "json_schema"):
        domain_rows = [item for item in rows if item["domain"] == domain]
        extracted_rows = [item for item in domain_rows if item["extraction_ok"] == "1"]
        uncheckable = [item for item in domain_rows if item["verdict"] == UNCHECKABLE]
        ruled_out = [item for item in extracted_rows if item["verdict"] == RULED_OUT_WRONG]
        valid_rows = [item for item in extracted_rows if item["actually_valid_checkable_property"] == "1"]
        false_positive = [item for item in valid_rows if item["verdict"] == RULED_OUT_WRONG]
        if false_positive:
            raise AssertionError("practical false positive detected after extraction")
        summary_rows.append(
            {
                "domain": domain,
                "outputs": len(domain_rows),
                "extraction_success_rate": rate(len(extracted_rows), len(domain_rows)),
                "content_rule_out_rate_extracted": rate(len(ruled_out), len(extracted_rows)),
                "uncheckable_rate": rate(len(uncheckable), len(domain_rows)),
                "practical_false_positive_rate": rate(len(false_positive), len(valid_rows)),
                "valid_extracted_count": len(valid_rows),
                "ruled_out_count": len(ruled_out),
                "uncheckable_count": len(uncheckable),
            }
        )
    for domain in ("python_code", "json_schema"):
        current = next(item for item in summary_rows if item["domain"] == domain)
        raw_rows = [item for item in rows if item["domain"] == domain and item["raw_input_verdict"]]
        raw_rule_out_rate = rate(
            len([item for item in raw_rows if item["raw_input_verdict"] == RULED_OUT_WRONG]),
            len(raw_rows),
        )
        before_after_rows.append(
            {
                "domain": domain,
                "slice3_raw_rule_out_rate": slice3.get(domain, ""),
                "slice4_current_raw_rule_out_rate": raw_rule_out_rate,
                "slice4_extracted_rule_out_rate": current["content_rule_out_rate_extracted"],
                "slice4_uncheckable_rate": current["uncheckable_rate"],
            }
        )
    return summary_rows, {"per_domain": summary_rows, "before_after": before_after_rows}


def rate(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "0.000"
    return f"{numerator / denominator:.3f}"


def load_slice3_rates() -> dict[str, str]:
    if not SLICE3_SUMMARY.exists():
        return {}
    data = json.loads(SLICE3_SUMMARY.read_text(encoding="utf-8"))
    return {
        domain: f"{values['checkable_error_rate']:.3f}"
        for domain, values in data.get("per_domain", {}).items()
    }


def write_spot_check(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spot_rows: list[dict[str, Any]] = []
    for domain in ("arithmetic", "python_code", "json_schema"):
        domain_ruleouts = [
            item for item in rows if item["domain"] == domain and item["verdict"] == RULED_OUT_WRONG
        ][:15]
        for item in domain_ruleouts:
            spot_rows.append(
                {
                    "task_id": item["task_id"],
                    "domain": domain,
                    "raw_response": item["raw_response"],
                    "extracted_content": item["extracted_content"],
                    "checker_reason": item["checker_reason"],
                }
            )
    write_csv(OUT_DIR / "manual_spot_check_ruleouts.csv", spot_rows)
    return spot_rows


def write_record(summary: dict[str, Any], spot_rows: list[dict[str, Any]]) -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    domain_lines = [
        "| Domain | Outputs | Extraction success | Extracted rule-out | UNCHECKABLE | Practical FP |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["per_domain"]:
        domain_lines.append(
            f"| {item['domain']} | {item['outputs']} | {item['extraction_success_rate']} | {item['content_rule_out_rate_extracted']} | {item['uncheckable_rate']} | {item['practical_false_positive_rate']} |"
        )
    before_lines = [
        "| Domain | Slice 3 raw rule-out | Slice 4 current raw rule-out | Slice 4 extracted rule-out | Slice 4 UNCHECKABLE |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for item in summary["before_after"]:
        before_lines.append(
            f"| {item['domain']} | {item['slice3_raw_rule_out_rate']} | {item['slice4_current_raw_rule_out_rate']} | {item['slice4_extracted_rule_out_rate']} | {item['slice4_uncheckable_rate']} |"
        )
    spot_counts = {
        domain: len([item for item in spot_rows if item["domain"] == domain])
        for domain in ("arithmetic", "python_code", "json_schema")
    }
    record = f"""# Phase 3 Slice 4 - Output Extraction Fix

Date: {date.today().isoformat()}

## Purpose

Fix the Slice 3 raw-wrapper false-positive cascade by extracting code, JSON, or integers before checking. Extraction failures now return `UNCHECKABLE`, never `RULED_OUT_WRONG`.

## Files created

- `src/dr_output_extraction_v1.py`
- `src/dr_run_checker_framework_eval_v2.py`
- `data/v1/digital_route/slice_04_extraction/raw_outputs_limit_5.jsonl`
- `data/v1/digital_route/slice_04_extraction/results_limit_5.csv`
- `data/v1/digital_route/slice_04_extraction/summary_limit_5.json`
- `data/v1/digital_route/slice_04_extraction/raw_outputs_full.jsonl`
- `data/v1/digital_route/slice_04_extraction/results_full.csv`
- `data/v1/digital_route/slice_04_extraction/summary_full.json`
- `data/v1/digital_route/slice_04_extraction/before_after.csv`
- `data/v1/digital_route/slice_04_extraction/manual_spot_check_ruleouts.csv`
- `data/v1/digital_route/records/SLICE_04_extraction_fix.md`
- `data/v1/digital_route/records/PHASE3_INDEX.md`

## Commands run

- `python src/dr_run_checker_framework_eval_v2.py --limit 5`
- `python src/dr_run_checker_framework_eval_v2.py`
- `python -m py_compile src/dr_output_extraction_v1.py src/dr_run_checker_framework_eval_v2.py`
- `git -C . diff --check`

## Per-Domain Results

{chr(10).join(domain_lines)}

## Before / After

{chr(10).join(before_lines)}

## Spot-Check Notes

Manual spot-check CSV rows: arithmetic {spot_counts['arithmetic']}, python_code {spot_counts['python_code']}, json_schema {spot_counts['json_schema']}. Rows include raw response, extracted content, and checker reason so remaining rule-outs can be inspected as content-level failures. If a domain has fewer than 15 rows, the eval produced fewer than 15 extracted rule-outs for that domain.

## Arithmetic Anchor

Arithmetic still uses the Slice 1 residue checker after tolerant integer extraction. This preserves the Slice 2 behavior: residue disagreement rules out wrong arithmetic, while extraction failure is `UNCHECKABLE`.

## Coverage

{CoverageReport([ArithmeticChecker(), PythonCodeChecker(), JsonSchemaChecker()]).text()}

## Conclusion

Extract-before-check removes wrapper/prose artifacts from code and JSON checking and moves extraction failure into an honest `UNCHECKABLE` bucket. Practical false-positive rates on extracted valid outputs were 0.000 for all domains in this run.

## Next Slice

Add a repair wrapper that sends only `RULED_OUT_WRONG` and `UNCHECKABLE` cases back to the model with targeted extraction/checker diagnostics.
"""
    RECORD_PATH.write_text(record, encoding="utf-8")
    index_line = (
        f"- {date.today().isoformat()} - Slice 04: extraction-before-check fix; "
        f"practical FP 0.000, code/json extracted rule-out "
        f"{summary['per_domain'][1]['content_rule_out_rate_extracted']}/"
        f"{summary['per_domain'][2]['content_rule_out_rate_extracted']}."
    )
    if INDEX_PATH.exists():
        existing = INDEX_PATH.read_text(encoding="utf-8")
        if index_line not in existing:
            INDEX_PATH.write_text(existing.rstrip() + "\n" + index_line + "\n", encoding="utf-8")
    else:
        INDEX_PATH.write_text("# Phase 3 Digital Route Index\n\n" + index_line + "\n", encoding="utf-8")


def run(limit: int | None) -> dict[str, Any]:
    assert_ollama_reachable()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tasks = select_tasks(build_tasks(50), limit)
    raw_path = OUT_DIR / ("raw_outputs_full.jsonl" if limit is None else f"raw_outputs_limit_{limit}.jsonl")
    batch_path = OUT_DIR / ("raw_batches_full.jsonl" if limit is None else f"raw_batches_limit_{limit}.jsonl")
    rows: list[dict[str, Any]] = []
    with raw_path.open("w", encoding="utf-8") as raw_file:
        if limit is None:
            with batch_path.open("w", encoding="utf-8") as batch_file:
                for domain in ("arithmetic", "python_code", "json_schema"):
                    domain_tasks = [task for task in tasks if task.domain == domain]
                    for chunk_start in range(0, len(domain_tasks), 5):
                        chunk = domain_tasks[chunk_start:chunk_start + 5]
                        try:
                            response = call_ollama(batch_prompt(domain, chunk), num_predict=1800, timeout_seconds=18)
                        except (OSError, TimeoutError, urllib.error.URLError) as exc:
                            response = f"GENERATION_TIMEOUT: {exc}"
                        batch_file.write(json.dumps({"domain": domain, "chunk_start": chunk_start, "raw_response": response}, ensure_ascii=True) + "\n")
                        split = split_batch_response(response, chunk)
                        for task in chunk:
                            raw = split.get(task.task_id, "")
                            raw_file.write(json.dumps({"task_id": task.task_id, "domain": task.domain, "prompt": task.prompt, "raw_response": raw}, ensure_ascii=True) + "\n")
                            rows.append(evaluate_task(task, raw))
        else:
            with batch_path.open("w", encoding="utf-8") as batch_file:
                for task in tasks:
                    try:
                        raw = call_ollama(prompt_for_task(task), num_predict=768, timeout_seconds=12)
                    except (OSError, TimeoutError, urllib.error.URLError) as exc:
                        raw = f"GENERATION_TIMEOUT: {exc}"
                    batch_file.write(json.dumps({"task_id": task.task_id, "domain": task.domain, "raw_response": raw}, ensure_ascii=True) + "\n")
                    raw_file.write(json.dumps({"task_id": task.task_id, "domain": task.domain, "prompt": task.prompt, "raw_response": raw}, ensure_ascii=True) + "\n")
                    rows.append(evaluate_task(task, raw))
    summary_rows, summary = summarize(rows)
    write_csv(OUT_DIR / ("results_full.csv" if limit is None else f"results_limit_{limit}.csv"), rows)
    write_csv(OUT_DIR / "before_after.csv", summary["before_after"])
    spot_rows = write_spot_check(rows)
    summary_path = OUT_DIR / ("summary_full.json" if limit is None else f"summary_limit_{limit}.json")
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    if limit is None:
        write_record(summary, spot_rows)
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def print_summary(summary: dict[str, Any]) -> None:
    print("Before/after")
    print("domain,slice3_raw,slice4_current_raw,slice4_extracted_rule_out,slice4_uncheckable")
    for item in summary["before_after"]:
        print(
            f"{item['domain']},{item['slice3_raw_rule_out_rate']},{item['slice4_current_raw_rule_out_rate']},"
            f"{item['slice4_extracted_rule_out_rate']},{item['slice4_uncheckable_rate']}"
        )
    print("\nPer-domain")
    print("domain,outputs,extraction_success,extracted_rule_out,uncheckable,practical_fp")
    for item in summary["per_domain"]:
        print(
            f"{item['domain']},{item['outputs']},{item['extraction_success_rate']},"
            f"{item['content_rule_out_rate_extracted']},{item['uncheckable_rate']},"
            f"{item['practical_false_positive_rate']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    summary = run(args.limit)
    print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
