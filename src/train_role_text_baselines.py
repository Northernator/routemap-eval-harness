import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


TRAIN_PATH = Path("data/v1/gold/model_train_dev_role.csv")
TEST_PATH = Path("data/v1/gold/model_test_fresh_adjudicated_role.csv")
PRED_OUT = Path("data/v1/gold/model_role_baseline_predictions_fresh.csv")
REPORT_OUT = Path("data/v1/gold/ROLE_MODEL_BASELINES_FRESH_ADJUDICATED.md")
ROLES = ["BACKGROUND", "CLAIM", "DEFINE", "METHOD", "RESULT", "LIMITATION", "NEXT_STEP", "EXAMPLE"]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "because",
    "before",
    "by",
    "can",
    "for",
    "from",
    "has",
    "have",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "more",
    "not",
    "of",
    "on",
    "or",
    "rather",
    "should",
    "than",
    "that",
    "the",
    "their",
    "then",
    "this",
    "to",
    "under",
    "when",
    "where",
    "whether",
    "with",
    "without",
}


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def word_tokens(text):
    return [
        token
        for token in re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", (text or "").lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def word_unigrams(row):
    return word_tokens(row.get("text", ""))


def word_unigrams_bigrams(row):
    tokens = word_tokens(row.get("text", ""))
    return tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]


def char_3_5grams(row):
    text = " ".join(re.findall(r"[a-z0-9]+", (row.get("text", "") or "").lower()))
    grams = []
    for ngram_size in range(3, 6):
        grams.extend(text[index:index + ngram_size] for index in range(0, max(0, len(text) - ngram_size + 1)))
    return grams


class MultinomialNB:
    def __init__(self, featurizer):
        self.featurizer = featurizer
        self.class_counts = Counter()
        self.feature_counts = {role: Counter() for role in ROLES}
        self.feature_totals = Counter()
        self.vocabulary = set()

    def fit(self, rows):
        for row in rows:
            role = row.get("gold_role", "")
            if role not in self.feature_counts:
                continue
            self.class_counts[role] += 1
            for feature in self.featurizer(row):
                self.feature_counts[role][feature] += 1
                self.feature_totals[role] += 1
                self.vocabulary.add(feature)

    def predict(self, row):
        features = self.featurizer(row)
        class_total = sum(self.class_counts.values())
        vocab_size = max(1, len(self.vocabulary))
        scores = {}
        for role in ROLES:
            score = math.log((self.class_counts.get(role, 0) + 1) / (class_total + len(ROLES)))
            denom = self.feature_totals.get(role, 0) + vocab_size
            for feature in features:
                score += math.log((self.feature_counts[role].get(feature, 0) + 1) / denom)
            scores[role] = score
        return max(scores.items(), key=lambda item: (item[1], item[0]))[0]


class CentroidTfidfLike:
    def __init__(self):
        self.idf = {}
        self.centroids = {role: Counter() for role in ROLES}
        self.centroid_norms = {role: 0.0 for role in ROLES}

    def fit(self, rows):
        docs = []
        df = Counter()
        for row in rows:
            counts = Counter(word_unigrams_bigrams(row))
            docs.append((row.get("gold_role", ""), counts))
            for feature in counts:
                df[feature] += 1
        total_docs = max(1, len(docs))
        self.idf = {feature: math.log((total_docs + 1) / (count + 1)) + 1 for feature, count in df.items()}
        role_doc_counts = Counter()
        for role, counts in docs:
            if role not in self.centroids:
                continue
            role_doc_counts[role] += 1
            vec = self.vectorize_counts(counts)
            for feature, value in vec.items():
                self.centroids[role][feature] += value
        for role in ROLES:
            divisor = max(1, role_doc_counts.get(role, 0))
            for feature in list(self.centroids[role]):
                self.centroids[role][feature] /= divisor
            self.centroid_norms[role] = vector_norm(self.centroids[role])

    def vectorize_counts(self, counts):
        total = sum(counts.values()) or 1
        return Counter({feature: (count / total) * self.idf.get(feature, 1.0) for feature, count in counts.items()})

    def predict(self, row):
        vec = self.vectorize_counts(Counter(word_unigrams_bigrams(row)))
        vec_norm = vector_norm(vec)
        scores = {}
        for role in ROLES:
            denom = vec_norm * self.centroid_norms[role]
            score = 0.0 if denom == 0 else dot(vec, self.centroids[role]) / denom
            scores[role] = score
        return max(scores.items(), key=lambda item: (item[1], item[0]))[0]


def dot(left, right):
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(feature, 0.0) for feature, value in left.items())


def vector_norm(vec):
    return math.sqrt(sum(value * value for value in vec.values()))


def confusion(rows, pred_col):
    matrix = defaultdict(Counter)
    for row in rows:
        matrix[row["gold_role"]][row[pred_col]] += 1
    return matrix


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def accuracy(rows, pred_col):
    return safe_div(sum(1 for row in rows if row["gold_role"] == row[pred_col]), len(rows))


def per_role_f1(rows, pred_col):
    matrix = confusion(rows, pred_col)
    result = {}
    for role in ROLES:
        tp = matrix[role].get(role, 0)
        fp = sum(counts.get(role, 0) for gold, counts in matrix.items() if gold != role)
        fn = sum(count for pred, count in matrix[role].items() if pred != role)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        result[role] = safe_div(2 * precision * recall, precision + recall)
    return result


def print_confusion(matrix):
    print(",".join(["gold\\pred"] + ROLES))
    for gold in ROLES:
        print(",".join([gold] + [str(matrix[gold].get(pred, 0)) for pred in ROLES]))


def write_predictions(rows):
    fields = [
        "segment_id",
        "gold_role",
        "pred_word_unigram_nb",
        "pred_word_unigram_bigram_nb",
        "pred_char_3_5gram_nb",
        "pred_centroid",
        "text",
    ]
    PRED_OUT.parent.mkdir(parents=True, exist_ok=True)
    with PRED_OUT.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in rows])


def write_report(train_rows, test_rows, accuracies, f1s, best_name):
    split_counts = Counter(row.get("split", "") for row in train_rows)
    lines = [
        "# Role Model Baselines: Fresh Adjudicated Test",
        "",
        "## Data",
        "",
        "| source | rows |",
        "|---|---:|",
    ]
    for split, count in split_counts.items():
        lines.append(f"| {split} | {count} |")
    lines.append(f"| fresh_v2_adjudicated_test | {len(test_rows)} |")

    lines.extend(["", "## Accuracy", "", "| model | accuracy |", "|---|---:|"])
    for name, value in accuracies.items():
        lines.append(f"| {name} | {value:.3f} |")

    lines.extend(["", f"Best model: `{best_name}` at {accuracies[best_name]:.3f}.", ""])
    lines.extend([
        "## Per-Role F1",
        "",
        "| role | word_unigram_nb | word_unigram_bigram_nb | char_3_5gram_nb | simple_centroid_tfidf_like |",
        "|---|---:|---:|---:|---:|",
    ])
    for role in ROLES:
        lines.append(
            f"| {role} | {f1s['word_unigram_nb'][role]:.3f} | "
            f"{f1s['word_unigram_bigram_nb'][role]:.3f} | "
            f"{f1s['char_3_5gram_nb'][role]:.3f} | "
            f"{f1s['simple_centroid_tfidf_like'][role]:.3f} |"
        )

    lines.extend([
        "",
        "## Comparison Against Previous Baselines",
        "",
        "| baseline | accuracy |",
        "|---|---:|",
        "| Rule v2 | 0.329 |",
        "| Naive Bayes | 0.430 |",
        "| Hybrid | 0.418 |",
        f"| Best new text baseline | {accuracies[best_name]:.3f} |",
        "",
        "## Interpretation",
        "",
        "The standard-library text baselines remain small-data baselines. They are trained only on the model-ready train/dev file and evaluated once on the locked fresh adjudicated test file. The result should guide the next modelling phase, not replace a larger validation protocol.",
        "",
        "Next recommendation: use the train/dev file for cross-validation and feature experiments, keep the fresh adjudicated test locked, and evaluate stronger learned role models only after development choices are fixed.",
    ])
    REPORT_OUT.write_text("\n".join(lines), encoding="utf-8")


def main():
    train_rows = read_rows(TRAIN_PATH)
    test_rows = read_rows(TEST_PATH)
    models = {
        "word_unigram_nb": MultinomialNB(word_unigrams),
        "word_unigram_bigram_nb": MultinomialNB(word_unigrams_bigrams),
        "char_3_5gram_nb": MultinomialNB(char_3_5grams),
        "simple_centroid_tfidf_like": CentroidTfidfLike(),
    }
    pred_cols = {
        "word_unigram_nb": "pred_word_unigram_nb",
        "word_unigram_bigram_nb": "pred_word_unigram_bigram_nb",
        "char_3_5gram_nb": "pred_char_3_5gram_nb",
        "simple_centroid_tfidf_like": "pred_centroid",
    }

    for model in models.values():
        model.fit(train_rows)

    pred_rows = []
    for row in test_rows:
        pred_row = dict(row)
        for name, model in models.items():
            pred_row[pred_cols[name]] = model.predict(row)
        pred_rows.append(pred_row)

    write_predictions(pred_rows)
    accuracies = {name: accuracy(pred_rows, pred_cols[name]) for name in models}
    f1s = {name: per_role_f1(pred_rows, pred_cols[name]) for name in models}
    best_name = max(accuracies, key=lambda name: (accuracies[name], name))
    best_col = pred_cols[best_name]

    print("Accuracy per model:")
    for name, value in accuracies.items():
        print(f"- {name}: {value:.3f}")
    print("Per-role F1 per model:")
    for name in models:
        print(f"{name}:")
        for role in ROLES:
            print(f"- {role}: {f1s[name][role]:.3f}")
    print(f"Best model: {best_name}")
    print(f"Best model accuracy: {accuracies[best_name]:.3f}")
    print("Confusion matrix for best model:")
    print_confusion(confusion(pred_rows, best_col))
    print("Top mismatches for best model:")
    mismatches = [row for row in pred_rows if row["gold_role"] != row[best_col]]
    for row in mismatches[:10]:
        text = " ".join(row.get("text", "").split())[:140]
        print(f"- {row['segment_id']}: gold={row['gold_role']} pred={row[best_col]} text={text}")
    write_report(train_rows, test_rows, accuracies, f1s, best_name)
    print(f"Predictions: {PRED_OUT}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
