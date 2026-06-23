import argparse
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from routemap_extraction_contract import normalize_extraction, validate_extraction


PROVIDERS = {"manual_copy", "ollama_http", "openai_http", "anthropic_http", "custom_command"}


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8-sig") as source:
        for line in source:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def request_json(url, payload, headers=None, timeout=120):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers or {}, method="POST")
    request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def extraction_or_raw(segment_id, provider, model, content):
    try:
        obj = json.loads(content)
        normalized = normalize_extraction(obj)
        valid, _ = validate_extraction(normalized)
        if valid:
            return {"segment_id": segment_id, "provider": provider, "model": model, "extraction": normalized}
    except (json.JSONDecodeError, TypeError):
        pass
    return {"segment_id": segment_id, "provider": provider, "model": model, "raw_response": str(content)}


def call_ollama(prompt, model):
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    response = request_json(f"{host}/api/generate", {"model": model, "prompt": prompt, "stream": False})
    return response.get("response", json.dumps(response))


def call_openai(prompt, model):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    response = request_json(
        "https://api.openai.com/v1/chat/completions",
        {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0},
        {"Authorization": f"Bearer {api_key}"},
    )
    return response["choices"][0]["message"]["content"]


def call_anthropic(prompt, model):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    response = request_json(
        "https://api.anthropic.com/v1/messages",
        {"model": model, "max_tokens": 1000, "messages": [{"role": "user", "content": prompt}]},
        {"x-api-key": api_key, "anthropic-version": "2023-06-01"},
    )
    parts = response.get("content", [])
    return "\n".join(part.get("text", "") for part in parts if part.get("type") == "text")


def call_custom(prompt, command):
    completed = subprocess.run(command, input=prompt, text=True, capture_output=True, shell=True, timeout=180)
    if completed.returncode != 0:
        return json.dumps({"error": completed.stderr.strip(), "stdout": completed.stdout.strip()})
    return completed.stdout.strip()


def dry_run(args, rows):
    print("DRY RUN: no provider calls will be made")
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model or ''}")
    print(f"Requests: {args.requests}")
    print(f"Output: {args.out}")
    print(f"Rows selected: {len(rows)}")
    if args.provider == "manual_copy" and rows:
        print("First prompt preview:")
        print(rows[0].get("prompt", "")[:1000])
    elif args.provider == "ollama_http":
        print(f"Would POST to {(os.environ.get('OLLAMA_HOST') or 'http://localhost:11434').rstrip('/')}/api/generate")
    elif args.provider == "openai_http":
        print("Would POST to https://api.openai.com/v1/chat/completions using OPENAI_API_KEY")
    elif args.provider == "anthropic_http":
        print("Would POST to https://api.anthropic.com/v1/messages using ANTHROPIC_API_KEY")
    elif args.provider == "custom_command":
        print(f"Would run command: {args.command}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    parser.add_argument("--model", default="")
    parser.add_argument("--command", default="")
    parser.add_argument("--requests", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.requests)
    if args.limit:
        rows = rows[: args.limit]
    if args.dry_run or not args.execute:
        dry_run(args, rows)
        if not args.execute:
            print("Pass --execute to make live calls.")
        return

    if args.provider == "manual_copy":
        raise SystemExit("manual_copy is preview-only; save manual outputs directly as JSONL.")
    if args.provider in {"ollama_http", "openai_http", "anthropic_http"} and not args.model:
        raise SystemExit("--model is required for HTTP providers")
    if args.provider == "custom_command" and not args.command:
        raise SystemExit("--command is required for custom_command")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with out_path.open("w", encoding="utf-8", newline="\n") as target:
        for row in rows:
            segment_id = row["segment_id"]
            prompt = row["prompt"]
            try:
                if args.provider == "ollama_http":
                    content = call_ollama(prompt, args.model)
                    record = {"segment_id": segment_id, "provider": args.provider, "model": args.model, "raw_response": content}
                elif args.provider == "openai_http":
                    content = call_openai(prompt, args.model)
                    record = extraction_or_raw(segment_id, args.provider, args.model or args.command, content)
                elif args.provider == "anthropic_http":
                    content = call_anthropic(prompt, args.model)
                    record = extraction_or_raw(segment_id, args.provider, args.model or args.command, content)
                else:
                    content = call_custom(prompt, args.command)
                    record = extraction_or_raw(segment_id, args.provider, args.model or args.command, content)
            except (RuntimeError, urllib.error.URLError, TimeoutError, subprocess.SubprocessError) as exc:
                record = {
                    "segment_id": segment_id,
                    "provider": args.provider,
                    "model": args.model or args.command,
                    "provider_error": True,
                    "error": str(exc),
                    "raw_response": "",
                }
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
            if args.sleep_seconds:
                time.sleep(args.sleep_seconds)
    print(f"Provider: {args.provider}")
    print(f"Rows written: {written}")
    print(f"Output: {out_path}")


if __name__ == "__main__":
    main()
