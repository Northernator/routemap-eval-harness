import argparse
import csv
from pathlib import Path

from entity_extractor_v2 import extract_entities_v2
from role_classifier_v4 import classify_role_v4


PRED_COLUMNS = [
    "pred_role",
    "pred_entities",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
]

STRONG_NEGATION_PATTERNS = [
    "cannot",
    "does not",
    "do not",
    "not sufficient",
    "not a complete",
    "not complete",
    "not enough",
    "not a substitute",
    "may be absent",
    "too broad to justify",
]

BACKGROUND_METADATA_PATTERNS = [
    "source note",
    "source notes",
    "source summarizes",
    "policy context",
    "document-level context",
    "document provides background",
    "white paper describes the setting",
    "benchmark package contains",
    "project readme records",
    "briefing introduces",
    "guidance explains",
    "project hub",
    "regulatory setting",
]

RELATION_BY_ROLE = {
    "BACKGROUND": "sets_context",
    "DEFINE": "defines",
    "CLAIM": "asserts",
    "METHOD": "recommends",
    "RESULT": "reports_usefulness",
    "NEXT_STEP": "proposes_next_test",
    "EXAMPLE": "gives_example",
}


def _contains_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def _clean(text: str) -> str:
    return "" if text is None else str(text).strip()


def infer_relation_v2(role: str, text: str) -> str:
    if role == "LIMITATION":
        return "limits" if _contains_any(text, STRONG_NEGATION_PATTERNS) else "warns_about"
    return RELATION_BY_ROLE.get(role, "asserts")


def infer_operative_status_v2(role: str, text: str) -> str:
    if role in {"BACKGROUND", "DEFINE", "RESULT", "EXAMPLE"}:
        return "DESCRIPTIVE"
    if role in {"METHOD", "NEXT_STEP"}:
        return "ACTIVE"
    if role == "LIMITATION":
        return "NEGATED" if _contains_any(text, STRONG_NEGATION_PATTERNS) else "LIMITED"
    if role == "CLAIM":
        return "NEGATED" if _contains_any(text, STRONG_NEGATION_PATTERNS) else "ACTIVE"
    return "DESCRIPTIVE"


def infer_answer_relevant_v2(role: str, text: str, title: str = "") -> str:
    if role != "BACKGROUND":
        return "YES"
    haystack = f"{_clean(title)} {_clean(text)}"
    return "NO" if _contains_any(haystack, BACKGROUND_METADATA_PATTERNS) else "MAYBE"


def predict(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for column in PRED_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)

    for row in rows:
        text = row.get("text", "")
        title = row.get("title", "")
        pred_role = classify_role_v4(text, title)
        row["pred_role"] = pred_role
        row["pred_entities"] = extract_entities_v2(text, title)
        row["pred_operative_status"] = infer_operative_status_v2(pred_role, text)
        row["pred_relation"] = infer_relation_v2(pred_role, text)
        row["pred_answer_relevant"] = infer_answer_relevant_v2(pred_role, text, title)

    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_csv", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    row_count = predict(args.input_csv, args.out)
    print(f"Wrote {row_count} rows to {args.out}")


if __name__ == "__main__":
    main()
