import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


ALLOWED_ROLES = [
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
]


def safe_div(a, b):
    return a / b if b else 0.0


def default_mismatch_path(pred_col):
    safe_name = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in pred_col)
    return Path("data/v1/gold") / f"role_label_mismatches_{safe_name}.csv"


def normalized(row, column):
    return (row.get(column) or "").strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data/v1/gold/v1_annotation_targets_clean.csv",
        help="Annotation CSV containing gold_role and a prediction column.",
    )
    parser.add_argument(
        "--pred-col",
        default="sample_role",
        help="Prediction column to evaluate against gold_role.",
    )
    parser.add_argument(
        "--mismatches-out",
        default=None,
        help="Where to write rows where the prediction column differs from gold_role.",
    )
    args = parser.parse_args()

    path = Path(args.csv)
    out_path = Path(args.mismatches_out) if args.mismatches_out else default_mismatch_path(args.pred_col)

    if not path.exists():
        raise SystemExit(f"CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    required = ["segment_id", "text", "gold_role", args.pred_col]
    missing = [column for column in required if column not in fieldnames]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    labelled = [row for row in rows if normalized(row, "gold_role")]
    if not labelled:
        raise SystemExit("No gold_role labels found. Fill gold_role first.")

    invalid_gold = [
        row for row in labelled
        if normalized(row, "gold_role") not in ALLOWED_ROLES
    ]
    if invalid_gold:
        print("Invalid gold_role rows:")
        for row in invalid_gold[:20]:
            print(f"- {row.get('segment_id')}: {row.get('gold_role')}")
        raise SystemExit(1)

    invalid_pred = [
        row for row in labelled
        if normalized(row, args.pred_col) and normalized(row, args.pred_col) not in ALLOWED_ROLES
    ]

    correct = 0
    mismatches = []
    confusion = defaultdict(Counter)

    for row in labelled:
        pred = normalized(row, args.pred_col)
        gold = normalized(row, "gold_role")
        confusion[gold][pred or "(blank)"] += 1
        if pred == gold:
            correct += 1
        else:
            mismatches.append(row)

    total = len(labelled)
    accuracy = safe_div(correct, total)

    print(f"Evaluating prediction column: {args.pred_col}")
    print(f"Total rows: {len(rows)}")
    print(f"Labelled rows: {total}")
    print(f"Correct {args.pred_col} vs gold_role: {correct}")
    print(f"Accuracy: {accuracy:.3f}")
    print()

    print("Count by gold_role:")
    gold_counts = Counter(normalized(row, "gold_role") for row in labelled)
    for role in ALLOWED_ROLES:
        print(f"- {role}: {gold_counts.get(role, 0)}")
    print()

    print(f"Count by {args.pred_col}:")
    pred_counts = Counter(normalized(row, args.pred_col) or "(blank)" for row in labelled)
    for role in ALLOWED_ROLES:
        print(f"- {role}: {pred_counts.get(role, 0)}")
    for role, count in sorted(pred_counts.items()):
        if role not in ALLOWED_ROLES:
            print(f"- {role}: {count}")
    print()

    print("Per-role precision / recall / F1:")
    for role in ALLOWED_ROLES:
        tp = sum(
            1 for row in labelled
            if normalized(row, "gold_role") == role
            and normalized(row, args.pred_col) == role
        )
        fp = sum(
            1 for row in labelled
            if normalized(row, "gold_role") != role
            and normalized(row, args.pred_col) == role
        )
        fn = sum(
            1 for row in labelled
            if normalized(row, "gold_role") == role
            and normalized(row, args.pred_col) != role
        )
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        print(
            f"- {role}: "
            f"precision={precision:.3f}, recall={recall:.3f}, f1={f1:.3f}, "
            f"tp={tp}, fp={fp}, fn={fn}"
        )
    print()

    print(f"Confusion matrix: gold_role -> {args.pred_col}")
    for gold in ALLOWED_ROLES:
        parts = ", ".join(
            f"{pred}={confusion[gold][pred]}"
            for pred in sorted(confusion[gold])
        )
        print(f"- {gold}: {parts if parts else '-'}")
    print()

    print("Invalid prediction rows:")
    if invalid_pred:
        for row in invalid_pred[:20]:
            print(f"- {row.get('segment_id')}: {row.get(args.pred_col)}")
    else:
        print("- none")
    print()

    out_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "segment_id",
        "title",
        "segment_index",
        "gold_role",
        args.pred_col,
        "notes",
        "text",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in mismatches:
            writer.writerow({column: row.get(column, "") for column in fields})

    print(f"Mismatches: {len(mismatches)}")
    print(f"Wrote mismatch review file: {out_path}")


if __name__ == "__main__":
    main()
