import csv
from collections import Counter, defaultdict
from pathlib import Path


PRED_PATH = Path("data/v1/gold/model_role_baseline_predictions_fresh.csv")
OUT_MD = Path("data/v1/gold/ROLE_PAIR_ERROR_ANALYSIS.md")
OUT_CSV = Path("data/v1/gold/role_pair_error_analysis.csv")
PRED_COL = "pred_centroid"

BOUNDARY_BY_PAIR = [
    ({"CLAIM", "DEFINE"}, "CLAIM_DEFINE_BOUNDARY"),
    ({"METHOD", "EXAMPLE"}, "METHOD_EXAMPLE_BOUNDARY"),
    ({"RESULT", "CLAIM"}, "RESULT_CLAIM_BOUNDARY"),
    ({"RESULT", "METHOD"}, "RESULT_METHOD_BOUNDARY"),
    ({"BACKGROUND", "CLAIM"}, "BACKGROUND_CLAIM_BOUNDARY"),
    ({"LIMITATION", "CLAIM"}, "LIMITATION_CLAIM_BOUNDARY"),
    ({"NEXT_STEP", "METHOD"}, "NEXT_STEP_METHOD_BOUNDARY"),
]


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def boundary(gold, pred):
    pair = {gold, pred}
    for labels, name in BOUNDARY_BY_PAIR:
        if pair == labels:
            return name
    return "MULTIWAY_AMBIGUOUS"


def main():
    rows = read_rows(PRED_PATH)
    pair_counts = Counter((row["gold_role"], row[PRED_COL]) for row in rows if row["gold_role"] != row[PRED_COL])
    examples = defaultdict(list)
    for row in rows:
        key = (row["gold_role"], row[PRED_COL])
        if row["gold_role"] != row[PRED_COL] and len(examples[key]) < 5:
            examples[key].append(row)

    with OUT_CSV.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(
            target,
            fieldnames=["gold_role", "pred_role", "count", "likely_rubric_boundary", "segment_id", "text"],
        )
        writer.writeheader()
        for (gold, pred), count in pair_counts.most_common():
            for row in examples[(gold, pred)]:
                writer.writerow({
                    "gold_role": gold,
                    "pred_role": pred,
                    "count": count,
                    "likely_rubric_boundary": boundary(gold, pred),
                    "segment_id": row["segment_id"],
                    "text": row["text"],
                })

    lines = [
        "# Role Pair Error Analysis",
        "",
        f"- Prediction column: `{PRED_COL}`",
        "",
        "## Confusion Pairs",
        "",
        "| gold_role | pred_role | count | likely_rubric_boundary |",
        "|---|---|---:|---|",
    ]
    for (gold, pred), count in pair_counts.most_common():
        lines.append(f"| {gold} | {pred} | {count} | {boundary(gold, pred)} |")

    lines.extend(["", "## Examples By Top Pair", ""])
    for (gold, pred), count in pair_counts.most_common(10):
        lines.extend([f"### {gold} -> {pred} ({count})", ""])
        for row in examples[(gold, pred)]:
            text = " ".join(row["text"].split())
            lines.append(f"- `{row['segment_id']}`: {text}")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_CSV}")
    print("Top confusion pairs:")
    for (gold, pred), count in pair_counts.most_common(5):
        print(f"- {gold} -> {pred}: {count} ({boundary(gold, pred)})")


if __name__ == "__main__":
    main()
