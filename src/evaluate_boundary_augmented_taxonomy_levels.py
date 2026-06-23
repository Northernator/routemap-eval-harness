import csv
from collections import Counter, defaultdict
from pathlib import Path

from role_taxonomies import available_taxonomies, map_role


PRED_PATH = Path("data/v1/gold/boundary_augmented_role_predictions_fresh.csv")
OUT_MD = Path("data/v1/gold/BOUNDARY_AUGMENTED_TAXONOMY_RESULTS_FRESH.md")
OUT_CSV = Path("data/v1/gold/boundary_augmented_taxonomy_results_fresh.csv")
PREVIOUS = {"fine_8": 0.456, "coarse_5": 0.582, "coarse_4": 0.633, "coarse_3": 0.810}


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def parse_pred_col(pred_col):
    body = pred_col.removeprefix("pred_")
    for setting in ["base_plus_boundary_train_dev", "base_plus_boundary_train", "base_only"]:
        prefix = f"{setting}_"
        if body.startswith(prefix):
            return setting, body[len(prefix):]
    return "", body


def evaluate(rows, pred_col, taxonomy):
    correct = 0
    matrix = defaultdict(Counter)
    for row in rows:
        gold = map_role(row["gold_role"], taxonomy)
        pred = map_role(row[pred_col], taxonomy)
        correct += int(gold == pred)
        matrix[gold][pred] += 1
    return safe_div(correct, len(rows)), matrix


def main():
    rows = read_rows(PRED_PATH)
    pred_cols = [column for column in rows[0] if column.startswith("pred_")]
    result_rows = []
    for pred_col in pred_cols:
        setting, model = parse_pred_col(pred_col)
        for taxonomy in available_taxonomies():
            score, _ = evaluate(rows, pred_col, taxonomy)
            result_rows.append({
                "setting": setting,
                "model": model,
                "prediction_column": pred_col,
                "taxonomy": taxonomy,
                "accuracy": f"{score:.6f}",
                "previous_best": f"{PREVIOUS[taxonomy]:.6f}",
                "delta": f"{score - PREVIOUS[taxonomy]:.6f}",
            })
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["setting", "model", "prediction_column", "taxonomy", "accuracy", "previous_best", "delta"],
        )
        writer.writeheader()
        writer.writerows(result_rows)

    lines = [
        "# Boundary-Augmented Taxonomy Results on Fresh Adjudicated Test",
        "",
        "## Best Model Per Taxonomy",
        "",
        "| taxonomy | setting | model | accuracy | previous_best | delta |",
        "|---|---|---|---:|---:|---:|",
    ]
    best_by_taxonomy = {}
    for taxonomy in available_taxonomies():
        candidates = [row for row in result_rows if row["taxonomy"] == taxonomy]
        best = max(candidates, key=lambda row: (float(row["accuracy"]), row["setting"], row["model"]))
        best_by_taxonomy[taxonomy] = best
        lines.append(
            f"| {taxonomy} | {best['setting']} | {best['model']} | {float(best['accuracy']):.3f} | "
            f"{float(best['previous_best']):.3f} | {float(best['delta']):+.3f} |"
        )
    lines.extend(["", "## All Scores", "", "| setting | model | taxonomy | accuracy | delta |", "|---|---|---|---:|---:|"])
    for row in result_rows:
        lines.append(f"| {row['setting']} | {row['model']} | {row['taxonomy']} | {float(row['accuracy']):.3f} | {float(row['delta']):+.3f} |")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Markdown: {OUT_MD}")
    print(f"CSV: {OUT_CSV}")
    for taxonomy, best in best_by_taxonomy.items():
        print(f"{taxonomy}: best={best['setting']} {best['model']} accuracy={float(best['accuracy']):.3f} delta={float(best['delta']):+.3f}")


if __name__ == "__main__":
    main()
