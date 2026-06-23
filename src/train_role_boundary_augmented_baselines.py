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


BASE_TRAIN = Path("data/v1/gold/model_train_dev_role.csv")
BOUNDARY_TRAIN = Path("data/v1/gold/boundary_pair_train_v1.csv")
BOUNDARY_DEV = Path("data/v1/gold/boundary_pair_dev_v1.csv")
TEST = Path("data/v1/gold/model_test_fresh_adjudicated_role.csv")
PRED_OUT = Path("data/v1/gold/boundary_augmented_role_predictions_fresh.csv")
RESULTS_CSV = Path("data/v1/gold/boundary_augmented_role_results_fresh.csv")
RESULTS_MD = Path("data/v1/gold/BOUNDARY_AUGMENTED_ROLE_RESULTS_FRESH.md")

ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]
PREVIOUS_BEST = 0.456


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def model_factories():
    return {
        "word_unigram_nb": lambda: MultinomialNB(word_unigrams),
        "word_unigram_bigram_nb": lambda: MultinomialNB(word_unigrams_bigrams),
        "char_3_5gram_nb": lambda: MultinomialNB(char_3_5grams),
        "centroid": CentroidTfidfLike,
    }


def prediction_column(setting, model_name):
    return f"pred_{setting}_{model_name}"


def train_predict(train_rows, test_rows):
    predictions = {}
    for model_name, factory in model_factories().items():
        model = factory()
        model.fit(train_rows)
        predictions[model_name] = [model.predict(row) for row in test_rows]
    return predictions


def confusion(rows, preds):
    matrix = defaultdict(Counter)
    for row, pred in zip(rows, preds):
        matrix[row["gold_role"]][pred] += 1
    return matrix


def accuracy(rows, preds):
    return safe_div(sum(1 for row, pred in zip(rows, preds) if row["gold_role"] == pred), len(rows))


def per_role_metrics(rows, preds):
    matrix = confusion(rows, preds)
    result = {}
    for role in ROLES:
        tp = matrix[role].get(role, 0)
        fp = sum(counts.get(role, 0) for gold, counts in matrix.items() if gold != role)
        fn = sum(count for pred, count in matrix[role].items() if pred != role)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        result[role] = {
            "precision": precision,
            "recall": recall,
            "f1": safe_div(2 * precision * recall, precision + recall),
            "support": sum(matrix[role].values()),
        }
    return result


def matrix_lines(matrix):
    lines = ["| gold\\pred | " + " | ".join(ROLES) + " |", "|" + "---|" * (len(ROLES) + 1)]
    for gold in ROLES:
        lines.append(f"| {gold} | " + " | ".join(str(matrix[gold].get(pred, 0)) for pred in ROLES) + " |")
    return lines


def top_confusions(rows, preds):
    pairs = Counter()
    for row, pred in zip(rows, preds):
        if row["gold_role"] != pred:
            pairs[(row["gold_role"], pred)] += 1
    return pairs


def main():
    base_rows = read_rows(BASE_TRAIN)
    boundary_train = read_rows(BOUNDARY_TRAIN)
    boundary_dev = read_rows(BOUNDARY_DEV)
    test_rows = read_rows(TEST)
    settings = {
        "base_only": base_rows,
        "base_plus_boundary_train": base_rows + boundary_train,
        "base_plus_boundary_train_dev": base_rows + boundary_train + boundary_dev,
    }

    all_predictions = {}
    for setting, train_rows in settings.items():
        all_predictions[setting] = train_predict(train_rows, test_rows)

    pred_rows = []
    for index, row in enumerate(test_rows):
        out = {
            "segment_id": row["segment_id"],
            "gold_role": row["gold_role"],
            "text": row["text"],
        }
        for setting in settings:
            for model_name in model_factories():
                out[prediction_column(setting, model_name)] = all_predictions[setting][model_name][index]
        pred_rows.append(out)

    pred_fields = [
        "segment_id",
        "gold_role",
        "text",
        "pred_base_only_word_unigram_nb",
        "pred_base_only_word_unigram_bigram_nb",
        "pred_base_only_char_3_5gram_nb",
        "pred_base_only_centroid",
        "pred_base_plus_boundary_train_word_unigram_nb",
        "pred_base_plus_boundary_train_word_unigram_bigram_nb",
        "pred_base_plus_boundary_train_char_3_5gram_nb",
        "pred_base_plus_boundary_train_centroid",
        "pred_base_plus_boundary_train_dev_word_unigram_nb",
        "pred_base_plus_boundary_train_dev_word_unigram_bigram_nb",
        "pred_base_plus_boundary_train_dev_char_3_5gram_nb",
        "pred_base_plus_boundary_train_dev_centroid",
    ]
    with PRED_OUT.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=pred_fields)
        writer.writeheader()
        writer.writerows(pred_rows)

    result_rows = []
    best = {"setting": "", "model": "", "accuracy": -1.0, "preds": []}
    for setting in settings:
        for model_name in model_factories():
            preds = all_predictions[setting][model_name]
            score = accuracy(test_rows, preds)
            if score > best["accuracy"]:
                best = {"setting": setting, "model": model_name, "accuracy": score, "preds": preds}
            result_rows.append({
                "setting": setting,
                "model": model_name,
                "metric_type": "overall",
                "label": "ALL",
                "accuracy": f"{score:.6f}",
                "precision": "",
                "recall": "",
                "f1": "",
                "support": len(test_rows),
            })
            for role, metrics in per_role_metrics(test_rows, preds).items():
                result_rows.append({
                    "setting": setting,
                    "model": model_name,
                    "metric_type": "per_role",
                    "label": role,
                    "accuracy": "",
                    "precision": f"{metrics['precision']:.6f}",
                    "recall": f"{metrics['recall']:.6f}",
                    "f1": f"{metrics['f1']:.6f}",
                    "support": metrics["support"],
                })

    with RESULTS_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["setting", "model", "metric_type", "label", "accuracy", "precision", "recall", "f1", "support"],
        )
        writer.writeheader()
        writer.writerows(result_rows)

    best_metrics = per_role_metrics(test_rows, best["preds"])
    best_matrix = confusion(test_rows, best["preds"])
    lines = [
        "# Boundary-Augmented Role Results on Fresh Adjudicated Test",
        "",
        "## Accuracy By Setting And Model",
        "",
        "| setting | model | accuracy | delta_vs_previous_0.456 |",
        "|---|---|---:|---:|",
    ]
    for row in result_rows:
        if row["metric_type"] == "overall":
            score = float(row["accuracy"])
            lines.append(f"| {row['setting']} | {row['model']} | {score:.3f} | {score - PREVIOUS_BEST:+.3f} |")
    lines.extend([
        "",
        f"Best model overall: `{best['setting']}` / `{best['model']}` at {best['accuracy']:.3f}.",
        "",
        "## Per-Role Metrics For Best Model",
        "",
        "| role | precision | recall | F1 | support |",
        "|---|---:|---:|---:|---:|",
    ])
    for role in ROLES:
        metrics = best_metrics[role]
        lines.append(f"| {role} | {metrics['precision']:.3f} | {metrics['recall']:.3f} | {metrics['f1']:.3f} | {metrics['support']} |")
    lines.extend(["", "## Confusion Matrix For Best Model", ""])
    lines.extend(matrix_lines(best_matrix))
    lines.extend(["", "## Top Confusions For Best Model", "", "| gold | pred | count |", "|---|---|---:|"])
    for (gold, pred), count in top_confusions(test_rows, best["preds"]).most_common(10):
        lines.append(f"| {gold} | {pred} | {count} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "This is a transfer test: boundary-pair train/dev rows are added to training, but the locked fresh adjudicated test remains untouched. Improvements here indicate boundary-pair examples transfer beyond the synthetic boundary test.",
    ])
    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Predictions: {PRED_OUT}")
    print(f"Results CSV: {RESULTS_CSV}")
    print(f"Results MD: {RESULTS_MD}")
    print(f"Best model: {best['setting']} {best['model']}")
    print(f"Best accuracy: {best['accuracy']:.3f}")
    print(f"Delta vs previous best: {best['accuracy'] - PREVIOUS_BEST:+.3f}")


if __name__ == "__main__":
    main()
