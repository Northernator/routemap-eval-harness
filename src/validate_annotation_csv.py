import argparse
import csv
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = [
    "doc_id",
    "segment_id",
    "title",
    "segment_index",
    "text",
    "sample_role",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "notes",
]

VALID_GOLD_ROLES = {
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
}


def normalized(value):
    return "" if value is None else str(value).strip()


def count_label(counter, value):
    counter[normalized(value) or "(blank)"] += 1


def print_counts(title, counter):
    print(title)
    if not counter:
        print("- none")
        return
    for label, count in sorted(counter.items()):
        print(f"- {label}: {count}")


def validate_csv(csv_path):
    rows = []
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        rows = list(reader)

    sample_role_counts = Counter()
    gold_role_counts = Counter()
    invalid_gold_role_rows = []
    empty_segment_id_rows = []
    empty_text_rows = []

    for row_index, row in enumerate(rows, start=2):
        segment_id = normalized(row.get("segment_id", ""))
        text = normalized(row.get("text", ""))
        gold_role = normalized(row.get("gold_role", ""))

        count_label(sample_role_counts, row.get("sample_role", ""))
        count_label(gold_role_counts, gold_role)

        if not segment_id:
            empty_segment_id_rows.append(row_index)
        if not text:
            empty_text_rows.append(row_index)
        if gold_role and gold_role not in VALID_GOLD_ROLES:
            invalid_gold_role_rows.append((row_index, segment_id or "(blank)", gold_role))

    print(f"Total rows: {len(rows)}")
    print_counts("Count by sample_role:", sample_role_counts)
    print_counts("Count by gold_role:", gold_role_counts)

    if missing_columns:
        print("Missing required columns:")
        for column in missing_columns:
            print(f"- {column}")
    else:
        print("Missing required columns: none")

    print("Invalid gold_role rows:")
    if invalid_gold_role_rows:
        for row_index, segment_id, gold_role in invalid_gold_role_rows:
            print(f"- row {row_index} segment {segment_id}: {gold_role}")
    else:
        print("- none")

    print("Empty segment_id rows:")
    if empty_segment_id_rows:
        for row_index in empty_segment_id_rows:
            print(f"- row {row_index}")
    else:
        print("- none")

    print("Empty text rows:")
    if empty_text_rows:
        for row_index in empty_text_rows:
            print(f"- row {row_index}")
    else:
        print("- none")

    return missing_columns or invalid_gold_role_rows or empty_segment_id_rows or empty_text_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()

    has_errors = validate_csv(args.csv)
    if has_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
