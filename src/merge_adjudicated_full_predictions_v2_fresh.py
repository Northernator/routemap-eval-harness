import csv
from pathlib import Path


GOLD_PATH = Path("data/v1/gold/heldout_full_extraction_gold_v2_adjudicated.csv")
PRED_PATH = Path("data/v1/gold/heldout_full_extraction_pred_v2_fresh.csv")
OUT_PATH = Path("data/v1/gold/heldout_full_extraction_pred_v2_fresh_adjudicated.csv")
PRED_COLUMNS = ["pred_role", "pred_entities", "pred_operative_status", "pred_relation", "pred_answer_relevant"]


def read_by_id(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return {row["segment_id"]: row for row in csv.DictReader(source)}


def main():
    gold_rows = read_by_id(GOLD_PATH)
    pred_rows = read_by_id(PRED_PATH)
    fieldnames = list(next(iter(gold_rows.values())).keys())
    for column in PRED_COLUMNS:
        if column not in fieldnames:
            fieldnames.append(column)
    rows = []
    for segment_id in sorted(gold_rows):
        row = dict(gold_rows[segment_id])
        pred = pred_rows[segment_id]
        for column in PRED_COLUMNS:
            row[column] = pred.get(column, "")
        rows.append(row)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    excluded = sum(1 for row in rows if row.get("include_in_eval") == "NO")
    print(f"Rows written: {len(rows)}")
    print(f"Excluded count: {excluded}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
