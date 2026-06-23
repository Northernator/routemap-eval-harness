import csv
from collections import Counter, defaultdict
from pathlib import Path

from role_taxonomies import available_taxonomies, map_role


PRED_PATH = Path("data/v1/gold/boundary_pair_baseline_predictions.csv")
OUT_MD = Path("data/v1/gold/BOUNDARY_PAIR_TAXONOMY_RESULTS.md")
OUT_CSV = Path("data/v1/gold/boundary_pair_taxonomy_results.csv")


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def parse_prediction_column(pred_col):
    body = pred_col.removeprefix("pred_")
    for setting in ["A_existing_train_dev", "B_plus_boundary_train"]:
        prefix = f"{setting}_"
        if body.startswith(prefix):
            return setting, body[len(prefix):]
    return "", body


def evaluate(rows, pred_col, taxonomy):
    correct = 0
    by_pair = defaultdict(lambda: [0, 0])
    for row in rows:
        gold = map_role(row["gold_role"], taxonomy)
        pred = map_role(row[pred_col], taxonomy)
        match = gold == pred
        correct += int(match)
        by_pair[row["boundary_pair"]][0] += int(match)
        by_pair[row["boundary_pair"]][1] += 1
    return safe_div(correct, len(rows)), by_pair


def main():
    rows = read_rows(PRED_PATH)
    pred_cols = [column for column in rows[0] if column.startswith("pred_")]
    result_rows = []
    for pred_col in pred_cols:
        setting, model = parse_prediction_column(pred_col)
        for taxonomy in available_taxonomies():
            acc, by_pair = evaluate(rows, pred_col, taxonomy)
            result_rows.append({
                "setting": setting,
                "model": model,
                "prediction_column": pred_col,
                "taxonomy": taxonomy,
                "boundary_pair": "ALL",
                "accuracy": f"{acc:.6f}",
                "count": len(rows),
            })
            for pair, (correct, total) in sorted(by_pair.items()):
                result_rows.append({
                    "setting": setting,
                    "model": model,
                    "prediction_column": pred_col,
                    "taxonomy": taxonomy,
                    "boundary_pair": pair,
                    "accuracy": f"{safe_div(correct, total):.6f}",
                    "count": total,
                })

    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["setting", "model", "prediction_column", "taxonomy", "boundary_pair", "accuracy", "count"],
        )
        writer.writeheader()
        writer.writerows(result_rows)

    overall = [row for row in result_rows if row["boundary_pair"] == "ALL"]
    lines = [
        "# Boundary Pair Taxonomy Results",
        "",
        "## Overall Accuracy",
        "",
        "| setting | model | taxonomy | accuracy |",
        "|---|---|---|---:|",
    ]
    for row in overall:
        lines.append(f"| {row['setting']} | {row['model']} | {row['taxonomy']} | {float(row['accuracy']):.3f} |")

    lines.extend(["", "## Best By Taxonomy", "", "| taxonomy | setting | model | accuracy |", "|---|---|---|---:|"])
    for taxonomy in available_taxonomies():
        candidates = [row for row in overall if row["taxonomy"] == taxonomy]
        best = max(candidates, key=lambda row: (float(row["accuracy"]), row["setting"], row["model"]))
        lines.append(f"| {taxonomy} | {best['setting']} | {best['model']} | {float(best['accuracy']):.3f} |")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    for taxonomy in available_taxonomies():
        candidates = [row for row in overall if row["taxonomy"] == taxonomy]
        best = max(candidates, key=lambda row: (float(row["accuracy"]), row["setting"], row["model"]))
        print(f"{taxonomy}: best={best['setting']} {best['model']} accuracy={float(best['accuracy']):.3f}")


if __name__ == "__main__":
    main()
