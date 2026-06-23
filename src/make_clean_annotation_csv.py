import argparse
import csv
from pathlib import Path


COLUMNS = [
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


def clean_row(row):
    return {column: row.get(column, "") for column in COLUMNS}


def write_clean_csv(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    row_count = 0
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        with output_path.open("w", encoding="utf-8", newline="") as target:
            writer = csv.DictWriter(target, fieldnames=COLUMNS)
            writer.writeheader()
            for row in reader:
                writer.writerow(clean_row(row))
                row_count += 1

    return row_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="input_csv", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    row_count = write_clean_csv(args.input_csv, args.out)
    print(f"Wrote {row_count} rows to {args.out}")


if __name__ == "__main__":
    main()
