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
    "notes",
]

FIELD_PAIRS = [
    ("role", "gold_role", "pred_role"),
    ("operative_status", "gold_operative_status", "pred_operative_status"),
    ("relation", "gold_relation", "pred_relation"),
    ("answer_relevant", "gold_answer_relevant", "pred_answer_relevant"),
]


def split_entities(value):
    return {
        part.strip().lower()
        for part in (value or "").split(";")
        if part.strip()
    }


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def evaluate(csv_path, mismatches_out):
    csv_path = Path(csv_path)
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)

    total = len(rows)
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

    metrics = {
        "total_rows": total,
        "accuracies": {name: safe_div(count, total) for name, count in correct.items()},
        "mismatch_counts": mismatch_counts,
        "entity_exact_match": safe_div(exact_entities, total),
        "entity_average_jaccard": safe_div(jaccard_total, total),
        "zero_entity_overlap": zero_entity_overlap,
        "strict_full_row_accuracy": safe_div(strict_full_rows, total),
        "strict_mismatch_count": len(mismatch_rows),
        "mismatch_path": str(mismatches_out),
    }
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--mismatches-out", default="data/v1/gold/full_extraction_mismatches_v1.csv")
    args = parser.parse_args()

    metrics = evaluate(args.csv, args.mismatches_out)

    print(f"Total rows: {metrics['total_rows']}")
    print(f"Role accuracy: {metrics['accuracies']['role']:.3f}")
    print(f"Operative status accuracy: {metrics['accuracies']['operative_status']:.3f}")
    print(f"Relation accuracy: {metrics['accuracies']['relation']:.3f}")
    print(f"Answer relevance accuracy: {metrics['accuracies']['answer_relevant']:.3f}")
    print(f"Entity exact match: {metrics['entity_exact_match']:.3f}")
    print(f"Entity average Jaccard: {metrics['entity_average_jaccard']:.3f}")
    print(f"Rows with zero entity overlap: {metrics['zero_entity_overlap']}")
    print(f"Strict full-row accuracy: {metrics['strict_full_row_accuracy']:.3f}")
    print("Mismatch counts by field:")
    for name in ["role", "operative_status", "relation", "answer_relevant"]:
        print(f"- {name}: {metrics['mismatch_counts'][name]}")
    print(f"Mismatch count: {metrics['strict_mismatch_count']}")
    print(f"Strict mismatch rows: {metrics['strict_mismatch_count']}")
    print(f"Wrote mismatch review file: {metrics['mismatch_path']}")


if __name__ == "__main__":
    main()
