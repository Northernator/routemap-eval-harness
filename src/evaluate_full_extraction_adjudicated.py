import argparse
import csv
from pathlib import Path


MISMATCH_COLUMNS = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "pred_role",
    "gold_entities",
    "pred_entities",
    "gold_operative_status",
    "pred_operative_status",
    "gold_relation",
    "pred_relation",
    "gold_answer_relevant",
    "pred_answer_relevant",
    "include_in_eval",
    "adjudication_status",
    "notes",
]

FIELD_PAIRS = [
    ("role", "gold_role", "pred_role"),
    ("operative_status", "gold_operative_status", "pred_operative_status"),
    ("relation", "gold_relation", "pred_relation"),
    ("answer_relevant", "gold_answer_relevant", "pred_answer_relevant"),
]


def split_entities(value):
    return {part.strip().lower() for part in (value or "").split(";") if part.strip()}


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def evaluate(csv_path, mismatches_out):
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as source:
        all_rows = list(csv.DictReader(source))
    rows = [row for row in all_rows if row.get("include_in_eval", "YES") in {"", "YES"}]
    correct = {name: 0 for name, _, _ in FIELD_PAIRS}
    mismatch_counts = {name: 0 for name, _, _ in FIELD_PAIRS}
    exact_entities = 0
    zero_entity_overlap = 0
    jaccard_total = 0.0
    strict_full_rows = 0
    mismatch_rows = []

    for row in rows:
        field_matches = {}
        for name, gold_col, pred_col in FIELD_PAIRS:
            match = (row.get(gold_col) or "").strip() == (row.get(pred_col) or "").strip()
            field_matches[name] = match
            if match:
                correct[name] += 1
            else:
                mismatch_counts[name] += 1
        gold_entities = split_entities(row.get("gold_entities"))
        pred_entities = split_entities(row.get("pred_entities"))
        entity_exact = gold_entities == pred_entities
        if entity_exact:
            exact_entities += 1
        intersection = gold_entities & pred_entities
        union = gold_entities | pred_entities
        if not intersection:
            zero_entity_overlap += 1
        jaccard = safe_div(len(intersection), len(union))
        jaccard_total += jaccard
        strict = all(field_matches.values()) and entity_exact
        if strict:
            strict_full_rows += 1
        else:
            mismatch_rows.append(row)

    mismatches_out = Path(mismatches_out)
    mismatches_out.parent.mkdir(parents=True, exist_ok=True)
    with mismatches_out.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=MISMATCH_COLUMNS)
        writer.writeheader()
        for row in mismatch_rows:
            writer.writerow({column: row.get(column, "") for column in MISMATCH_COLUMNS})

    total = len(rows)
    return {
        "total_rows": len(all_rows),
        "evaluated_rows": total,
        "excluded_rows": len(all_rows) - total,
        "accuracies": {name: safe_div(count, total) for name, count in correct.items()},
        "mismatch_counts": mismatch_counts,
        "entity_exact_match": safe_div(exact_entities, total),
        "entity_average_jaccard": safe_div(jaccard_total, total),
        "zero_entity_overlap": zero_entity_overlap,
        "strict_full_row_accuracy": safe_div(strict_full_rows, total),
        "strict_mismatch_count": len(mismatch_rows),
        "mismatch_path": str(mismatches_out),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--mismatches-out", required=True)
    args = parser.parse_args()

    metrics = evaluate(args.csv, args.mismatches_out)
    print(f"Total rows: {metrics['total_rows']}")
    print(f"Evaluated rows: {metrics['evaluated_rows']}")
    print(f"Excluded rows: {metrics['excluded_rows']}")
    print(f"Role accuracy: {metrics['accuracies']['role']:.3f}")
    print(f"Operative status accuracy: {metrics['accuracies']['operative_status']:.3f}")
    print(f"Relation accuracy: {metrics['accuracies']['relation']:.3f}")
    print(f"Answer relevance accuracy: {metrics['accuracies']['answer_relevant']:.3f}")
    print(f"Entity exact match: {metrics['entity_exact_match']:.3f}")
    print(f"Entity average Jaccard: {metrics['entity_average_jaccard']:.3f}")
    print(f"Strict full-row accuracy: {metrics['strict_full_row_accuracy']:.3f}")
    print(f"Mismatch count: {metrics['strict_mismatch_count']}")
    print(f"Mismatch CSV path: {metrics['mismatch_path']}")


if __name__ == "__main__":
    main()
