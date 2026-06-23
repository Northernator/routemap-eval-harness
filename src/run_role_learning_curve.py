import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

from train_role_text_baselines import CentroidTfidfLike, MultinomialNB, accuracy, read_rows, word_unigrams_bigrams


TRAIN_PATH = Path("data/v1/gold/model_train_dev_role.csv")
TEST_PATH = Path("data/v1/gold/model_test_fresh_adjudicated_role.csv")
OUT_MD = Path("data/v1/gold/ROLE_LEARNING_CURVE_RESULTS.md")
OUT_CSV = Path("data/v1/gold/role_learning_curve_results.csv")
SIZES = [20, 40, 60, 80, 120, "all"]
SEEDS = [1, 2, 3, 4, 5]
ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]


def balanced_sample(rows, target_size, seed):
    if target_size == "all" or target_size >= len(rows):
        return list(rows)
    rng = random.Random(seed)
    by_role = defaultdict(list)
    for row in rows:
        by_role[row["gold_role"]].append(row)
    for role_rows in by_role.values():
        rng.shuffle(role_rows)

    selected = []
    base = target_size // len(ROLES)
    remainder = target_size % len(ROLES)
    roles = list(ROLES)
    rng.shuffle(roles)
    for index, role in enumerate(roles):
        take = base + (1 if index < remainder else 0)
        selected.extend(by_role[role][:take])
    if len(selected) < target_size:
        selected_ids = {id(row) for row in selected}
        leftovers = [row for row in rows if id(row) not in selected_ids]
        rng.shuffle(leftovers)
        selected.extend(leftovers[:target_size - len(selected)])
    rng.shuffle(selected)
    return selected[:target_size]


def run_model(model_name, train_rows, test_rows):
    if model_name == "word_unigram_bigram_nb":
        model = MultinomialNB(word_unigrams_bigrams)
        pred_col = "pred"
    else:
        model = CentroidTfidfLike()
        pred_col = "pred"
    model.fit(train_rows)
    pred_rows = []
    for row in test_rows:
        pred = dict(row)
        pred[pred_col] = model.predict(row)
        pred_rows.append(pred)
    return accuracy(pred_rows, pred_col)


def write_csv(rows):
    fields = ["model", "train_size", "seed", "actual_train_rows", "accuracy"]
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    train_rows = read_rows(TRAIN_PATH)
    test_rows = read_rows(TEST_PATH)
    models = ["simple_centroid_tfidf_like", "word_unigram_bigram_nb"]
    result_rows = []
    for model_name in models:
        for size in SIZES:
            for seed in SEEDS:
                sample_seed = 42 + seed
                sampled = balanced_sample(train_rows, len(train_rows) if size == "all" else size, sample_seed)
                result_rows.append({
                    "model": model_name,
                    "train_size": str(size),
                    "seed": seed,
                    "actual_train_rows": len(sampled),
                    "accuracy": f"{run_model(model_name, sampled, test_rows):.6f}",
                })
    write_csv(result_rows)

    grouped = defaultdict(list)
    for row in result_rows:
        grouped[(row["model"], row["train_size"])].append(float(row["accuracy"]))

    lines = [
        "# Role Learning Curve Results",
        "",
        "| model | train_size | mean_accuracy | min_accuracy | max_accuracy |",
        "|---|---:|---:|---:|---:|",
    ]
    for model_name in models:
        for size in SIZES:
            values = grouped[(model_name, str(size))]
            mean = sum(values) / len(values)
            lines.append(f"| {model_name} | {size} | {mean:.3f} | {min(values):.3f} | {max(values):.3f} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "If accuracy rises with more data, collect more labels. If accuracy plateaus low, improve features, model family, or taxonomy before collecting large amounts of similar data.",
    ])
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    for model_name in models:
        values = grouped[(model_name, "all")]
        print(f"{model_name} all-data mean={sum(values) / len(values):.3f} min={min(values):.3f} max={max(values):.3f}")


if __name__ == "__main__":
    main()
