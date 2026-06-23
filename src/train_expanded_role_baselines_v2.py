import csv
from collections import Counter, defaultdict
from pathlib import Path

from role_taxonomies import available_taxonomies, map_role
from train_role_text_baselines import CentroidTfidfLike, MultinomialNB, char_3_5grams, word_unigrams, word_unigrams_bigrams


OLD_TRAIN = Path("data/v1/gold/model_train_dev_role.csv")
EXP_TRAIN = Path("data/v1/gold/expanded_train_v2.csv")
EXP_DEV = Path("data/v1/gold/expanded_dev_v2.csv")
LOCKED_TEST = Path("data/v1/gold/model_test_fresh_adjudicated_role.csv")
EXP_TEST = Path("data/v1/gold/expanded_test_v2.csv")
OUT_CSV = Path("data/v1/gold/expanded_role_baseline_results_v2.csv")
OUT_MD = Path("data/v1/gold/EXPANDED_ROLE_BASELINE_RESULTS_V2.md")
ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def models():
    return {
        "word_unigram_nb": lambda: MultinomialNB(word_unigrams),
        "word_unigram_bigram_nb": lambda: MultinomialNB(word_unigrams_bigrams),
        "char_3_5gram_nb": lambda: MultinomialNB(char_3_5grams),
        "simple_centroid_tfidf_like": CentroidTfidfLike,
    }


def safe_div(a, b):
    return a / b if b else 0.0


def predict_rows(model, rows):
    output = []
    for row in rows:
        out = dict(row)
        out["pred_role"] = model.predict(row)
        output.append(out)
    return output


def accuracy(rows, taxonomy="fine_8"):
    correct = 0
    for row in rows:
        correct += int(map_role(row["gold_role"], taxonomy) == map_role(row["pred_role"], taxonomy))
    return safe_div(correct, len(rows))


def per_role_f1(rows):
    matrix = defaultdict(Counter)
    for row in rows:
        matrix[row["gold_role"]][row["pred_role"]] += 1
    result = {}
    for role in ROLES:
        tp = matrix[role][role]
        fp = sum(matrix[gold][role] for gold in ROLES if gold != role)
        fn = sum(count for pred, count in matrix[role].items() if pred != role)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        result[role] = safe_div(2 * precision * recall, precision + recall)
    return result


def top_confusions(rows):
    counter = Counter()
    for row in rows:
        if row["gold_role"] != row["pred_role"]:
            counter[(row["gold_role"], row["pred_role"])] += 1
    return counter


def main():
    old = read_rows(OLD_TRAIN)
    exp_train = read_rows(EXP_TRAIN)
    exp_dev = read_rows(EXP_DEV)
    tests = {"locked_fresh_adjudicated": read_rows(LOCKED_TEST), "expanded_test_v2": read_rows(EXP_TEST)}
    settings = {
        "old_train_only": old,
        "old_plus_expanded_train": old + exp_train,
        "old_plus_expanded_train_dev": old + exp_train + exp_dev,
    }
    result_rows = []
    best = {}
    for setting, train_rows in settings.items():
        for model_name, factory in models().items():
            model = factory()
            model.fit(train_rows)
            for test_name, test_rows in tests.items():
                pred_rows = predict_rows(model, test_rows)
                for taxonomy in available_taxonomies():
                    result_rows.append({
                        "setting": setting,
                        "model": model_name,
                        "testset": test_name,
                        "metric": f"{taxonomy}_accuracy",
                        "label": "ALL",
                        "value": f"{accuracy(pred_rows, taxonomy):.6f}",
                    })
                for role, f1 in per_role_f1(pred_rows).items():
                    result_rows.append({
                        "setting": setting,
                        "model": model_name,
                        "testset": test_name,
                        "metric": "per_role_f1",
                        "label": role,
                        "value": f"{f1:.6f}",
                    })
                key = (test_name, setting, model_name)
                best[key] = (accuracy(pred_rows), pred_rows)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["setting", "model", "testset", "metric", "label", "value"])
        writer.writeheader()
        writer.writerows(result_rows)

    lines = ["# Expanded Role Baseline Results V2", "", "| testset | setting | model | fine_8 | coarse_5 | coarse_4 | coarse_3 |", "|---|---|---|---:|---:|---:|---:|"]
    for setting in settings:
        for model_name in models():
            for test_name in tests:
                scores = {
                    taxonomy: next(float(row["value"]) for row in result_rows if row["setting"] == setting and row["model"] == model_name and row["testset"] == test_name and row["metric"] == f"{taxonomy}_accuracy")
                    for taxonomy in available_taxonomies()
                }
                lines.append(f"| {test_name} | {setting} | {model_name} | {scores['fine_8']:.3f} | {scores['coarse_5']:.3f} | {scores['coarse_4']:.3f} | {scores['coarse_3']:.3f} |")
    for test_name in tests:
        candidates = [(key, value) for key, value in best.items() if key[0] == test_name]
        key, value = max(candidates, key=lambda item: (item[1][0], item[0][1], item[0][2]))
        lines.extend(["", f"## Best on {test_name}", "", f"`{key[1]}` / `{key[2]}` accuracy {value[0]:.3f}.", "", "| gold | pred | count |", "|---|---|---:|"])
        for (gold, pred), count in top_confusions(value[1]).most_common(10):
            lines.append(f"| {gold} | {pred} | {count} |")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    for test_name in tests:
        key, value = max([(key, value) for key, value in best.items() if key[0] == test_name], key=lambda item: (item[1][0], item[0][1], item[0][2]))
        print(f"Best {test_name}: {key[1]} {key[2]} {value[0]:.3f}")
    print(f"Markdown: {OUT_MD}")
    print(f"CSV: {OUT_CSV}")


if __name__ == "__main__":
    main()
