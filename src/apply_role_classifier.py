import argparse
import csv
from collections import Counter
from pathlib import Path

from role_classifier import ALLOWED_ROLES, classify_role


def print_counts(counts):
    print("Count by predicted role:")
    for role in ALLOWED_ROLES:
        print(f"- {role}: {counts.get(role, 0)}")


def apply_classifier(input_path, output_path, pred_col):
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if pred_col not in fieldnames:
        fieldnames.append(pred_col)

    counts = Counter()
    for row in rows:
        prediction = classify_role(row.get("text", ""), row.get("title", ""))
        row[pred_col] = prediction
        counts[prediction] += 1

    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows), counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="input_csv", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--pred-col", default="pred_role_v2")
    args = parser.parse_args()

    row_count, counts = apply_classifier(args.input_csv, args.out, args.pred_col)
    print(f"Wrote {row_count} rows to {args.out}")
    print_counts(counts)


if __name__ == "__main__":
    main()
