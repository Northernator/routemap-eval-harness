import csv
from collections import Counter, defaultdict
from pathlib import Path


PRED_PATH = Path("data/v1/gold/model_role_baseline_predictions_fresh.csv")
OUT_MD = Path("data/v1/gold/GROUPED_ROLE_TAXONOMY_RESULTS.md")
OUT_CSV = Path("data/v1/gold/grouped_role_taxonomy_results.csv")

PREDICTION_COLUMNS = [
    "pred_word_unigram_nb",
    "pred_word_unigram_bigram_nb",
    "pred_char_3_5gram_nb",
    "pred_centroid",
]

TAXONOMIES = {
    "A_8_role_original": {
        "BACKGROUND": "BACKGROUND",
        "CLAIM": "CLAIM",
        "DEFINE": "DEFINE",
        "METHOD": "METHOD",
        "RESULT": "RESULT",
        "LIMITATION": "LIMITATION",
        "NEXT_STEP": "NEXT_STEP",
        "EXAMPLE": "EXAMPLE",
    },
    "B_5_role_compressed": {
        "BACKGROUND": "CONTEXT",
        "CLAIM": "ASSERTION",
        "DEFINE": "ASSERTION",
        "RESULT": "ASSERTION",
        "METHOD": "ACTION",
        "NEXT_STEP": "ACTION",
        "LIMITATION": "CAVEAT",
        "EXAMPLE": "INSTANCE",
    },
    "C_4_role_compressed": {
        "BACKGROUND": "CONTEXT",
        "CLAIM": "CONTENT",
        "DEFINE": "CONTENT",
        "RESULT": "CONTENT",
        "METHOD": "ACTION",
        "NEXT_STEP": "ACTION",
        "EXAMPLE": "ACTION",
        "LIMITATION": "CAVEAT",
    },
    "D_3_role_compressed": {
        "BACKGROUND": "CONTEXT",
        "CLAIM": "SUBSTANTIVE",
        "DEFINE": "SUBSTANTIVE",
        "METHOD": "SUBSTANTIVE",
        "RESULT": "SUBSTANTIVE",
        "NEXT_STEP": "SUBSTANTIVE",
        "EXAMPLE": "SUBSTANTIVE",
        "LIMITATION": "CAVEAT",
    },
}


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def evaluate(rows, mapping, pred_col):
    labels = sorted(set(mapping.values()))
    matrix = defaultdict(Counter)
    for row in rows:
        gold = mapping[row["gold_role"]]
        pred = mapping[row[pred_col]]
        matrix[gold][pred] += 1
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


def write_csv(rows):
    fields = ["taxonomy", "model", "group", "accuracy", "precision", "recall", "f1", "support"]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def matrix_lines(labels, matrix):
    lines = ["| gold\\pred | " + " | ".join(labels) + " |", "|" + "---|" * (len(labels) + 1)]
    for gold in labels:
        counts = [str(matrix[gold].get(pred, 0)) for pred in labels]
        lines.append(f"| {gold} | " + " | ".join(counts) + " |")
    return lines


def main():
    rows = read_rows(PRED_PATH)
    csv_rows = []
    results = {}
    for taxonomy_name, mapping in TAXONOMIES.items():
        results[taxonomy_name] = {}
        for pred_col in PREDICTION_COLUMNS:
            result = evaluate(rows, mapping, pred_col)
            results[taxonomy_name][pred_col] = result
            for label, metrics in result["per_label"].items():
                csv_rows.append({
                    "taxonomy": taxonomy_name,
                    "model": pred_col,
                    "group": label,
                    "accuracy": f"{result['accuracy']:.6f}",
                    "precision": f"{metrics['precision']:.6f}",
                    "recall": f"{metrics['recall']:.6f}",
                    "f1": f"{metrics['f1']:.6f}",
                    "support": metrics["support"],
                })
    write_csv(csv_rows)

    lines = [
        "# Grouped Role Taxonomy Results",
        "",
        "## Accuracy Summary",
        "",
        "| taxonomy | best_model | best_accuracy | pred_word_unigram_nb | pred_word_unigram_bigram_nb | pred_char_3_5gram_nb | pred_centroid |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for taxonomy_name, model_results in results.items():
        best_model = max(model_results, key=lambda model: (model_results[model]["accuracy"], model))
        cells = [f"{model_results[pred_col]['accuracy']:.3f}" for pred_col in PREDICTION_COLUMNS]
        lines.append(
            f"| {taxonomy_name} | {best_model} | {model_results[best_model]['accuracy']:.3f} | "
            + " | ".join(cells)
            + " |"
        )

    for taxonomy_name, model_results in results.items():
        best_model = max(model_results, key=lambda model: (model_results[model]["accuracy"], model))
        best = model_results[best_model]
        lines.extend([
            "",
            f"## {taxonomy_name}: Best Model `{best_model}`",
            "",
            "| group | precision | recall | F1 | support |",
            "|---|---:|---:|---:|---:|",
        ])
        for label in best["labels"]:
            metrics = best["per_label"][label]
            lines.append(
                f"| {label} | {metrics['precision']:.3f} | {metrics['recall']:.3f} | "
                f"{metrics['f1']:.3f} | {metrics['support']} |"
            )
        lines.extend(["", "Confusion matrix:", ""])
        lines.extend(matrix_lines(best["labels"], best["matrix"]))

    lines.extend([
        "",
        "## Interpretation",
        "",
        "If compressed taxonomies score much higher than the 8-role original, the current taxonomy is too fine for the available data/features. If compressed taxonomies still perform weakly, the representation or model family is also weak.",
        "",
        "These grouped results are diagnostic only. They do not replace the 8-role benchmark.",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    for taxonomy_name, model_results in results.items():
        best_model = max(model_results, key=lambda model: (model_results[model]["accuracy"], model))
        print(f"{taxonomy_name}: best={best_model} accuracy={model_results[best_model]['accuracy']:.3f}")


if __name__ == "__main__":
    main()
