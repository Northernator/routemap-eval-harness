import argparse
import csv
from pathlib import Path

from evaluate_full_extraction_custom_cols import evaluate
from role_taxonomies import available_taxonomies, map_role


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def taxonomy_accuracy(rows, taxonomy):
    correct = 0
    for row in rows:
        correct += int(map_role(row["gold_role"], taxonomy) == map_role(row["pred_role"], taxonomy))
    return correct / len(rows) if rows else 0.0


def write_markdown(path, rows, metrics):
    lines = [
        "# RouteMap Extractor Rule Provider Results",
        "",
        "| metric | score |",
        "|---|---:|",
        f"| rows | {len(rows)} |",
        f"| role accuracy | {metrics['role_accuracy']:.3f} |",
    ]
    for taxonomy in available_taxonomies():
        lines.append(f"| {taxonomy} accuracy | {taxonomy_accuracy(rows, taxonomy):.3f} |")
    lines.extend([
        f"| entity exact | {metrics['entity_exact_match']:.3f} |",
        f"| entity Jaccard | {metrics['entity_average_jaccard']:.3f} |",
        f"| entity precision | {metrics['entity_average_precision']:.3f} |",
        f"| entity recall | {metrics['entity_average_recall']:.3f} |",
        f"| entity F1 | {metrics['entity_average_f1']:.3f} |",
        f"| status accuracy | {metrics['operative_status_accuracy']:.3f} |",
        f"| relation accuracy | {metrics['relation_accuracy']:.3f} |",
        f"| answer relevance accuracy | {metrics['answer_relevance_accuracy']:.3f} |",
        f"| strict full-row | {metrics['strict_full_row_accuracy']:.3f} |",
        f"| relaxed_1 | {metrics['relaxed_1']:.3f} |",
        f"| relaxed_2 | {metrics['relaxed_2']:.3f} |",
        f"| relaxed_3 | {metrics['relaxed_3']:.3f} |",
        "",
        "This rule provider is an offline scaffold baseline. It is provider-ready but does not call external APIs.",
    ])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    rows = read_rows(args.csv)
    metrics = evaluate(rows, "pred_role", "pred_entities", "pred_operative_status", "pred_relation", "pred_answer_relevant")
    write_markdown(args.out_md, rows, metrics)
    print(f"Rows: {len(rows)}")
    print(f"Role accuracy: {metrics['role_accuracy']:.3f}")
    print(f"Entity Jaccard: {metrics['entity_average_jaccard']:.3f}")
    print(f"Strict full-row: {metrics['strict_full_row_accuracy']:.3f}")
    print(f"Relaxed 1: {metrics['relaxed_1']:.3f}")
    print(f"Relaxed 2: {metrics['relaxed_2']:.3f}")
    print(f"Relaxed 3: {metrics['relaxed_3']:.3f}")
    print(f"Markdown: {args.out_md}")


if __name__ == "__main__":
    main()
