"""Phase 3 Slice 5: resumable, token-capped corpus generation."""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


MODEL = "llama3.1"
DOMAINS = ("arithmetic", "python_code", "json_schema")


@dataclass(frozen=True)
class CorpusTask:
    task_id: str
    domain: str
    prompt: str
    expr_spec: dict[str, Any] | None = None
    true_answer: int | None = None
    schema: dict[str, Any] | None = None

    def as_cache_task(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "domain": self.domain,
            "prompt": self.prompt,
            "expr_spec": self.expr_spec,
            "true_answer": self.true_answer,
            "schema": self.schema,
        }


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


def build_tasks(n: int = 30) -> list[CorpusTask]:
    tasks: list[CorpusTask] = []
    schema = route_schema()
    for index in range(n):
        if index % 5 == 0:
            expr = {"family": "power", "base": 37 + index, "exponent": 12 + (index % 7)}
            prompt = f"Compute {(37 + index)}^{12 + (index % 7)} exactly."
        elif index % 5 == 1:
            expr = {"family": "factorial", "n": 20 + (index % 18)}
            prompt = f"Compute {(20 + (index % 18))}! exactly."
        elif index % 5 == 2:
            expr = {"family": "fibonacci", "n": 70 + index}
            prompt = f"Compute Fibonacci F({70 + index}) exactly, with F(0)=0 and F(1)=1."
        elif index % 5 == 3:
            values = [918_273 + index * 101, 837_465 + index * 103, 746_382 + index * 107, 665_544 + index * 109]
            expr = {"family": "bigsum", "values": values}
            prompt = "Compute this exact sum: " + " + ".join(str(value) for value in values) + "."
        else:
            values = [123 + index, 257 + index, 389 + index, 521 + index]
            expr = {"family": "bigprod", "values": values}
            prompt = "Compute this exact product: " + " x ".join(str(value) for value in values) + "."
        tasks.append(CorpusTask(f"arith_{index:03d}", "arithmetic", prompt, expr, exact_value(expr), None))

    for index in range(n):
        if index % 4 == 0:
            prompt = f"Write valid Python code for function f_{index}(a, b) returning a + b + {index}."
        elif index % 4 == 1:
            prompt = f"Write valid Python code for function f_{index}(items) returning list(reversed(items))."
        elif index % 4 == 2:
            prompt = f"Write valid Python code for class Box{index} with __init__(self, value) and get(self)."
        else:
            prompt = f"Write valid Python code for function f_{index}(text) returning text.split('->')."
        tasks.append(CorpusTask(f"code_{index:03d}", "python_code", prompt))

    for index in range(n):
        score = 104 if index % 5 == 0 else (-3 if index % 5 == 1 else 10 + (index % 70))
        status = "maybe" if index % 7 == 0 else ("pass" if index % 2 == 0 else "fail")
        tags = "empty tags list" if index % 6 == 0 else "tags route and audit"
        prompt = (
            f"Return a JSON object for id route-{index}, score {score}, status {status}, {tags}. "
            "Schema: id string; score integer 0..100; status pass/fail; tags nonempty array of strings; no extra keys."
        )
        tasks.append(CorpusTask(f"json_{index:03d}", "json_schema", prompt, schema=schema))
    return tasks


def prompt_for_task(task: CorpusTask) -> str:
    if task.domain == "arithmetic":
        target = "number"
    elif task.domain == "python_code":
        target = "Python code"
    else:
        target = "JSON"
    return f"Respond with ONLY the {target}, no explanation.\n{task.prompt}"


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


def call_ollama(prompt: str, timeout_seconds: int) -> str:
    queue: multiprocessing.Queue[str] = multiprocessing.Queue()
    process = multiprocessing.Process(target=_ollama_worker, args=(prompt, 256, timeout_seconds + 5, queue))
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join(2)
        raise TimeoutError(f"Ollama generation exceeded {timeout_seconds}s")
    if process.exitcode != 0:
        raise RuntimeError(f"Ollama worker exited with code {process.exitcode}")
    return "" if queue.empty() else queue.get()


def read_cache(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            rows[str(row["task_id"])] = row
    return rows


def append_cache_row(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def generate(args: argparse.Namespace) -> None:
    out_path = Path(args.out)
    selected_domains = set(DOMAINS if args.domain == "all" else [args.domain])
    tasks = [task for task in build_tasks(args.n) if task.domain in selected_domains]
    cached = read_cache(out_path)
    total_by_domain = {domain: len([task for task in tasks if task.domain == domain]) for domain in selected_domains}
    cached_by_domain = {
        domain: len([task for task in tasks if task.domain == domain and task.task_id in cached])
        for domain in selected_domains
    }
    print("Initial progress: " + ", ".join(f"{domain} {cached_by_domain[domain]}/{total_by_domain[domain]}" for domain in sorted(selected_domains)))
    for task in tasks:
        if task.task_id in cached:
            continue
        status = "generation_failed"
        raw_output = ""
        error = ""
        for attempt in range(1, args.retries + 2):
            try:
                raw_output = call_ollama(prompt_for_task(task), args.timeout)
                status = "completed"
                error = ""
                break
            except Exception as exc:  # keep resumable generation moving
                error = f"{type(exc).__name__}: {exc}"
        row = {
            **task.as_cache_task(),
            "model": MODEL,
            "status": status,
            "raw_output": raw_output,
            "generation_error": error,
        }
        append_cache_row(out_path, row)
        cached[task.task_id] = row
        done = len([item for item in tasks if item.domain == task.domain and item.task_id in cached])
        print(f"{task.domain}: {done}/{total_by_domain[task.domain]} cached ({task.task_id}: {status})")
    final_by_domain = {
        domain: len([task for task in tasks if task.domain == domain and task.task_id in cached])
        for domain in selected_domains
    }
    print("Final progress: " + ", ".join(f"{domain} {final_by_domain[domain]}/{total_by_domain[domain]}" for domain in sorted(selected_domains)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=("all",) + DOMAINS, default="all")
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--out", required=True)
    generate(parser.parse_args())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
