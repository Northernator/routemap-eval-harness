import argparse
import csv
from pathlib import Path

from full_extraction_rules import infer_full_fields


FILL_COLUMNS = [
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
]


def fill_gold(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    for column in FILL_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)

    fill_counts = {column: 0 for column in FILL_COLUMNS}
    for row in rows:
        role = (row.get("gold_role") or "").strip()
        fields = infer_full_fields(role, row.get("text", ""), row.get("title", ""))
        updates = {
            "gold_entities": fields["entities"],
            "gold_operative_status": fields["operative_status"],
            "gold_relation": fields["relation"],
            "gold_answer_relevant": fields["answer_relevant"],
        }
        for column, value in updates.items():
            if not (row.get(column) or "").strip():
                row[column] = value
                fill_counts[column] += 1

    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), fill_counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_csv", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    row_count, fill_counts = fill_gold(args.input_csv, args.out)
    print(f"Wrote {row_count} rows to {args.out}")
    print("Filled fields:")
    for column in FILL_COLUMNS:
        print(f"- {column}: {fill_counts[column]}")


if __name__ == "__main__":
    main()
