"""Cached local-Ollama role classifier for RouteMap role labels."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from llm_output_parsing import extract_json_object_from_text
from role_taxonomies import ALLOWED_FINE_ROLES


ROOT = Path(__file__).resolve().parents[1]
TRAIN_DEV_PATH = ROOT / "data/v1/gold/model_train_dev_role.csv"
TRUE_BLIND_PATH = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
OUT_DIR = ROOT / "data/v1/role_experiments/llm_role_classifier"
DEFAULT_OUTPUTS = OUT_DIR / "outputs"

MODEL = "llama3.1"
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
ROLES = list(ALLOWED_FINE_ROLES)

# Frozen train-derived few-shot examples from model_train_dev_role.csv seed_train rows only.
FEW_SHOTS = [
    {
        "segment_id": "DOC0002_S0004",
        "role": "DEFINE",
        "text": "Secure AI system development means designing, building, deploying, operating, and maintaining AI systems with explicit security responsibilities and mitigations at each stage.",
    },
    {
        "segment_id": "DOC0003_S0005",
        "role": "CLAIM",
        "text": "LLM security differs from ordinary web security because prompts, tool access, retrieval context, model outputs, and agent autonomy all become part of the attack surface.",
    },
    {
        "segment_id": "DOC0001_S0008",
        "role": "RESULT",
        "text": "A RouteMap annotation should classify NIST-style material as strong METHOD and GOVERNANCE content because the framework defines roles, lifecycle steps, controls, and limitations.",
    },
]

FROZEN_PROMPT = """Classify the passage's PRIMARY RouteMap role by the job it performs, not by its topic.

Allowed roles:
- BACKGROUND: source, document, project, policy, or dataset context that frames where information comes from or why it exists.
- CLAIM: substantive thesis, principle, or assertion about a system, risk, method, evidence, or governance practice.
- DEFINE: term or category explanation; names what something means, covers, denotes, or is called.
- METHOD: action, procedure, workflow, or implementation step to perform.
- RESULT: observed or reported outcome from evaluation, review, benchmark, test, inspection, or document output.
- LIMITATION: caveat, insufficiency, constraint, boundary, failure mode, or warning.
- NEXT_STEP: proposed future work, future evaluation, future dataset construction, or follow-up testing.
- EXAMPLE: concrete instance, scenario, case, or illustrative situation.

Hard boundaries:
- DEFINE names what a term/category means; CLAIM argues something about it.
- RESULT reports an observed/evaluated outcome; CLAIM states a thesis or principle.
- BACKGROUND gives source/project context; CLAIM gives a substantive assertion.

Return ONLY a JSON object exactly like {"role": "CLAIM"}.
"""


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def dataset_rows(dataset):
    if dataset == "train":
        return [row for row in read_rows(TRAIN_DEV_PATH) if row.get("split") == "seed_train"]
    if dataset == "dev":
        return [row for row in read_rows(TRAIN_DEV_PATH) if row.get("split") == "heldout_v1_dev"]
    if dataset == "true_blind":
        return read_rows(TRUE_BLIND_PATH)
    raise ValueError(f"unknown dataset: {dataset}")


def row_text(row):
    return row.get("text") or row.get("segment_text") or ""


def prompt_for(row):
    lines = [FROZEN_PROMPT.strip(), "", "Train-derived examples:"]
    for shot in FEW_SHOTS:
        lines.extend(
            [
                f"Passage: {shot['text']}",
                f"JSON: {json.dumps({'role': shot['role']})}",
                "",
            ]
        )
    lines.extend(
        [
            "Classify this passage.",
            f"Title: {row.get('title') or row.get('source_topic') or ''}",
            f"Passage: {row_text(row)}",
            "JSON:",
        ]
    )
    return "\n".join(lines)


def ollama_json(path, payload=None, timeout=120):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{OLLAMA_BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Ollama unreachable or invalid response at {OLLAMA_BASE_URL}: {exc}") from exc


def ensure_ollama():
    tags = ollama_json("/api/tags", None, timeout=10)
    names = {model.get("name", "").split(":")[0] for model in tags.get("models", [])}
    full_names = {model.get("name", "") for model in tags.get("models", [])}
    if MODEL not in names and MODEL not in full_names:
        raise SystemExit(f"Ollama reachable, but model {MODEL!r} is not listed. Run: ollama pull {MODEL}")
    return True


def call_ollama(prompt):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0},
    }
    response = ollama_json("/api/generate", payload, timeout=180)
    return response.get("response", "")


def normalize_role(value):
    role = str(value or "").strip().upper()
    role = role.replace("-", "_").replace(" ", "_")
    return role if role in ROLES else ""


def parse_role(raw_response):
    parsed, error = extract_json_object_from_text(raw_response)
    if parsed is None:
        return "", True, "", error or "parse_failed"
    role = normalize_role(parsed.get("role", ""))
    if not role:
        return "", False, str(parsed.get("role", "")), "invalid_label"
    return role, False, "", ""


def read_cache(path):
    cached = {}
    path = Path(path)
    if not path.exists():
        return cached
    with path.open("r", encoding="utf-8-sig") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            segment_id = row.get("segment_id", "")
            if segment_id:
                cached[segment_id] = row
    return cached


def append_jsonl(path, row):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("a", encoding="utf-8") as target:
        target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def output_row(dataset, row, raw_response):
    pred_role, parse_failed, invalid_label, parse_error = parse_role(raw_response)
    return {
        "segment_id": row.get("segment_id", ""),
        "dataset": dataset,
        "model": MODEL,
        "raw_response": raw_response,
        "pred_role": pred_role,
        "parse_failed": parse_failed,
        "invalid_label": invalid_label,
        "parse_error": parse_error,
    }


def run(args):
    rows = dataset_rows(args.dataset)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]
    if not args.execute:
        for row in rows[: max(1, args.limit or 3)]:
            print(f"segment_id={row.get('segment_id', '')}")
            print(prompt_for(row))
            print("---")
        return

    ensure_ollama()
    cached = read_cache(args.out)
    requested = len(rows)
    completed = 0
    skipped = 0
    for row in rows:
        segment_id = row.get("segment_id", "")
        if segment_id in cached:
            skipped += 1
            continue
        raw_response = call_ollama(prompt_for(row))
        result = output_row(args.dataset, row, raw_response)
        append_jsonl(args.out, result)
        cached[segment_id] = result
        completed += 1
        print(
            f"{args.dataset} {segment_id} pred={result['pred_role'] or 'EMPTY'} "
            f"parse_failed={result['parse_failed']} invalid={bool(result['invalid_label'])}"
        )
        sys.stdout.flush()
    print(f"done dataset={args.dataset} requested={requested} completed={completed} skipped={skipped} out={args.out}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["train", "dev", "true_blind"], required=True)
    parser.add_argument("--limit", type=int, default=0, help="0 means all rows")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(args)


if __name__ == "__main__":
    main()
