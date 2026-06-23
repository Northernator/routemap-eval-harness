import csv
import re
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import extract_entities_ontology_v1


INPUT_PATH = Path("data/v1/gold/heldout_full_extraction_pred_boundary_augmented_role_fresh.csv")
OUT_PATH = Path("data/v1/gold/heldout_full_extraction_pred_combined_v3_fresh.csv")

RELATION_BY_ROLE = {
    "BACKGROUND": "sets_context",
    "DEFINE": "defines",
    "CLAIM": "asserts",
    "METHOD": "recommends",
    "RESULT": "reports_usefulness",
    "LIMITATION": "limits",
    "NEXT_STEP": "proposes_next_test",
    "EXAMPLE": "gives_example",
}

DESCRIPTIVE_ROLES = {"BACKGROUND", "DEFINE", "RESULT", "EXAMPLE"}
ACTIVE_ROLES = {"METHOD", "NEXT_STEP"}
NEGATION_RE = re.compile(r"\b(cannot|can't|does not|do not|insufficient|not enough|not complete|fails?|failure|unable)\b")
SOURCE_METADATA_RE = re.compile(
    r"\b(source|package|project|readme|appendix|overview|briefing|handbook|catalog|playbook|documentation page|metadata)\b"
)


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def operative_status(role, text):
    lowered = (text or "").lower()
    if role in DESCRIPTIVE_ROLES:
        return "DESCRIPTIVE"
    if role in ACTIVE_ROLES:
        return "ACTIVE"
    if role == "LIMITATION":
        return "NEGATED" if NEGATION_RE.search(lowered) else "LIMITED"
    if role == "CLAIM":
        return "NEGATED" if NEGATION_RE.search(lowered) else "ACTIVE"
    return ""


def answer_relevant(role, text, title):
    if role != "BACKGROUND":
        return "YES"
    haystack = f"{title or ''} {text or ''}".lower()
    return "NO" if SOURCE_METADATA_RE.search(haystack) else "MAYBE"


def main():
    rows = read_rows(INPUT_PATH)
    if not rows:
        raise ValueError(f"No rows found in {INPUT_PATH}")

    new_columns = [
        "pred_role_combined_v3",
        "pred_entities_combined_v3",
        "pred_operative_status_combined_v3",
        "pred_relation_combined_v3",
        "pred_answer_relevant_combined_v3",
    ]
    fieldnames = list(rows[0].keys())
    for column in new_columns:
        if column not in fieldnames:
            fieldnames.append(column)

    role_counts = Counter()
    output_rows = []
    for row in rows:
        role = row.get("pred_role_boundary_augmented", "")
        text = row.get("text", "")
        title = row.get("title", "")
        output = dict(row)
        output["pred_role_combined_v3"] = role
        output["pred_entities_combined_v3"] = extract_entities_ontology_v1(text, title)
        output["pred_operative_status_combined_v3"] = operative_status(role, text)
        output["pred_relation_combined_v3"] = RELATION_BY_ROLE.get(role, "")
        output["pred_answer_relevant_combined_v3"] = answer_relevant(role, text, title)
        output_rows.append(output)
        role_counts[role or "(blank)"] += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Rows written: {len(output_rows)}")
    print(f"Output: {OUT_PATH}")
    print("Combined role counts:")
    for role, count in role_counts.most_common():
        print(f"{role}: {count}")


if __name__ == "__main__":
    main()
