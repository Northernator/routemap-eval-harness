import argparse
import json
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


def parse_json(raw_output):
    try:
        data = json.loads(raw_output)
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


def call_provider(provider, prompt, row, model):
    if provider == "stub":
        return json.dumps(stub_label(row))
    if provider == "openai":
        raise NotImplementedError("OpenAI provider call is not wired yet.")
    if provider == "anthropic":
        raise NotImplementedError("Anthropic provider call is not wired yet.")
    if provider == "ollama":
        raise NotImplementedError("Ollama provider call is not wired yet.")
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
    args = ap.parse_args()

    schema = load_schema(args.schema)
    segments = pd.read_csv(args.segments, keep_default_na=False)
    template = Path(args.prompt).read_text(encoding="utf-8")
    rows = []
    errors = []

    for _, row in segments.iterrows():
        prompt = template.replace("{{PASSAGE}}", str(row.get("text", "")))
        try:
            raw_output = call_provider(args.provider, prompt, row, args.model)
        except NotImplementedError as exc:
            raise SystemExit(f"{args.provider} provider selected, but no provider call is configured yet: {exc}") from exc

        data, parse_errors = parse_json(raw_output)
        label_errors = parse_errors if parse_errors else validate_label(data, schema)
        if label_errors:
            errors.append({
                "segment_id": row.get("segment_id", ""),
                "provider": args.provider,
                "model": args.model,
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
            "llm_model": args.model,
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
