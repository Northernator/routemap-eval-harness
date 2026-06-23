import argparse
import csv
from pathlib import Path

from role_taxonomies import available_taxonomies, map_role


def split_entities(value):
    return {part.strip().lower() for part in (value or "").split(";") if part.strip()}


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return [row for row in csv.DictReader(source) if row.get("include_in_eval", "YES") in {"", "YES"}]


def evaluate(rows, taxonomy):
    counts = {
        "role": 0,
        "relation": 0,
        "entity_exact": 0,
        "strict": 0,
        "relaxed_strict": 0,
    }
    jaccard_total = 0.0
    for row in rows:
        role_match = map_role(row["gold_role"], taxonomy) == map_role(row["pred_role"], taxonomy)
        status_match = row.get("gold_operative_status", "") == row.get("pred_operative_status", "")
        relation_match = row.get("gold_relation", "") == row.get("pred_relation", "")
        answer_match = row.get("gold_answer_relevant", "") == row.get("pred_answer_relevant", "")
        gold_entities = split_entities(row.get("gold_entities"))
        pred_entities = split_entities(row.get("pred_entities"))
        entity_exact = gold_entities == pred_entities
        intersection = gold_entities & pred_entities
        union = gold_entities | pred_entities
        jaccard = safe_div(len(intersection), len(union))
        jaccard_total += jaccard

        counts["role"] += int(role_match)
        counts["relation"] += int(relation_match)
        counts["entity_exact"] += int(entity_exact)
        counts["strict"] += int(role_match and status_match and relation_match and answer_match and entity_exact)
        counts["relaxed_strict"] += int(role_match and answer_match and jaccard >= 0.5)
    total = len(rows)
    return {
        "rows": total,
        "role_accuracy": safe_div(counts["role"], total),
        "relation_accuracy": safe_div(counts["relation"], total),
        "entity_exact_match": safe_div(counts["entity_exact"], total),
        "entity_average_jaccard": safe_div(jaccard_total, total),
        "strict_row_accuracy": safe_div(counts["strict"], total),
        "relaxed_strict_accuracy": safe_div(counts["relaxed_strict"], total),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    rows = read_rows(args.csv)
    results = {taxonomy: evaluate(rows, taxonomy) for taxonomy in available_taxonomies()}

    fields = [
        "taxonomy",
        "rows",
        "role_accuracy",
        "relation_accuracy",
        "entity_exact_match",
        "entity_average_jaccard",
        "strict_row_accuracy",
        "relaxed_strict_accuracy",
    ]
    with Path(args.out_csv).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        for taxonomy, result in results.items():
            writer.writerow({"taxonomy": taxonomy, **{key: f"{value:.6f}" if isinstance(value, float) else value for key, value in result.items()}})

    lines = [
        "# Full Extraction Taxonomy Level Evaluation",
        "",
        "| taxonomy | role_accuracy | relation_accuracy | entity_exact | entity_jaccard | strict | relaxed_strict |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for taxonomy, result in results.items():
        lines.append(
            f"| {taxonomy} | {result['role_accuracy']:.3f} | {result['relation_accuracy']:.3f} | "
            f"{result['entity_exact_match']:.3f} | {result['entity_average_jaccard']:.3f} | "
            f"{result['strict_row_accuracy']:.3f} | {result['relaxed_strict_accuracy']:.3f} |"
        )
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Strict full extraction remains hard because entity exact match and downstream relation/status fields still constrain success. Relaxed strict shows whether mapped role plus answer relevance plus partial entity overlap is improving under coarser taxonomies.",
    ])
    Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")

    for taxonomy, result in results.items():
        print(
            f"{taxonomy}: strict={result['strict_row_accuracy']:.3f} "
            f"relaxed_strict={result['relaxed_strict_accuracy']:.3f}"
        )
    print(f"Markdown: {args.out_md}")
    print(f"CSV: {args.out_csv}")


if __name__ == "__main__":
    main()
