import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


ROLES = [
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
]

MISMATCH_FIELDS = ["segment_id", "title", "text", "gold_role", "pred_role", "notes"]


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def load_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def evaluate(rows, gold_col, pred_col):
    total = len(rows)
    correct = sum(1 for row in rows if row.get(gold_col, "").strip() == row.get(pred_col, "").strip())
    matrix = defaultdict(Counter)
    mismatches = []
    for row in rows:
        gold = row.get(gold_col, "").strip()
        pred = row.get(pred_col, "").strip()
        matrix[gold][pred] += 1
        if gold != pred:
            mismatches.append(row)

    per_role = {}
    labels = sorted(set(ROLES) | set(matrix.keys()) | {pred for counts in matrix.values() for pred in counts})
    for role in labels:
        tp = matrix[role].get(role, 0)
        fp = sum(counts.get(role, 0) for gold, counts in matrix.items() if gold != role)
        fn = sum(count for pred, count in matrix[role].items() if pred != role)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        per_role[role] = {
            "precision": precision,
            "recall": recall,
            "f1": safe_div(2 * precision * recall, precision + recall),
            "support": sum(matrix[role].values()),
        }

    return {
        "accuracy": safe_div(correct, total),
        "total": total,
        "correct": correct,
        "matrix": matrix,
        "per_role": per_role,
        "mismatches": mismatches,
    }


def write_mismatches(path, mismatches, gold_col, pred_col):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=MISMATCH_FIELDS)
        writer.writeheader()
        for row in mismatches:
            writer.writerow({
                "segment_id": row.get("segment_id", ""),
                "title": row.get("title", ""),
                "text": row.get("text", ""),
                "gold_role": row.get(gold_col, ""),
                "pred_role": row.get(pred_col, ""),
                "notes": row.get("notes", ""),
            })


def print_matrix(matrix):
    print("Confusion matrix:")
    print(",".join(["gold\\pred"] + ROLES))
    for gold in ROLES:
        print(",".join([gold] + [str(matrix[gold].get(pred, 0)) for pred in ROLES]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--pred-col", required=True)
    parser.add_argument("--gold-col", default="gold_role")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    rows = load_rows(args.csv)
    analysis = evaluate(rows, args.gold_col, args.pred_col)
    write_mismatches(args.out, analysis["mismatches"], args.gold_col, args.pred_col)

    print(f"Rows: {analysis['total']}")
    print(f"Accuracy: {analysis['accuracy']:.3f}")
    print(f"Mismatches: {len(analysis['mismatches'])}")
    print("Per-role precision/recall/F1:")
    print("role,precision,recall,f1,support")
    for role in ROLES:
        metrics = analysis["per_role"].get(role, {"precision": 0.0, "recall": 0.0, "f1": 0.0, "support": 0})
        print(f"{role},{metrics['precision']:.3f},{metrics['recall']:.3f},{metrics['f1']:.3f},{metrics['support']}")
    print_matrix(analysis["matrix"])
    print(f"Mismatch CSV: {args.out}")


if __name__ == "__main__":
    main()
