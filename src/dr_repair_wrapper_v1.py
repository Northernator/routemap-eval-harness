"""Phase 3 Slice 6 repair wrapper."""

from __future__ import annotations

import json
import multiprocessing
import urllib.request
from pathlib import Path
from typing import Any


MODEL = "llama3.1"


def build_repair_prompt(flagged: dict[str, Any], round_index: int) -> str:
    domain = flagged["domain"]
    raw = str(flagged.get("raw_output", ""))
    extracted = str(flagged.get("extracted_content", ""))
    reason = str(flagged.get("checker_reason", ""))
    prompt = str(flagged.get("prompt", ""))
    if domain == "arithmetic":
        shown = extracted or raw
        return (
            f"Your answer {shown!r} fails an exact consistency check: {reason}. "
            f"Recompute this problem and respond with ONLY the integer.\nProblem: {prompt}"
        )
    if domain == "json_schema":
        if flagged.get("verdict") == "UNCHECKABLE":
            return (
                "Your previous response did not yield a checkable JSON object. "
                "Return ONLY a JSON object satisfying the schema: id string, score integer 0..100, "
                "status pass/fail, tags nonempty string array, no extra keys.\n"
                f"Task: {prompt}"
            )
        return (
            f"Your JSON violates the schema: {reason}. Return ONLY corrected JSON satisfying the schema. "
            "Schema: id string, score integer 0..100, status pass/fail, tags nonempty string array, no extra keys.\n"
            f"Task: {prompt}\nPrevious JSON: {extracted or raw}"
        )
    if flagged.get("verdict") == "UNCHECKABLE":
        return (
            "Your previous response did not yield checkable Python code. "
            f"Return ONLY corrected Python code, no explanation.\nTask: {prompt}"
        )
    return (
        f"Your code has a syntax error or parse failure: {reason}. "
        f"Return ONLY corrected Python code, no explanation.\nTask: {prompt}\nPrevious code: {extracted or raw}"
    )


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


def call_ollama(prompt: str, timeout_seconds: int = 60, num_predict: int = 96) -> str:
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
    return "" if queue.empty() else queue.get()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True) + "\n")


def repair_once(
    flagged: dict[str, Any],
    round_index: int,
    timeout_seconds: int = 60,
    retries: int = 2,
) -> dict[str, Any]:
    prompt = build_repair_prompt(flagged, round_index)
    raw_output = ""
    status = "generation_failed"
    error = ""
    for _attempt in range(1, retries + 2):
        try:
            raw_output = call_ollama(prompt, timeout_seconds=timeout_seconds, num_predict=96)
            status = "completed"
            error = ""
            break
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
    return {
        "task_id": flagged["task_id"],
        "domain": flagged["domain"],
        "round": round_index,
        "status": status,
        "prompt": prompt,
        "raw_output": raw_output,
        "generation_error": error,
    }
