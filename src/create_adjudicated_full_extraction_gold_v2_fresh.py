import csv
from collections import Counter
from pathlib import Path


FULL_PATH = Path("data/v1/gold/heldout_full_extraction_gold_v2.csv")
REVIEW_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.csv")
OUT_PATH = Path("data/v1/gold/heldout_full_extraction_gold_v2_adjudicated.csv")

ADDED = ["original_gold_role", "adjudicated_role", "adjudication_status", "include_in_eval"]


def read_by_id(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return {row["segment_id"]: row for row in csv.DictReader(source)}


def include_flag(status):
    return "YES" if status in {"ACCEPT_GOLD", "CHANGE_GOLD"} else "NO"


def main():
    full_rows = read_by_id(FULL_PATH)
    review_rows = read_by_id(REVIEW_PATH)
    fieldnames = list(next(iter(full_rows.values())).keys()) + ADDED
    rows = []
    for segment_id in sorted(full_rows):
        row = dict(full_rows[segment_id])
        review = review_rows[segment_id]
        row["original_gold_role"] = row.get("gold_role", "")
        row["adjudicated_role"] = review.get("adjudicated_role", "")
        row["adjudication_status"] = review.get("adjudication_status", "")
        row["include_in_eval"] = include_flag(row["adjudication_status"])
        if row["include_in_eval"] == "YES":
            row["gold_role"] = row["adjudicated_role"]
        rows.append(row)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    include_counts = Counter(row["include_in_eval"] for row in rows)
    changed = sum(1 for row in rows if row["original_gold_role"] != row["adjudicated_role"])
    print(f"Rows written: {len(rows)}")
    print(f"Include YES count: {include_counts.get('YES', 0)}")
    print(f"Include NO count: {include_counts.get('NO', 0)}")
    print(f"Changed-role count: {changed}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
