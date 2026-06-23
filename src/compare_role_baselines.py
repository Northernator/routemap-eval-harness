import csv
from collections import Counter, defaultdict
from pathlib import Path


RULE_PATH = Path("data/v1/gold/heldout_full_extraction_pred_v2_fresh.csv")
NB_PATH = Path("data/v1/gold/heldout_role_nb_pred_v2_fresh.csv")
OUT_PATH = Path("data/v1/gold/ROLE_BASELINE_COMPARISON_V2_FRESH.md")

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


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def accuracy(rows, pred_col):
    return sum(1 for row in rows if row["gold_role"] == row[pred_col]) / len(rows) if rows else 0.0


def per_role(rows, pred_col):
    stats = {}
    for role in ROLES:
        role_rows = [row for row in rows if row["gold_role"] == role]
        stats[role] = {
            "support": len(role_rows),
            "correct": sum(1 for row in role_rows if row[pred_col] == role),
            "accuracy": accuracy(role_rows, pred_col),
        }
    return stats


def merge_rows():
    rule_rows = {row["segment_id"]: row for row in read_rows(RULE_PATH)}
    nb_rows = {row["segment_id"]: row for row in read_rows(NB_PATH)}
    merged = []
    for segment_id, rule_row in rule_rows.items():
        nb_row = nb_rows[segment_id]
        merged.append({
            "segment_id": segment_id,
            "title": rule_row.get("title", ""),
            "text": rule_row.get("text", ""),
            "gold_role": rule_row.get("gold_role", ""),
            "pred_role_rule": rule_row.get("pred_role", ""),
            "pred_role_nb": nb_row.get("pred_role_nb", ""),
            "notes": rule_row.get("notes", ""),
        })
    return merged


def confusion_pairs(rows, pred_col):
    counts = Counter()
    for row in rows:
        if row["gold_role"] != row[pred_col]:
            counts[(row["gold_role"], row[pred_col])] += 1
    return counts


def example_lines(rows):
    lines = ["| segment_id | gold_role | rule_pred | nb_pred | text |", "|---|---|---|---|---|"]
    for row in rows[:10]:
        text = " ".join(row["text"].split())[:120]
        lines.append(f"| {row['segment_id']} | {row['gold_role']} | {row['pred_role_rule']} | {row['pred_role_nb']} | {text} |")
    return lines


def main():
    rows = merge_rows()
    rule_acc = accuracy(rows, "pred_role_rule")
    nb_acc = accuracy(rows, "pred_role_nb")
    rule_stats = per_role(rows, "pred_role_rule")
    nb_stats = per_role(rows, "pred_role_nb")

    rule_wins = [row for row in rows if row["gold_role"] == row["pred_role_rule"] and row["gold_role"] != row["pred_role_nb"]]
    nb_wins = [row for row in rows if row["gold_role"] != row["pred_role_rule"] and row["gold_role"] == row["pred_role_nb"]]
    shared_failures = [row for row in rows if row["gold_role"] != row["pred_role_rule"] and row["gold_role"] != row["pred_role_nb"]]

    lines = [
        "# Role Baseline Comparison: Fresh Held-Out v2",
        "",
        "## Summary",
        "",
        f"- Rule v2 role accuracy: {rule_acc:.3f}",
        f"- Naive Bayes role accuracy: {nb_acc:.3f}",
        f"- Rule-only wins: {len(rule_wins)}",
        f"- Naive-Bayes-only wins: {len(nb_wins)}",
        f"- Shared failures: {len(shared_failures)}",
        "",
        "## Per-Role Comparison",
        "",
        "| role | support | rule_correct | rule_recall | nb_correct | nb_recall |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for role in ROLES:
        lines.append(
            f"| {role} | {rule_stats[role]['support']} | {rule_stats[role]['correct']} | "
            f"{rule_stats[role]['accuracy']:.3f} | {nb_stats[role]['correct']} | {nb_stats[role]['accuracy']:.3f} |"
        )

    lines.extend(["", "## Where Rule Wins", ""])
    lines.extend(example_lines(rule_wins) if rule_wins else ["No rule-only wins."])
    lines.extend(["", "## Where Naive Bayes Wins", ""])
    lines.extend(example_lines(nb_wins) if nb_wins else ["No Naive-Bayes-only wins."])
    lines.extend(["", "## Shared Failures", ""])
    lines.extend(example_lines(shared_failures))

    lines.extend(["", "## Top Rule Confusions", "", "| gold_role | pred_role | count |", "|---|---|---:|"])
    for (gold, pred), count in confusion_pairs(rows, "pred_role_rule").most_common(10):
        lines.append(f"| {gold} | {pred} | {count} |")
    lines.extend(["", "## Top Naive Bayes Confusions", "", "| gold_role | pred_role | count |", "|---|---|---:|"])
    for (gold, pred), count in confusion_pairs(rows, "pred_role_nb").most_common(10):
        lines.append(f"| {gold} | {pred} | {count} |")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "The Naive Bayes baseline is trained only on the existing development data and the earlier held-out v1 gold. "
        "It does not use the fresh held-out v2 gold for training. If it beats the rule extractor, the result suggests "
        "that even a simple learned bag-of-words baseline generalises better than the tuned rule set. If it fails in "
        "similar places, the training data is likely too small or lexically narrow for this role inventory.",
        "",
    ])

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Rule v2 role accuracy: {rule_acc:.3f}")
    print(f"Naive Bayes role accuracy: {nb_acc:.3f}")
    print(f"Rule-only wins: {len(rule_wins)}")
    print(f"Naive-Bayes-only wins: {len(nb_wins)}")
    print(f"Shared failures: {len(shared_failures)}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
