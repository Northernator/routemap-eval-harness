import csv
from collections import Counter
from pathlib import Path


ROLE_PATH = Path("data/v1/gold/heldout_role_eval_v2.csv")
REVIEW_PATH = Path("data/v1/gold/role_adjudication_review_v2_fresh.csv")
OUT_PATH = Path("data/v1/gold/heldout_role_eval_v2_adjudicated.csv")

FIELDNAMES = [
    "segment_id",
    "title",
    "text",
    "original_gold_role",
    "adjudicated_role",
    "adjudication_status",
    "rubric_issue",
    "adjudication_reason",
    "include_in_eval",
    "notes",
]


def read_by_id(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return {row["segment_id"]: row for row in csv.DictReader(source)}


def include_flag(status):
    return "YES" if status in {"ACCEPT_GOLD", "CHANGE_GOLD"} else "NO"


def main():
    role_rows = read_by_id(ROLE_PATH)
    review_rows = read_by_id(REVIEW_PATH)
    rows = []
    for segment_id in sorted(role_rows):
        role_row = role_rows[segment_id]
        review = review_rows[segment_id]
        rows.append({
            "segment_id": segment_id,
            "title": role_row.get("title", ""),
            "text": role_row.get("text", ""),
            "original_gold_role": role_row.get("gold_role", ""),
            "adjudicated_role": review.get("adjudicated_role", ""),
            "adjudication_status": review.get("adjudication_status", ""),
            "rubric_issue": review.get("rubric_issue", ""),
            "adjudication_reason": review.get("adjudication_reason", ""),
            "include_in_eval": include_flag(review.get("adjudication_status", "")),
            "notes": role_row.get("notes", ""),
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    status_counts = Counter(row["adjudication_status"] for row in rows)
    include_counts = Counter(row["include_in_eval"] for row in rows)
    changed = sum(1 for row in rows if row["original_gold_role"] != row["adjudicated_role"])
    print(f"Rows written: {len(rows)}")
    print(f"Include YES count: {include_counts.get('YES', 0)}")
    print(f"Include NO count: {include_counts.get('NO', 0)}")
    print("Status counts:")
    for status in ["ACCEPT_GOLD", "CHANGE_GOLD", "NEEDS_SECOND_REVIEW", "RUBRIC_AMBIGUOUS"]:
        print(f"- {status}: {status_counts.get(status, 0)}")
    print(f"Changed-role count: {changed}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
