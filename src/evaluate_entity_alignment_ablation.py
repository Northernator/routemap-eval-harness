import argparse
import csv
from collections import Counter
from pathlib import Path

import entity_ontology_v1
import entity_ontology_v1_plus_true_blind
import evaluate_llm_extraction_predictions as base_eval


METRICS = [
    "evaluated_rows",
    "missing_invalid_rows",
    "role",
    "coarse_5",
    "coarse_4",
    "coarse_3",
    "entity_jaccard",
    "entity_exact",
    "status",
    "relation",
    "answer",
    "strict",
    "relaxed_1",
    "relaxed_2",
    "relaxed_3",
]


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def split_for(ontology):
    if ontology == "v1":
        return entity_ontology_v1.split_entity_set
    if ontology == "v1_plus":
        return entity_ontology_v1_plus_true_blind.split_entity_set
    raise ValueError(f"Unknown ontology: {ontology}")


def evaluate(rows, ontology):
    split_entity_set = split_for(ontology)
    valid_rows = [row for row in rows if row.get("pred_valid") == "YES"]
    counts = Counter()
    failures = Counter()
    row_out = []
    for row in valid_rows:
        gold_entities = split_entity_set(row.get("gold_entities", ""))
        pred_entities = split_entity_set(row.get("pred_entities", ""))
        entity_exact, entity_j, entity_p, entity_r, entity_f1 = base_eval.entity_metrics(gold_entities, pred_entities)
        role_ok = row["gold_role"] == row["pred_role"]
        coarse5_ok = base_eval.map_role(row["gold_role"], "coarse_5") == base_eval.map_role(row["pred_role"], "coarse_5")
        coarse4_ok = base_eval.map_role(row["gold_role"], "coarse_4") == base_eval.map_role(row["pred_role"], "coarse_4")
        coarse3_ok = base_eval.map_role(row["gold_role"], "coarse_3") == base_eval.map_role(row["pred_role"], "coarse_3")
        status_ok = row["gold_operative_status"] == row["pred_operative_status"]
        relation_ok = row["gold_relation"] == row["pred_relation"]
        answer_ok = row["gold_answer_relevant"] == row["pred_answer_relevant"]
        strict = role_ok and status_ok and relation_ok and answer_ok and entity_exact
        relaxed_1 = role_ok and answer_ok and entity_j >= 0.5
        relaxed_2 = coarse4_ok and answer_ok and entity_j >= 0.5
        relaxed_3 = coarse3_ok and answer_ok and entity_j >= 0.5
        flags = {
            "role": role_ok,
            "entity": entity_exact,
            "status": status_ok,
            "relation": relation_ok,
            "answer": answer_ok,
        }
        for key, ok in [
            ("role", role_ok),
            ("coarse_5", coarse5_ok),
            ("coarse_4", coarse4_ok),
            ("coarse_3", coarse3_ok),
            ("entity_exact", entity_exact),
            ("status", status_ok),
            ("relation", relation_ok),
            ("answer", answer_ok),
            ("strict", strict),
            ("relaxed_1", relaxed_1),
            ("relaxed_2", relaxed_2),
            ("relaxed_3", relaxed_3),
        ]:
            counts[key] += int(ok)
        for key, value in [
            ("entity_jaccard", entity_j),
            ("entity_precision", entity_p),
            ("entity_recall", entity_r),
            ("entity_f1", entity_f1),
        ]:
            counts[key] += value
        failures[base_eval.failure_pattern(flags)] += 1
        row_out.append({
            "segment_id": row["segment_id"],
            "gold_role": row["gold_role"],
            "pred_role": row["pred_role"],
            "gold_coarse_5": base_eval.map_role(row["gold_role"], "coarse_5"),
            "pred_coarse_5": base_eval.map_role(row["pred_role"], "coarse_5"),
            "gold_coarse_4": base_eval.map_role(row["gold_role"], "coarse_4"),
            "pred_coarse_4": base_eval.map_role(row["pred_role"], "coarse_4"),
            "gold_coarse_3": base_eval.map_role(row["gold_role"], "coarse_3"),
            "pred_coarse_3": base_eval.map_role(row["pred_role"], "coarse_3"),
            "gold_entities": row["gold_entities"],
            "pred_entities": row["pred_entities"],
            "entity_jaccard": f"{entity_j:.6f}",
            "entity_exact": "YES" if entity_exact else "NO",
            "gold_operative_status": row["gold_operative_status"],
            "pred_operative_status": row["pred_operative_status"],
            "gold_relation": row["gold_relation"],
            "pred_relation": row["pred_relation"],
            "gold_answer_relevant": row["gold_answer_relevant"],
            "pred_answer_relevant": row["pred_answer_relevant"],
            "failure_pattern": base_eval.failure_pattern(flags),
        })
    n = len(valid_rows)
    metrics = {
        "evaluated_rows": n,
        "missing_invalid_rows": len(rows) - n,
    }
    for metric in METRICS[2:]:
        metrics[metric] = base_eval.safe_div(counts[metric], n)
    return metrics, row_out, failures


def write_outputs(metrics, row_out, failures, out_md, out_csv, ontology):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=list(row_out[0].keys()) if row_out else ["segment_id"])
        writer.writeheader()
        writer.writerows(row_out)
    lines = [
        "# Entity Alignment Ablation Evaluation",
        "",
        f"- ontology: `{ontology}`",
        "- status: ABLATION ONLY; not locked true-blind scoring.",
        "",
        "## Metrics",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for metric in METRICS:
        value = metrics[metric]
        lines.append(f"| {metric} | {value if isinstance(value, int) else f'{value:.6f}'} |")
    lines.extend(["", "## Failure Patterns", "", "| pattern | rows |", "|---|---:|"])
    for pattern, count in failures.most_common(10):
        lines.append(f"| {pattern} | {count} |")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--ontology", choices=["v1", "v1_plus"], required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()
    metrics, row_out, failures = evaluate(read_rows(args.csv), args.ontology)
    write_outputs(metrics, row_out, failures, Path(args.out_md), Path(args.out_csv), args.ontology)
    print("entity_alignment_ablation_eval")
    print(f"csv={args.csv}")
    print(f"ontology={args.ontology}")
    for metric in METRICS:
        value = metrics[metric]
        print(f"{metric}={value if isinstance(value, int) else f'{value:.6f}'}")


if __name__ == "__main__":
    main()
