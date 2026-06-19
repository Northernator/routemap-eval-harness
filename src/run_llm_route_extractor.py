import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
import pandas as pd


REQUIRED_FIELDS = [
    "role",
    "entities",
    "operative_status",
    "relation",
    "confidence",
    "rationale",
]

ERROR_COLUMNS = ["segment_id", "provider", "model", "errors", "raw_output"]

DEFAULT_MODELS = {
    "stub": "stub",
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-3-5-haiku-latest",
    "ollama": "llama3.1",
}


def project_root():
    return Path(__file__).resolve().parents[1]


def load_schema(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def value(row, column, default=""):
    if column not in row:
        return default
    item = row[column]
    if pd.isna(item):
        return default
    return str(item).strip()


def split_entities(raw):
    return [part.strip() for part in str(raw).split("|") if part.strip()]


def stub_label(row):
    role = value(row, "gold_role", "BACKGROUND") or "BACKGROUND"
    status = value(row, "gold_operative_status", "UNKNOWN") or "UNKNOWN"
    relation = value(row, "gold_relation", "background_to") or "background_to"
    entities = split_entities(value(row, "gold_entities"))
    copied = any(value(row, column) for column in ["gold_role", "gold_operative_status", "gold_relation", "gold_entities"])
    return {
        "role": role,
        "entities": entities,
        "operative_status": status,
        "relation": relation,
        "confidence": 1.0 if copied else 0.25,
        "rationale": "Stub provider copied available gold labels." if copied else "Stub provider used fallback labels.",
    }


def default_model(provider, model):
    return model or DEFAULT_MODELS[provider]


def extract_json_object(raw_output):
    text = str(raw_output).strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    if text.startswith("{") and text.endswith("}"):
        return text

    start = text.find("{")
    if start == -1:
        return text

    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(text[start:], start):
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return text


def parse_json(raw_output):
    candidate = extract_json_object(raw_output)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return None, ["JSON output must be an object"]
    return data, []


def validate_label(data, schema):
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in data:
            errors.append(f"missing field: {field}")

    if errors:
        return errors

    if data["role"] not in set(schema["roles"]):
        errors.append(f"invalid role: {data['role']}")
    if data["operative_status"] not in set(schema["operative_status"]):
        errors.append(f"invalid operative_status: {data['operative_status']}")
    if data["relation"] not in set(schema["relations"]):
        errors.append(f"invalid relation: {data['relation']}")
    if not isinstance(data["entities"], list) or not all(isinstance(item, str) for item in data["entities"]):
        errors.append("entities must be a list of strings")
    if not isinstance(data["rationale"], str):
        errors.append("rationale must be a string")
    if not isinstance(data["confidence"], (int, float)) or not 0 <= float(data["confidence"]) <= 1:
        errors.append("confidence must be a number between 0 and 1")
    return errors


def request_json(url, payload, headers):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc


def call_openai(prompt, model):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    response = request_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return only strict JSON matching the requested schema."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    return response["choices"][0]["message"]["content"]


def call_anthropic(prompt, model):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    response = request_json(
        "https://api.anthropic.com/v1/messages",
        {
            "model": model,
            "max_tokens": 800,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        },
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    return "\n".join(block.get("text", "") for block in response.get("content", []) if block.get("type") == "text")


def call_ollama(prompt, model):
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
        {"Content-Type": "application/json"},
    )
    return response.get("response", "")


def call_provider(provider, prompt, row, model):
    if provider == "stub":
        return json.dumps(stub_label(row))
    if provider == "openai":
        return call_openai(prompt, model)
    if provider == "anthropic":
        return call_anthropic(prompt, model)
    if provider == "ollama":
        return call_ollama(prompt, model)
    raise ValueError(f"Unknown provider: {provider}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True)
    ap.add_argument("--out", default="data/outputs/llm_route_labels.csv")
    ap.add_argument("--provider", choices=["stub", "openai", "anthropic", "ollama"], default="stub")
    ap.add_argument("--model", default="")
    ap.add_argument("--prompt", default="prompts/llm_route_extractor_prompt.md")
    ap.add_argument("--schema", default=str(project_root() / "configs" / "route_schema.json"))
    ap.add_argument("--errors-out", default="data/outputs/llm_route_errors.csv")
    ap.add_argument("--limit", type=int, default=0, help="Process only the first N segments when N > 0")
    ap.add_argument("--sleep-seconds", type=float, default=0.0, help="Sleep between non-stub provider calls")
    ap.add_argument("--dry-run", action="store_true", help="Print prompts without calling the selected provider")
    args = ap.parse_args()

    schema = load_schema(args.schema)
    segments = pd.read_csv(args.segments, keep_default_na=False)
    if args.limit > 0:
        segments = segments.head(args.limit)
    template = Path(args.prompt).read_text(encoding="utf-8")
    selected_model = default_model(args.provider, args.model)
    rows = []
    errors = []

    for _, row in segments.iterrows():
        prompt = template.replace("{{PASSAGE}}", str(row.get("text", "")))
        if args.dry_run:
            print(f"\n--- prompt for {row.get('segment_id', '')} ({args.provider}/{selected_model}) ---")
            print(prompt)
            raw_output = json.dumps(stub_label(row))
        else:
            try:
                raw_output = call_provider(args.provider, prompt, row, selected_model)
            except Exception as exc:
                raw_output = ""
                errors.append({
                    "segment_id": row.get("segment_id", ""),
                    "provider": args.provider,
                    "model": selected_model,
                    "errors": f"provider call failed: {exc}",
                    "raw_output": raw_output,
                })
            if args.sleep_seconds > 0 and args.provider != "stub":
                time.sleep(args.sleep_seconds)

        data, parse_errors = parse_json(raw_output)
        label_errors = parse_errors if parse_errors else validate_label(data, schema)
        if label_errors:
            errors.append({
                "segment_id": row.get("segment_id", ""),
                "provider": args.provider,
                "model": selected_model,
                "errors": " | ".join(label_errors),
                "raw_output": raw_output,
            })
            data = data or {
                "role": "",
                "entities": [],
                "operative_status": "",
                "relation": "",
                "confidence": 0.0,
                "rationale": "",
            }

        rows.append({**row.to_dict(), **{
            "llm_provider": args.provider,
            "llm_model": selected_model,
            "llm_role": data.get("role", ""),
            "llm_entities": "|".join(data.get("entities", [])) if isinstance(data.get("entities", []), list) else "",
            "llm_operative_status": data.get("operative_status", ""),
            "llm_relation": data.get("relation", ""),
            "llm_confidence": data.get("confidence", 0.0),
            "llm_rationale": data.get("rationale", ""),
            "llm_valid": len(label_errors) == 0,
        }})

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.errors_out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    pd.DataFrame(errors, columns=ERROR_COLUMNS).to_csv(args.errors_out, index=False)
    print(f"Wrote {len(rows)} labels to {args.out}")
    print(f"Wrote {len(errors)} validation errors to {args.errors_out}")


if __name__ == "__main__":
    main()
