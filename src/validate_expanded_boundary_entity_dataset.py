import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from routemap_extraction_contract import ALLOWED_ANSWER_RELEVANCE, ALLOWED_RELATIONS, ALLOWED_ROLES, ALLOWED_STATUSES


REQUIRED = [
    "segment_id",
    "dataset_family",
    "boundary_pair",
    "title",
    "text",
    "gold_role",
    "contrast_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "difficulty",
    "notes",
]
FORBIDDEN = ["### CLAIM", "### DEFINE", "### METHOD", "### RESULT", "### LIMITATION", "### NEXT_STEP", "### EXAMPLE", "### BACKGROUND"]
BOUNDARY_PAIRS = [
    "CLAIM vs DEFINE",
    "RESULT vs CLAIM",
    "BACKGROUND vs CLAIM",
    "BACKGROUND vs EXAMPLE",
    "BACKGROUND vs RESULT",
    "METHOD vs EXAMPLE",
    "RESULT vs METHOD",
    "CLAIM vs METHOD",
]


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    rows = read_rows(args.csv)
    errors = []
    if len(rows) != 560:
        errors.append(f"expected 560 rows, found {len(rows)}")
    missing_cols = [column for column in REQUIRED if column not in (rows[0].keys() if rows else [])]
    if missing_cols:
        errors.append(f"missing columns: {missing_cols}")
    segment_ids = [row.get("segment_id", "") for row in rows]
    if len(segment_ids) != len(set(segment_ids)):
        errors.append("segment_id values are not unique")

    boundary_counts = Counter()
    boundary_role_counts = defaultdict(Counter)
    role_counts = Counter()
    entity_counts = Counter()
    difficulty_counts = Counter()
    invalid_rows = []

    for row in rows:
        row_errors = []
        text = row.get("text", "")
        if not text.strip():
            row_errors.append("empty text")
        if not row.get("gold_entities", "").strip():
            row_errors.append("empty gold_entities")
        if any(marker in text for marker in FORBIDDEN):
            row_errors.append("forbidden heading")
        if row.get("gold_role") not in ALLOWED_ROLES:
            row_errors.append("invalid role")
        if row.get("gold_operative_status") not in ALLOWED_STATUSES:
            row_errors.append("invalid status")
        if row.get("gold_relation") not in ALLOWED_RELATIONS:
            row_errors.append("invalid relation")
        if row.get("gold_answer_relevant") not in ALLOWED_ANSWER_RELEVANCE:
            row_errors.append("invalid relevance")
        if row.get("dataset_family") == "boundary_pair":
            pair = row.get("boundary_pair")
            parts = pair.split(" vs ")
            if pair not in BOUNDARY_PAIRS:
                row_errors.append("unexpected boundary pair")
            elif row.get("gold_role") not in parts or row.get("contrast_role") not in parts:
                row_errors.append("role not in boundary pair")
            boundary_counts[pair] += 1
            boundary_role_counts[pair][row.get("gold_role")] += 1
        role_counts[row.get("gold_role")] += 1
        difficulty_counts[row.get("difficulty")] += 1
        for entity in row.get("gold_entities", "").split(";"):
            entity = entity.strip()
            if entity:
                entity_counts[entity] += 1
        if row_errors:
            invalid_rows.append((row.get("segment_id"), row_errors))

    for pair in BOUNDARY_PAIRS:
        if boundary_counts[pair] != 50:
            errors.append(f"{pair} expected 50 rows, found {boundary_counts[pair]}")
        for role in pair.split(" vs "):
            if boundary_role_counts[pair][role] != 25:
                errors.append(f"{pair} {role} expected 25 rows, found {boundary_role_counts[pair][role]}")
    entity_focus_count = sum(1 for row in rows if row.get("dataset_family") == "entity_focus")
    if entity_focus_count != 160:
        errors.append(f"entity_focus expected 160 rows, found {entity_focus_count}")
    if invalid_rows:
        errors.append(f"invalid rows: {invalid_rows[:10]}")

    print(f"Rows: {len(rows)}")
    print("Role counts:")
    for role, count in role_counts.most_common():
        print(f"- {role}: {count}")
    print("Boundary-pair counts:")
    for pair, count in boundary_counts.items():
        print(f"- {pair}: {count}")
    print("Difficulty counts:")
    for difficulty, count in difficulty_counts.most_common():
        print(f"- {difficulty}: {count}")
    print("Top entity frequencies:")
    for entity, count in entity_counts.most_common(20):
        print(f"- {entity}: {count}")
    if errors:
        print("Validation: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("Validation: PASS")


if __name__ == "__main__":
    main()
