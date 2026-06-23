import argparse
import csv
from pathlib import Path


COLUMNS = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "notes",
]

NEGATED_PATTERNS = [
    "cannot",
    "does not",
    "not replace",
    "not a complete",
    "not sufficient",
    "absent",
    "stale",
    "too broad",
]

LIMITED_PATTERNS = [
    "overstate",
    "difficult",
    "hide retrieval weaknesses",
    "leave uncertainty",
    "can lose detail",
]

ENTITY_PATTERNS = [
    ("ai principles", "AI principles"),
    ("trustworthy ai", "trustworthy AI"),
    ("model release review", "model release review"),
    ("release evidence", "release evidence"),
    ("llm application security", "LLM application security"),
    ("route-extraction", "route extraction"),
    ("route extraction", "route extraction"),
    ("routemap", "RouteMap"),
    ("route provenance", "route provenance"),
    ("retrieval trace", "retrieval trace"),
    ("answer support", "answer support"),
    ("ai risk posture", "AI risk management"),
    ("ai risk", "AI risk management"),
    ("risk management", "risk management"),
    ("secure ai", "secure AI development"),
    ("secure model", "secure AI development"),
    ("prompt injection", "prompt injection"),
    ("data protection", "data protection"),
    ("privacy", "privacy"),
    ("consent", "permission boundary"),
    ("eu ai act", "EU AI Act"),
    ("high-risk", "high-risk AI"),
    ("risk management system", "risk management system"),
    ("agent memory", "agent memory"),
    ("long-context memory", "long-context memory"),
    ("long-context", "long-context memory"),
    ("permission check", "permission boundary"),
    ("permission", "permission boundary"),
    ("incident response", "incident response"),
    ("monitoring", "monitoring"),
    ("governance", "governance"),
    ("evaluation scripts", "evaluation scripts"),
    ("mismatch review", "mismatch review"),
    ("gold labels", "gold labels"),
    ("benchmark", "benchmark"),
    ("retrieval", "retrieval"),
    ("model behavior", "model behavior"),
    ("controls", "controls"),
    ("audit", "audit"),
    ("human", "human review"),
    ("reviewer", "human review"),
    ("source", "source context"),
    ("documentation", "documentation"),
]

TITLE_ENTITIES = [
    ("privacy", "privacy"),
    ("security", "LLM application security"),
    ("roadmap", "AI roadmap"),
    ("benchmark", "benchmark"),
    ("memory", "agent memory"),
    ("retrieval", "retrieval"),
    ("eval", "evaluation"),
]


def contains_any(text, patterns):
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def infer_operative_status(role, text):
    if role in {"BACKGROUND", "DEFINE", "EXAMPLE", "RESULT"}:
        return "DESCRIPTIVE"
    if role in {"NEXT_STEP", "METHOD"}:
        return "ACTIVE"
    if role == "LIMITATION":
        if contains_any(text, NEGATED_PATTERNS):
            return "NEGATED"
        return "LIMITED"
    if role == "CLAIM":
        if contains_any(text, NEGATED_PATTERNS):
            return "NEGATED"
        return "ACTIVE"
    return "DESCRIPTIVE"


def infer_relation(role, text):
    lowered = text.lower()
    if role == "BACKGROUND":
        return "sets_context"
    if role == "DEFINE":
        return "defines"
    if role == "CLAIM":
        return "asserts"
    if role == "METHOD":
        if "map" in lowered or "trace" in lowered or "route" in lowered:
            return "maps_to"
        if "should" in lowered or "reviewer" in lowered or "operators" in lowered:
            return "recommends"
        return "recommends"
    if role == "RESULT":
        if "retrieval" in lowered or "recovered" in lowered or "higher recall" in lowered:
            return "supports_retrieval"
        return "reports_usefulness"
    if role == "LIMITATION":
        if contains_any(text, NEGATED_PATTERNS):
            return "limits"
        return "warns_about"
    if role == "NEXT_STEP":
        return "proposes_next_test"
    if role == "EXAMPLE":
        return "gives_example"
    return "asserts"


def infer_answer_relevant(role, notes):
    if role == "BACKGROUND":
        return "NO" if "context" in notes.lower() else "MAYBE"
    return "YES"


def extract_entities(text, title):
    haystack = f"{title} {text}".lower()
    entities = []
    seen = set()
    for pattern, entity in ENTITY_PATTERNS + TITLE_ENTITIES:
        if pattern in haystack and entity not in seen:
            entities.append(entity)
            seen.add(entity)
    if not entities:
        entities.append("RouteMap segment")
    return "; ".join(entities[:5])


def build_gold(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)

    output_rows = []
    for row in rows:
        role = (row.get("gold_role") or "").strip()
        text = row.get("text", "")
        title = row.get("title", "")
        notes = row.get("notes", "")
        output_rows.append({
            "segment_id": row.get("segment_id", ""),
            "title": title,
            "text": text,
            "gold_role": role,
            "gold_entities": extract_entities(text, title),
            "gold_operative_status": infer_operative_status(role, text),
            "gold_relation": infer_relation(role, text),
            "gold_answer_relevant": infer_answer_relevant(role, notes),
            "notes": notes,
        })

    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(output_rows)

    return len(output_rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_csv", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    row_count = build_gold(args.input_csv, args.out)
    print(f"Wrote {row_count} rows to {args.out}")


if __name__ == "__main__":
    main()
