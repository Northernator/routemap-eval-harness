import argparse
import csv
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import split_entity_set
from role_taxonomies import map_role


BASELINES = {
    "best local fine_8 role": 0.532,
    "ontology_v1 entity Jaccard": 0.506,
    "combined_v3 strict": 0.051,
    "combined_v3 relaxed_1": 0.253,
    "combined_v3 relaxed_2": 0.354,
    "combined_v3 relaxed_3": 0.443,
}


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(a, b):
    return a / b if b else 0.0


def entity_metrics(gold, pred):
    inter = gold & pred
    union = gold | pred
    precision = safe_div(len(inter), len(pred))
    recall = safe_div(len(inter), len(gold))
    f1 = safe_div(2 * precision * recall, precision + recall)
    return gold == pred, safe_div(len(inter), len(union)), precision, recall, f1


def failure_pattern(flags):
    return "+".join(name for name, ok in flags.items() if not ok) or "none"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    all_rows = read_rows(args.csv)
    rows = [row for row in all_rows if row.get("pred_valid") == "YES"]
    counts = Counter()
    row_out = []
    failures = Counter()
    for row in rows:
        gold_entities = split_entity_set(row.get("gold_entities", ""))
        pred_entities = split_entity_set(row.get("pred_entities", ""))
        entity_exact, entity_j, entity_p, entity_r, entity_f1 = entity_metrics(gold_entities, pred_entities)
        role_ok = row["gold_role"] == row["pred_role"]
        coarse5_ok = map_role(row["gold_role"], "coarse_5") == map_role(row["pred_role"], "coarse_5")
        coarse4_ok = map_role(row["gold_role"], "coarse_4") == map_role(row["pred_role"], "coarse_4")
        coarse3_ok = map_role(row["gold_role"], "coarse_3") == map_role(row["pred_role"], "coarse_3")
        status_ok = row["gold_operative_status"] == row["pred_operative_status"]
        relation_ok = row["gold_relation"] == row["pred_relation"]
        answer_ok = row["gold_answer_relevant"] == row["pred_answer_relevant"]
        strict = role_ok and status_ok and relation_ok and answer_ok and entity_exact
        relaxed_1 = role_ok and answer_ok and entity_j >= 0.5
        relaxed_2 = coarse4_ok and answer_ok and entity_j >= 0.5
        relaxed_3 = coarse3_ok and answer_ok and entity_j >= 0.5
        for key, ok in [
            ("role", role_ok),
            ("coarse_5", coarse5_ok),
            ("coarse_4", coarse4_ok),
            ("coarse_3", coarse3_ok),
            ("status", status_ok),
            ("relation", relation_ok),
            ("answer", answer_ok),
            ("entity_exact", entity_exact),
            ("strict", strict),
            ("relaxed_1", relaxed_1),
            ("relaxed_2", relaxed_2),
            ("relaxed_3", relaxed_3),
        ]:
            counts[key] += int(ok)
        counts["entity_j"] += entity_j
        counts["entity_p"] += entity_p
        counts["entity_r"] += entity_r
        counts["entity_f1"] += entity_f1
        pattern = failure_pattern({"role": role_ok, "entity": entity_exact, "status": status_ok, "relation": relation_ok, "answer": answer_ok})
        failures[pattern] += 1
        row_out.append({
            "segment_id": row["segment_id"],
            "gold_role": row["gold_role"],
            "pred_role": row["pred_role"],
            "gold_coarse_5": map_role(row["gold_role"], "coarse_5"),
            "pred_coarse_5": map_role(row["pred_role"], "coarse_5"),
            "gold_coarse_4": map_role(row["gold_role"], "coarse_4"),
            "pred_coarse_4": map_role(row["pred_role"], "coarse_4"),
            "gold_coarse_3": map_role(row["gold_role"], "coarse_3"),
            "pred_coarse_3": map_role(row["pred_role"], "coarse_3"),
            "gold_entities": row["gold_entities"],
            "pred_entities": row["pred_entities"],
            "entity_jaccard": f"{entity_j:.6f}",
            "gold_operative_status": row["gold_operative_status"],
            "pred_operative_status": row["pred_operative_status"],
            "gold_relation": row["gold_relation"],
            "pred_relation": row["pred_relation"],
            "gold_answer_relevant": row["gold_answer_relevant"],
            "pred_answer_relevant": row["pred_answer_relevant"],
            "failure_pattern": pattern,
        })

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(row_out[0].keys()) if row_out else ["segment_id"])
        writer.writeheader()
        writer.writerows(row_out)

    n = len(rows)
    metrics = {
        "evaluated rows": n,
        "missing/invalid rows": len(all_rows) - n,
        "role accuracy": safe_div(counts["role"], n),
        "coarse_5 accuracy": safe_div(counts["coarse_5"], n),
        "coarse_4 accuracy": safe_div(counts["coarse_4"], n),
        "coarse_3 accuracy": safe_div(counts["coarse_3"], n),
        "entity exact match": safe_div(counts["entity_exact"], n),
        "entity average Jaccard": safe_div(counts["entity_j"], n),
        "entity average precision": safe_div(counts["entity_p"], n),
        "entity average recall": safe_div(counts["entity_r"], n),
        "entity average F1": safe_div(counts["entity_f1"], n),
        "operative status accuracy": safe_div(counts["status"], n),
        "relation accuracy": safe_div(counts["relation"], n),
        "answer relevance accuracy": safe_div(counts["answer"], n),
        "strict full-row accuracy": safe_div(counts["strict"], n),
        "relaxed_1": safe_div(counts["relaxed_1"], n),
        "relaxed_2": safe_div(counts["relaxed_2"], n),
        "relaxed_3": safe_div(counts["relaxed_3"], n),
    }
    lines = ["# LLM Extraction Evaluation", "", "## Metrics", "", "| metric | value |", "|---|---:|"]
    for key, value in metrics.items():
        lines.append(f"| {key} | {value if isinstance(value, int) else f'{value:.3f}'} |")
    lines.extend(["", "## Local Baselines", "", "| baseline | score |", "|---|---:|"])
    for key, value in BASELINES.items():
        lines.append(f"| {key} | {value:.3f} |")
    lines.extend(["", "## Top Failure Patterns", "", "| pattern | rows |", "|---|---:|"])
    for pattern, count in failures.most_common(10):
        lines.append(f"| {pattern} | {count} |")
    lines.extend(["", "## Interpretation", ""])
    if n == 0:
        lines.append("No valid provider outputs were available for evaluation. Metrics are zero-valued placeholders, not model performance.")
    else:
        lines.append("Compare provider runs against local baselines only after outputs validate cleanly. Missing or invalid rows are excluded from metric denominators and counted separately.")
    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evaluated rows: {n}")
    print(f"Missing/invalid rows: {len(all_rows) - n}")
    print(f"Role accuracy: {metrics['role accuracy']:.3f}")
    print(f"Entity Jaccard: {metrics['entity average Jaccard']:.3f}")
    print(f"Strict full-row: {metrics['strict full-row accuracy']:.3f}")
    print(f"Markdown: {out_md}")
    print(f"Rows CSV: {out_csv}")


if __name__ == "__main__":
    main()
