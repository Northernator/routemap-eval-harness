import argparse
import csv
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import format_entity_set, split_entity_set


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def score_sets(gold, pred):
    intersection = gold & pred
    union = gold | pred
    precision = safe_div(len(intersection), len(pred))
    recall = safe_div(len(intersection), len(gold))
    f1 = safe_div(2 * precision * recall, precision + recall)
    return {
        "exact": gold == pred,
        "jaccard": safe_div(len(intersection), len(union)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "zero_overlap": not intersection,
        "missing": gold - pred,
        "extra": pred - gold,
    }


def evaluate(rows, gold_col, pred_col):
    exact = 0
    zero_overlap = 0
    totals = Counter()
    missing = Counter()
    extra = Counter()
    diagnostics = []

    for row in rows:
        gold = split_entity_set(row.get(gold_col, ""))
        pred = split_entity_set(row.get(pred_col, ""))
        scores = score_sets(gold, pred)
        exact += int(scores["exact"])
        zero_overlap += int(scores["zero_overlap"])
        totals["jaccard"] += scores["jaccard"]
        totals["precision"] += scores["precision"]
        totals["recall"] += scores["recall"]
        totals["f1"] += scores["f1"]
        missing.update(scores["missing"])
        extra.update(scores["extra"])
        diagnostics.append({
            "model": pred_col,
            "segment_id": row.get("segment_id", ""),
            "title": row.get("title", ""),
            "text": row.get("text", ""),
            "gold_entities": format_entity_set(gold),
            "pred_entities": format_entity_set(pred),
            "exact": "YES" if scores["exact"] else "NO",
            "jaccard": f"{scores['jaccard']:.6f}",
            "precision": f"{scores['precision']:.6f}",
            "recall": f"{scores['recall']:.6f}",
            "f1": f"{scores['f1']:.6f}",
            "zero_overlap": "YES" if scores["zero_overlap"] else "NO",
            "missing_entities": format_entity_set(scores["missing"]),
            "extra_entities": format_entity_set(scores["extra"]),
        })

    total = len(rows)
    return {
        "model": pred_col,
        "rows": total,
        "exact_match": safe_div(exact, total),
        "average_jaccard": safe_div(totals["jaccard"], total),
        "average_precision": safe_div(totals["precision"], total),
        "average_recall": safe_div(totals["recall"], total),
        "average_f1": safe_div(totals["f1"], total),
        "zero_overlap_rows": zero_overlap,
        "missing": missing,
        "extra": extra,
        "diagnostics": diagnostics,
    }


def write_diagnostics(path, diagnostics):
    fieldnames = [
        "model",
        "segment_id",
        "title",
        "text",
        "gold_entities",
        "pred_entities",
        "exact",
        "jaccard",
        "precision",
        "recall",
        "f1",
        "zero_overlap",
        "missing_entities",
        "extra_entities",
    ]
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(diagnostics)


def write_markdown(path, results):
    lines = [
        "# Entity Extraction Results on Fresh Adjudicated Test",
        "",
        "| model | exact match | avg Jaccard | avg precision | avg recall | avg F1 | zero-overlap rows |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for result in results:
        lines.append(
            f"| {result['model']} | {result['exact_match']:.3f} | {result['average_jaccard']:.3f} | "
            f"{result['average_precision']:.3f} | {result['average_recall']:.3f} | "
            f"{result['average_f1']:.3f} | {result['zero_overlap_rows']} |"
        )
    for result in results:
        lines.extend([
            "",
            f"## {result['model']}",
            "",
            "### Most Common Missing Gold Entities",
            "",
            "| entity | count |",
            "|---|---:|",
        ])
        for entity, count in result["missing"].most_common(15):
            lines.append(f"| {entity} | {count} |")
        lines.extend(["", "### Most Common Extra Predicted Entities", "", "| entity | count |", "|---|---:|"])
        for entity, count in result["extra"].most_common(15):
            lines.append(f"| {entity} | {count} |")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--gold-col", required=True)
    parser.add_argument("--pred-cols", nargs="+", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    rows = read_rows(args.csv)
    results = [evaluate(rows, args.gold_col, pred_col) for pred_col in args.pred_cols]
    diagnostics = []
    for result in results:
        diagnostics.extend(result["diagnostics"])

    write_diagnostics(args.out_csv, diagnostics)
    write_markdown(args.out_md, results)

    print(f"Rows: {len(rows)}")
    for result in results:
        print(f"{result['model']} exact_match: {result['exact_match']:.3f}")
        print(f"{result['model']} average_jaccard: {result['average_jaccard']:.3f}")
        print(f"{result['model']} average_precision: {result['average_precision']:.3f}")
        print(f"{result['model']} average_recall: {result['average_recall']:.3f}")
        print(f"{result['model']} average_f1: {result['average_f1']:.3f}")
        print(f"{result['model']} zero_overlap_rows: {result['zero_overlap_rows']}")
    print(f"Markdown: {args.out_md}")
    print(f"Diagnostics CSV: {args.out_csv}")


if __name__ == "__main__":
    main()
