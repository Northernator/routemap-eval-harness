import argparse
import csv
from pathlib import Path

from full_extraction_rules import infer_full_fields
from role_classifier_hybrid import classify_role_hybrid


PRED_COLUMNS = [
    "pred_role",
    "pred_entities",
    "pred_operative_status",
    "pred_relation",
    "pred_answer_relevant",
]


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
        pred_role = classify_role_hybrid(row.get("text", ""), row.get("title", ""))
        fields = infer_full_fields(pred_role, row.get("text", ""), row.get("title", ""))
        row["pred_role"] = pred_role
        row["pred_entities"] = fields["entities"]
        row["pred_operative_status"] = fields["operative_status"]
        row["pred_relation"] = fields["relation"]
        row["pred_answer_relevant"] = fields["answer_relevant"]

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
