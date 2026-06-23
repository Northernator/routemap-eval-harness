import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from role_taxonomies import available_taxonomies, map_role


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def evaluate(rows, gold_col, pred_col, taxonomy):
    matrix = defaultdict(Counter)
    labels = set()
    for row in rows:
        gold = map_role(row[gold_col], taxonomy)
        pred = map_role(row[pred_col], taxonomy)
        labels.update([gold, pred])
        matrix[gold][pred] += 1
    labels = sorted(labels)
    total = len(rows)
    correct = sum(matrix[label].get(label, 0) for label in labels)
    per_label = {}
    for label in labels:
        tp = matrix[label].get(label, 0)
        fp = sum(counts.get(label, 0) for gold, counts in matrix.items() if gold != label)
        fn = sum(count for pred, count in matrix[label].items() if pred != label)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        per_label[label] = {
            "precision": precision,
            "recall": recall,
            "f1": safe_div(2 * precision * recall, precision + recall),
            "support": sum(matrix[label].values()),
        }
    return {"accuracy": safe_div(correct, total), "labels": labels, "matrix": matrix, "per_label": per_label}


def write_csv(path, rows):
    fields = ["model_name", "taxonomy", "accuracy", "label", "precision", "recall", "f1", "support"]
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def matrix_lines(labels, matrix):
    lines = ["| gold\\pred | " + " | ".join(labels) + " |", "|" + "---|" * (len(labels) + 1)]
    for gold in labels:
        lines.append(f"| {gold} | " + " | ".join(str(matrix[gold].get(pred, 0)) for pred in labels) + " |")
    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--gold-col", required=True)
    parser.add_argument("--pred-cols", nargs="+", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    rows = read_rows(args.csv)
    results = {}
    flat_rows = []
    for pred_col in args.pred_cols:
        results[pred_col] = {}
        for taxonomy in available_taxonomies():
            result = evaluate(rows, args.gold_col, pred_col, taxonomy)
            results[pred_col][taxonomy] = result
            for label, metrics in result["per_label"].items():
                flat_rows.append({
                    "model_name": pred_col,
                    "taxonomy": taxonomy,
                    "accuracy": f"{result['accuracy']:.6f}",
                    "label": label,
                    "precision": f"{metrics['precision']:.6f}",
                    "recall": f"{metrics['recall']:.6f}",
                    "f1": f"{metrics['f1']:.6f}",
                    "support": metrics["support"],
                })
    write_csv(args.out_csv, flat_rows)

    lines = [
        "# Role Taxonomy Level Evaluation",
        "",
        "## Model x Taxonomy Accuracy",
        "",
        "| model | " + " | ".join(available_taxonomies()) + " |",
        "|" + "---|" * (len(available_taxonomies()) + 1),
    ]
    for pred_col in args.pred_cols:
        lines.append(
            f"| {pred_col} | "
            + " | ".join(f"{results[pred_col][taxonomy]['accuracy']:.3f}" for taxonomy in available_taxonomies())
            + " |"
        )

    lines.extend(["", "## Best Model Per Taxonomy", "", "| taxonomy | best_model | accuracy |", "|---|---|---:|"])
    for taxonomy in available_taxonomies():
        best_model = max(args.pred_cols, key=lambda pred_col: (results[pred_col][taxonomy]["accuracy"], pred_col))
        lines.append(f"| {taxonomy} | {best_model} | {results[best_model][taxonomy]['accuracy']:.3f} |")

    lines.extend(["", "## Best Taxonomy Per Model", "", "| model | best_taxonomy | accuracy |", "|---|---|---:|"])
    for pred_col in args.pred_cols:
        best_taxonomy = max(available_taxonomies(), key=lambda taxonomy: (results[pred_col][taxonomy]["accuracy"], taxonomy))
        lines.append(f"| {pred_col} | {best_taxonomy} | {results[pred_col][best_taxonomy]['accuracy']:.3f} |")

    for taxonomy in available_taxonomies():
        best_model = max(args.pred_cols, key=lambda pred_col: (results[pred_col][taxonomy]["accuracy"], pred_col))
        result = results[best_model][taxonomy]
        lines.extend(["", f"## {taxonomy}: `{best_model}`", ""])
        lines.extend(matrix_lines(result["labels"], result["matrix"]))

    lines.extend([
        "",
        "## Interpretation",
        "",
        "Fine and coarse scores should both be reported. Coarse taxonomy gains indicate that models have route-function signal even when they miss fine-grained role boundaries.",
    ])
    Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")

    for taxonomy in available_taxonomies():
        best_model = max(args.pred_cols, key=lambda pred_col: (results[pred_col][taxonomy]["accuracy"], pred_col))
        print(f"{taxonomy}: best_model={best_model} accuracy={results[best_model][taxonomy]['accuracy']:.3f}")
    print(f"Markdown: {args.out_md}")
    print(f"CSV: {args.out_csv}")


if __name__ == "__main__":
    main()
