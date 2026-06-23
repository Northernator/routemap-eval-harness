import csv
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


TRAIN_PATHS = [
    Path("data/v1/gold/v1_full_extraction_gold_v1_noleak.csv"),
    Path("data/v1/gold/heldout_full_extraction_gold_v1.csv"),
]
TEST_PATH = Path("data/v1/gold/heldout_full_extraction_gold_v2.csv")
OUT_PATH = Path("data/v1/gold/heldout_role_nb_pred_v2_fresh.csv")

ROLES = [
    "BACKGROUND",
    "CLAIM",
    "DEFINE",
    "METHOD",
    "RESULT",
    "LIMITATION",
    "NEXT_STEP",
    "EXAMPLE",
]

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

BIGRAM_KEEPERS = {
    "agent",
    "answer",
    "audit",
    "benchmark",
    "claim",
    "consent",
    "control",
    "evidence",
    "evaluation",
    "future",
    "gold",
    "human",
    "incident",
    "label",
    "limitation",
    "memory",
    "model",
    "next",
    "permission",
    "policy",
    "privacy",
    "release",
    "retrieval",
    "review",
    "risk",
    "route",
    "routemap",
    "source",
    "tool",
    "trace",
}


def read_rows(paths):
    rows = []
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            rows.extend(csv.DictReader(source))
    return rows


def tokenize(text):
    words = [
        token
        for token in re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", (text or "").lower())
        if token not in STOPWORDS and len(token) > 1
    ]
    features = list(words)
    for left, right in zip(words, words[1:]):
        if left in BIGRAM_KEEPERS or right in BIGRAM_KEEPERS:
            features.append(f"{left}_{right}")
    return features


def train_nb(rows):
    class_counts = Counter()
    token_counts = {role: Counter() for role in ROLES}
    token_totals = Counter()
    vocabulary = set()

    for row in rows:
        role = row.get("gold_role", "").strip()
        if role not in token_counts:
            continue
        class_counts[role] += 1
        for token in tokenize(row.get("text", "")):
            token_counts[role][token] += 1
            token_totals[role] += 1
            vocabulary.add(token)

    return {
        "class_counts": class_counts,
        "token_counts": token_counts,
        "token_totals": token_totals,
        "vocabulary": vocabulary,
        "total_rows": sum(class_counts.values()),
    }


def score_roles(model, text):
    tokens = tokenize(text)
    vocab_size = max(1, len(model["vocabulary"]))
    class_total = max(1, model["total_rows"])
    scores = {}

    for role in ROLES:
        class_count = model["class_counts"].get(role, 0)
        prior = math.log((class_count + 1) / (class_total + len(ROLES)))
        denom = model["token_totals"].get(role, 0) + vocab_size
        score = prior
        for token in tokens:
            score += math.log((model["token_counts"][role].get(token, 0) + 1) / denom)
        scores[role] = score
    return scores


def predict_role(model, text):
    scores = score_roles(model, text)
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    best_role, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else best_score
    return best_role, best_score - second_score, scores


def confusion_matrix(rows, pred_col, gold_col="gold_role"):
    matrix = defaultdict(Counter)
    for row in rows:
        matrix[row.get(gold_col, "").strip()][row.get(pred_col, "").strip()] += 1
    return matrix


def print_matrix(matrix):
    header = ["gold\\pred"] + ROLES
    print(",".join(header))
    for gold in ROLES:
        counts = [str(matrix[gold].get(pred, 0)) for pred in ROLES]
        print(",".join([gold] + counts))


def main():
    train_rows = read_rows(TRAIN_PATHS)
    test_rows = read_rows([TEST_PATH])
    model = train_nb(train_rows)

    output_rows = []
    correct = 0
    for row in test_rows:
        pred, margin, _ = predict_role(model, row.get("text", ""))
        if pred == row.get("gold_role", "").strip():
            correct += 1
        output_rows.append({
            "segment_id": row.get("segment_id", ""),
            "title": row.get("title", ""),
            "text": row.get("text", ""),
            "gold_role": row.get("gold_role", ""),
            "pred_role_nb": pred,
            "notes": row.get("notes", ""),
            "_margin": f"{margin:.6f}",
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["segment_id", "title", "text", "gold_role", "pred_role_nb", "notes"],
        )
        writer.writeheader()
        writer.writerows([{key: row[key] for key in writer.fieldnames} for row in output_rows])

    accuracy = correct / len(test_rows) if test_rows else 0.0
    print(f"Training rows: {model['total_rows']}")
    print(f"Test rows: {len(test_rows)}")
    print(f"Role accuracy: {accuracy:.3f}")
    print("Count by gold role:")
    for role, count in Counter(row["gold_role"] for row in output_rows).most_common():
        print(f"- {role}: {count}")
    print("Count by predicted role:")
    for role, count in Counter(row["pred_role_nb"] for row in output_rows).most_common():
        print(f"- {role}: {count}")
    print("Confusion matrix:")
    print_matrix(confusion_matrix(output_rows, "pred_role_nb"))
    print("Top incorrect examples:")
    incorrect = [row for row in output_rows if row["gold_role"] != row["pred_role_nb"]]
    incorrect.sort(key=lambda row: row["_margin"], reverse=True)
    for row in incorrect[:10]:
        text = " ".join(row["text"].split())[:140]
        print(f"- {row['segment_id']}: gold={row['gold_role']} pred={row['pred_role_nb']} text={text}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
