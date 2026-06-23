import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]
MISMATCH_FIELDS = [
    "segment_id",
    "title",
    "text",
    "original_gold_role",
    "adjudicated_role",
    "pred_role",
    "adjudication_status",
    "rubric_issue",
    "adjudication_reason",
]


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def read_by_id(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return {row["segment_id"]: row for row in csv.DictReader(source)}


def metrics(gold_rows, pred_rows, pred_col):
    eval_rows = [row for row in gold_rows.values() if row.get("include_in_eval") == "YES"]
    matrix = defaultdict(Counter)
    mismatches = []
    for gold in eval_rows:
        pred = pred_rows[gold["segment_id"]].get(pred_col, "")
        actual = gold.get("adjudicated_role", "")
        matrix[actual][pred] += 1
        if pred != actual:
            mismatches.append((gold, pred))
    total = len(eval_rows)
    correct = sum(matrix[role].get(role, 0) for role in ROLES)
    per_role = {}
    for role in ROLES:
        tp = matrix[role].get(role, 0)
        fp = sum(counts.get(role, 0) for gold_role, counts in matrix.items() if gold_role != role)
        fn = sum(count for pred_role, count in matrix[role].items() if pred_role != role)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        per_role[role] = (precision, recall, safe_div(2 * precision * recall, precision + recall), sum(matrix[role].values()))
    return {
        "total_rows": len(gold_rows),
        "evaluated_rows": total,
        "excluded_rows": len(gold_rows) - total,
        "accuracy": safe_div(correct, total),
        "matrix": matrix,
        "per_role": per_role,
        "mismatches": mismatches,
    }


def write_mismatches(path, mismatches):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=MISMATCH_FIELDS)
        writer.writeheader()
        for gold, pred in mismatches:
            writer.writerow({
                "segment_id": gold.get("segment_id", ""),
                "title": gold.get("title", ""),
                "text": gold.get("text", ""),
                "original_gold_role": gold.get("original_gold_role", ""),
                "adjudicated_role": gold.get("adjudicated_role", ""),
                "pred_role": pred,
                "adjudication_status": gold.get("adjudication_status", ""),
                "rubric_issue": gold.get("rubric_issue", ""),
                "adjudication_reason": gold.get("adjudication_reason", ""),
            })


def print_matrix(matrix):
    print("Confusion matrix:")
    print(",".join(["gold\\pred"] + ROLES))
    for gold in ROLES:
        print(",".join([gold] + [str(matrix[gold].get(pred, 0)) for pred in ROLES]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--pred", required=True)
    parser.add_argument("--pred-col", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    gold_rows = read_by_id(args.gold)
    pred_rows = read_by_id(args.pred)
    result = metrics(gold_rows, pred_rows, args.pred_col)
    write_mismatches(args.out, result["mismatches"])

    print(f"Total rows: {result['total_rows']}")
    print(f"Evaluated rows: {result['evaluated_rows']}")
    print(f"Excluded rows: {result['excluded_rows']}")
    print(f"Accuracy: {result['accuracy']:.3f}")
    print("Per-role precision/recall/F1:")
    print("role,precision,recall,f1,support")
    for role in ROLES:
        precision, recall, f1, support = result["per_role"][role]
        print(f"{role},{precision:.3f},{recall:.3f},{f1:.3f},{support}")
    print_matrix(result["matrix"])
    print(f"Mismatch count: {len(result['mismatches'])}")
    print(f"Mismatch CSV path: {args.out}")


if __name__ == "__main__":
    main()
