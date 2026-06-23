import argparse
import csv
from collections import Counter
from pathlib import Path


COMMONLY_CONFUSED_ROLES = {"CLAIM", "DEFINE", "METHOD", "RESULT", "BACKGROUND", "EXAMPLE"}


def load_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def review_priority(row):
    pattern_rank = {
        "all_wrong_same": 0,
        "all_wrong_different": 1,
        "nb_only_correct": 2,
        "rule_only_correct": 3,
        "hybrid_only_correct": 4,
        "rule_and_nb_correct": 5,
        "rule_and_hybrid_correct": 6,
        "nb_and_hybrid_correct": 7,
        "all_correct": 8,
    }
    predictions_disagree = len({row["pred_rule"], row["pred_nb"], row["pred_hybrid"]}) > 1
    common_role = row["gold_role"] in COMMONLY_CONFUSED_ROLES
    return (
        pattern_rank.get(row["agreement_pattern"], 9),
        0 if predictions_disagree else 1,
        0 if common_role else 1,
        row["segment_id"],
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    rows = load_rows(args.csv)
    review_rows = [row for row in rows if row["needs_review"] == "YES"]

    print(f"Total rows: {len(rows)}")
    print(f"Rows needing review: {len(review_rows)}")
    print("Count by agreement_pattern:")
    for pattern, count in Counter(row["agreement_pattern"] for row in rows).most_common():
        print(f"- {pattern}: {count}")
    print("Count by likely_ambiguity_type:")
    for ambiguity, count in Counter(row["likely_ambiguity_type"] for row in rows).most_common():
        print(f"- {ambiguity}: {count}")
    print("Count by gold_role for needs_review:")
    for role, count in Counter(row["gold_role"] for row in review_rows).most_common():
        print(f"- {role}: {count}")
    print("Top 15 rows to review first:")
    for row in sorted(review_rows, key=review_priority)[:15]:
        text = " ".join(row["text"].split())[:120]
        print(
            f"- {row['segment_id']}: gold={row['gold_role']} rule={row['pred_rule']} "
            f"nb={row['pred_nb']} hybrid={row['pred_hybrid']} "
            f"pattern={row['agreement_pattern']} ambiguity={row['likely_ambiguity_type']} text={text}"
        )


if __name__ == "__main__":
    main()
