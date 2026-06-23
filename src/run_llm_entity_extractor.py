"""Local-Ollama entity extraction cache for llm_entity_extractor_eval."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from llm_output_parsing import extract_json_object_from_text


ROOT = Path(__file__).resolve().parents[1]
MODEL = "llama3.1"
DEV_PATH = ROOT / "data/v1/gold/heldout_full_extraction_pred_v2.csv"
TRUE_BLIND_PATH = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
TRAIN_DEV_PATH = ROOT / "data/v1/gold/model_train_dev_role.csv"

# Frozen prompt. Few-shot examples are train-derived from model_train_dev_role.csv seed_train rows.
FROZEN_PROMPT = """You extract RouteMap entity mentions.

Return ONLY a JSON array of short verbatim noun phrases explicitly named in the passage.
Entities may be systems, roles, artifacts, datasets, policies, processes, tools, objects, or named concepts.
Prefer specific surface phrases a human annotator would tag. Do not return broad themes unless the passage explicitly names them.
Do not explain. Do not add commentary.

Example 1 passage:
Secure AI system development means designing, building, deploying, operating, and maintaining AI systems so they remain secure.
Example 1 entities:
["Secure AI system development", "AI systems"]

Example 2 passage:
The NCSC secure AI development guidance asks teams to document model capabilities, data provenance, and deployment risks before release.
Example 2 entities:
["NCSC secure AI development guidance", "model capabilities", "data provenance", "deployment risks"]

Passage:
{text}
"""

PROMPT_SHA256 = hashlib.sha256(FROZEN_PROMPT.encode("utf-8")).hexdigest()


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def dataset_rows(dataset):
    if dataset == "dev":
        return read_rows(DEV_PATH)
    if dataset == "true_blind":
        return read_rows(TRUE_BLIND_PATH)
    if dataset == "train_sample":
        rows = [row for row in read_rows(TRAIN_DEV_PATH) if "train" in row.get("split", "").lower()]
        return rows[:10]
    raise ValueError(f"unknown dataset: {dataset}")


def row_text(row):
    return row.get("text") or row.get("segment_text") or ""


def build_prompt(text):
    return FROZEN_PROMPT.format(text=text)


def request_json(url, payload, timeout=180):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama unreachable at {url}: {exc}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Ollama timed out at {url}: {exc}") from exc


def call_ollama(prompt, model=MODEL):
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    response = request_json(
        f"{base_url}/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        },
    )
    return response.get("response", "")


def strip_code_fences(text):
    value = "" if text is None else str(text).strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", value, flags=re.IGNORECASE | re.DOTALL)
    return fence.group(1).strip() if fence else value


def balanced_json_array(text):
    value = strip_code_fences(text)
    start = value.find("[")
    while start != -1:
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(value)):
            char = value[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
                if depth == 0:
                    candidate = value[start : index + 1]
                    try:
                        parsed = json.loads(candidate)
                        if isinstance(parsed, list):
                            return parsed, None
                    except json.JSONDecodeError as exc:
                        return None, str(exc)
        start = value.find("[", start + 1)
    return None, "no parseable JSON array found"


def parse_entities(raw_response):
    parsed, error = balanced_json_array(raw_response)
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()], None
    obj, obj_error = extract_json_object_from_text(raw_response)
    if obj and isinstance(obj.get("entities"), list):
        return [str(item).strip() for item in obj["entities"] if str(item).strip()], None
    return [], error or obj_error or "no entities array found"


def read_cache(path):
    if not Path(path).exists():
        return {}
    cache = {}
    with Path(path).open("r", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            cache[row.get("segment_id", "")] = row
    return cache


def append_jsonl(path, row):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as target:
        target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run(dataset, limit, execute, out_path):
    rows = dataset_rows(dataset)
    if limit and limit > 0:
        rows = rows[:limit]
    cache = read_cache(out_path)
    if not execute:
        for row in rows[: min(len(rows), 3)]:
            print(f"DRY RUN segment_id={row.get('segment_id', '')}")
            print(build_prompt(row_text(row))[:1200])
            print()
        print("Dry run only. Re-run with --execute to call local Ollama.")
        return {"rows": len(rows), "called": 0, "cached": 0, "parse_failed": 0}
    called = 0
    cached = 0
    parse_failed = 0
    for row in rows:
        segment_id = row.get("segment_id", "")
        if segment_id in cache:
            cached += 1
            parse_failed += int(bool(cache[segment_id].get("parse_failed")))
            continue
        prompt = build_prompt(row_text(row))
        raw_response = call_ollama(prompt)
        entities, error = parse_entities(raw_response)
        failed = bool(error)
        parse_failed += int(failed)
        called += 1
        append_jsonl(
            out_path,
            {
                "segment_id": segment_id,
                "dataset": dataset,
                "model": MODEL,
                "prompt_sha256": PROMPT_SHA256,
                "raw_response": raw_response,
                "parsed_entities": entities,
                "parse_failed": failed,
                "parse_error": error or "",
            },
        )
    return {"rows": len(rows), "called": called, "cached": cached, "parse_failed": parse_failed}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["dev", "true_blind", "train_sample"], required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result = run(args.dataset, args.limit, args.execute, Path(args.out))
    print("llm_entity_extractor_eval")
    print(f"dataset={args.dataset}")
    print(f"model={MODEL}")
    print(f"prompt_sha256={PROMPT_SHA256}")
    print(f"rows={result['rows']} called={result['called']} cached={result['cached']} parse_failed={result['parse_failed']}")
    print(f"out={args.out}")


if __name__ == "__main__":
    main()
