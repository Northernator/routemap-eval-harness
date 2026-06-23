import csv
from collections import Counter, defaultdict
from pathlib import Path

from train_role_text_baselines import (
    CentroidTfidfLike,
    MultinomialNB,
    char_3_5grams,
    word_unigrams,
    word_unigrams_bigrams,
)


MODEL_TRAIN_DEV = Path("data/v1/gold/model_train_dev_role.csv")
BOUNDARY_TRAIN = Path("data/v1/gold/boundary_pair_train_v1.csv")
BOUNDARY_DEV = Path("data/v1/gold/boundary_pair_dev_v1.csv")
BOUNDARY_TEST = Path("data/v1/gold/boundary_pair_test_v1.csv")
OUT_CSV = Path("data/v1/gold/boundary_pair_baseline_results.csv")
OUT_MD = Path("data/v1/gold/BOUNDARY_PAIR_BASELINE_RESULTS.md")
PRED_OUT = Path("data/v1/gold/boundary_pair_baseline_predictions.csv")
ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def model_specs():
    return {
        "word_unigram_nb": lambda: MultinomialNB(word_unigrams),
        "word_unigram_bigram_nb": lambda: MultinomialNB(word_unigrams_bigrams),
        "char_3_5gram_nb": lambda: MultinomialNB(char_3_5grams),
        "simple_centroid_tfidf_like": CentroidTfidfLike,
    }


def train_predict(train_rows, test_rows):
    predictions = {}
    for name, factory in model_specs().items():
        model = factory()
        model.fit(train_rows)
        predictions[name] = [model.predict(row) for row in test_rows]
    return predictions


def confusion(gold_rows, preds):
    matrix = defaultdict(Counter)
    for row, pred in zip(gold_rows, preds):
        matrix[row["gold_role"]][pred] += 1
    return matrix


def accuracy(gold_rows, preds):
    return safe_div(sum(1 for row, pred in zip(gold_rows, preds) if row["gold_role"] == pred), len(gold_rows))


def per_role_f1(gold_rows, preds):
    matrix = confusion(gold_rows, preds)
    f1 = {}
    for role in ROLES:
        tp = matrix[role].get(role, 0)
        fp = sum(counts.get(role, 0) for gold, counts in matrix.items() if gold != role)
        fn = sum(count for pred, count in matrix[role].items() if pred != role)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1[role] = safe_div(2 * precision * recall, precision + recall)
    return f1


def top_pairs(gold_rows, preds):
    pairs = Counter()
    for row, pred in zip(gold_rows, preds):
        if row["gold_role"] != pred:
            pairs[(row["gold_role"], pred)] += 1
    return pairs


def main():
    base_train = read_rows(MODEL_TRAIN_DEV)
    boundary_train = read_rows(BOUNDARY_TRAIN)
    boundary_dev = read_rows(BOUNDARY_DEV)
    test_rows = read_rows(BOUNDARY_TEST)
    settings = {
        "A_existing_train_dev": base_train,
        "B_plus_boundary_train": base_train + boundary_train,
    }

    result_rows = []
    prediction_rows = []
    all_predictions = {}
    for setting, train_rows in settings.items():
        predictions = train_predict(train_rows, test_rows)
        all_predictions[setting] = predictions
        for model_name, preds in predictions.items():
            overall = accuracy(test_rows, preds)
            result_rows.append({
                "setting": setting,
                "model": model_name,
                "metric_type": "overall",
                "label": "ALL",
                "accuracy": f"{overall:.6f}",
                "f1": "",
                "count": len(test_rows),
            })
            for pair in sorted({row["boundary_pair"] for row in test_rows}):
                subset = [(row, pred) for row, pred in zip(test_rows, preds) if row["boundary_pair"] == pair]
                result_rows.append({
                    "setting": setting,
                    "model": model_name,
                    "metric_type": "boundary_pair",
                    "label": pair,
                    "accuracy": f"{accuracy([row for row, _ in subset], [pred for _, pred in subset]):.6f}",
                    "f1": "",
                    "count": len(subset),
                })
            f1 = per_role_f1(test_rows, preds)
            for role, value in f1.items():
                result_rows.append({
                    "setting": setting,
                    "model": model_name,
                    "metric_type": "per_role_f1",
                    "label": role,
                    "accuracy": "",
                    "f1": f"{value:.6f}",
                    "count": sum(1 for row in test_rows if row["gold_role"] == role),
                })

    for index, row in enumerate(test_rows):
        out = dict(row)
        for setting, predictions in all_predictions.items():
            for model_name, preds in predictions.items():
                out[f"pred_{setting}_{model_name}"] = preds[index]
        prediction_rows.append(out)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["setting", "model", "metric_type", "label", "accuracy", "f1", "count"])
        writer.writeheader()
        writer.writerows(result_rows)

    pred_fields = list(test_rows[0].keys()) + [
        f"pred_{setting}_{model_name}" for setting in settings for model_name in model_specs()
    ]
    with PRED_OUT.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=pred_fields)
        writer.writeheader()
        writer.writerows(prediction_rows)

    lines = [
        "# Boundary Pair Baseline Results",
        "",
        f"- Boundary train rows: {len(boundary_train)}",
        f"- Boundary dev rows: {len(boundary_dev)}",
        f"- Boundary test rows: {len(test_rows)}",
        "",
        "## Accuracy By Setting And Model",
        "",
        "| setting | model | accuracy |",
        "|---|---|---:|",
    ]
    best = {}
    for setting in settings:
        best[setting] = ("", -1.0)
        for model_name, preds in all_predictions[setting].items():
            score = accuracy(test_rows, preds)
            if score > best[setting][1]:
                best[setting] = (model_name, score)
            lines.append(f"| {setting} | {model_name} | {score:.3f} |")

    lines.extend(["", "## Top Confusion Pairs", ""])
    for setting in settings:
        model_name, _ = best[setting]
        lines.extend([f"### {setting}: {model_name}", "", "| gold | pred | count |", "|---|---|---:|"])
        for (gold, pred), count in top_pairs(test_rows, all_predictions[setting][model_name]).most_common(10):
            lines.append(f"| {gold} | {pred} | {count} |")
        lines.append("")

    improvement = best["B_plus_boundary_train"][1] - best["A_existing_train_dev"][1]
    lines.extend([
        "## Interpretation",
        "",
        f"Best Setting A: `{best['A_existing_train_dev'][0]}` at {best['A_existing_train_dev'][1]:.3f}.",
        f"Best Setting B: `{best['B_plus_boundary_train'][0]}` at {best['B_plus_boundary_train'][1]:.3f}.",
        f"Adding boundary-pair training data changed boundary-pair test accuracy by {improvement:+.3f}.",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote predictions: {PRED_OUT}")
    print(f"Best Setting A: {best['A_existing_train_dev'][0]} {best['A_existing_train_dev'][1]:.3f}")
    print(f"Best Setting B: {best['B_plus_boundary_train'][0]} {best['B_plus_boundary_train'][1]:.3f}")
    print(f"Improvement: {improvement:+.3f}")


if __name__ == "__main__":
    main()
