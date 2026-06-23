import argparse
import csv
from collections import Counter
from pathlib import Path

from entity_ontology_v1 import format_entity_set, split_entity_set
from role_taxonomies import map_role


PREVIOUS = {
    "strict_full_row": 0.000,
    "relaxed_boundary_role": 0.089,
    "entity_jaccard_current": 0.326,
    "entity_jaccard_ontology_v1": 0.506,
}


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def entity_scores(gold, pred):
    intersection = gold & pred
    union = gold | pred
    precision = safe_div(len(intersection), len(pred))
    recall = safe_div(len(intersection), len(gold))
    f1 = safe_div(2 * precision * recall, precision + recall)
    return {
        "exact": gold == pred,
        "jaccard": safe_div(len(intersection), len(union)),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "zero_overlap": not intersection,
    }


def failure_pattern(role_ok, status_ok, relation_ok, answer_ok, entity_exact, entity_jaccard):
    failures = []
    if not role_ok:
        failures.append("role")
    if not status_ok:
        failures.append("status")
    if not relation_ok:
        failures.append("relation")
    if not answer_ok:
        failures.append("answer")
    if not entity_exact:
        failures.append("entity_exact")
    if entity_jaccard < 0.5:
        failures.append("entity_jaccard_lt_0.5")
    return "+".join(failures) if failures else "none"


def evaluate(rows, role_col, entities_col, status_col, relation_col, answer_col):
    counts = Counter()
    failure_counts = Counter()
    mismatch_rows = []

    for row in rows:
        gold_entities = split_entity_set(row.get("gold_entities", ""))
        pred_entities = split_entity_set(row.get(entities_col, ""))
        entity = entity_scores(gold_entities, pred_entities)

        role_ok = row.get("gold_role") == row.get(role_col)
        status_ok = row.get("gold_operative_status") == row.get(status_col)
        relation_ok = row.get("gold_relation") == row.get(relation_col)
        answer_ok = row.get("gold_answer_relevant") == row.get(answer_col)
        strict_ok = role_ok and status_ok and relation_ok and answer_ok and entity["exact"]
        relaxed_1 = role_ok and answer_ok and entity["jaccard"] >= 0.5
        relaxed_2 = map_role(row.get("gold_role", ""), "coarse_4") == map_role(row.get(role_col, ""), "coarse_4") and answer_ok and entity["jaccard"] >= 0.5
        relaxed_3 = map_role(row.get("gold_role", ""), "coarse_3") == map_role(row.get(role_col, ""), "coarse_3") and answer_ok and entity["jaccard"] >= 0.5

        counts["role"] += int(role_ok)
        counts["status"] += int(status_ok)
        counts["relation"] += int(relation_ok)
        counts["answer"] += int(answer_ok)
        counts["entity_exact"] += int(entity["exact"])
        counts["entity_zero_overlap"] += int(entity["zero_overlap"])
        counts["strict"] += int(strict_ok)
        counts["relaxed_1"] += int(relaxed_1)
        counts["relaxed_2"] += int(relaxed_2)
        counts["relaxed_3"] += int(relaxed_3)
        counts["entity_jaccard"] += entity["jaccard"]
        counts["entity_precision"] += entity["precision"]
        counts["entity_recall"] += entity["recall"]
        counts["entity_f1"] += entity["f1"]

        pattern = failure_pattern(role_ok, status_ok, relation_ok, answer_ok, entity["exact"], entity["jaccard"])
        if pattern != "none":
            failure_counts[pattern] += 1
            mismatch_rows.append({
                "segment_id": row.get("segment_id", ""),
                "title": row.get("title", ""),
                "text": row.get("text", ""),
                "gold_role": row.get("gold_role", ""),
                "pred_role": row.get(role_col, ""),
                "gold_entities": format_entity_set(gold_entities),
                "pred_entities": format_entity_set(pred_entities),
                "entity_jaccard": f"{entity['jaccard']:.6f}",
                "gold_operative_status": row.get("gold_operative_status", ""),
                "pred_operative_status": row.get(status_col, ""),
                "gold_relation": row.get("gold_relation", ""),
                "pred_relation": row.get(relation_col, ""),
                "gold_answer_relevant": row.get("gold_answer_relevant", ""),
                "pred_answer_relevant": row.get(answer_col, ""),
                "failure_pattern": pattern,
            })

    total = len(rows)
    return {
        "evaluated_rows": total,
        "role_accuracy": safe_div(counts["role"], total),
        "operative_status_accuracy": safe_div(counts["status"], total),
        "relation_accuracy": safe_div(counts["relation"], total),
        "answer_relevance_accuracy": safe_div(counts["answer"], total),
        "entity_exact_match": safe_div(counts["entity_exact"], total),
        "entity_average_jaccard": safe_div(counts["entity_jaccard"], total),
        "entity_average_precision": safe_div(counts["entity_precision"], total),
        "entity_average_recall": safe_div(counts["entity_recall"], total),
        "entity_average_f1": safe_div(counts["entity_f1"], total),
        "zero_entity_overlap_rows": counts["entity_zero_overlap"],
        "strict_full_row_accuracy": safe_div(counts["strict"], total),
        "relaxed_1": safe_div(counts["relaxed_1"], total),
        "relaxed_2": safe_div(counts["relaxed_2"], total),
        "relaxed_3": safe_div(counts["relaxed_3"], total),
        "failure_counts": failure_counts,
        "mismatch_rows": mismatch_rows,
    }


def write_mismatches(path, rows):
    fieldnames = [
        "segment_id",
        "title",
        "text",
        "gold_role",
        "pred_role",
        "gold_entities",
        "pred_entities",
        "entity_jaccard",
        "gold_operative_status",
        "pred_operative_status",
        "gold_relation",
        "pred_relation",
        "gold_answer_relevant",
        "pred_answer_relevant",
        "failure_pattern",
    ]
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, total_rows, excluded_rows, metrics):
    lines = [
        "# Combined V3 Full Extraction Results",
        "",
        "## Previous Reference Points",
        "",
        "| reference | score |",
        "|---|---:|",
        f"| previous strict full-row | {PREVIOUS['strict_full_row']:.3f} |",
        f"| previous relaxed full-row after boundary role | {PREVIOUS['relaxed_boundary_role']:.3f} |",
        f"| previous entity Jaccard current | {PREVIOUS['entity_jaccard_current']:.3f} |",
        f"| ontology_v1 entity Jaccard | {PREVIOUS['entity_jaccard_ontology_v1']:.3f} |",
        "",
        "## Combined V3 Scores",
        "",
        "| metric | score |",
        "|---|---:|",
        f"| total rows | {total_rows} |",
        f"| evaluated rows | {metrics['evaluated_rows']} |",
        f"| excluded rows | {excluded_rows} |",
        f"| role accuracy | {metrics['role_accuracy']:.3f} |",
        f"| operative status accuracy | {metrics['operative_status_accuracy']:.3f} |",
        f"| relation accuracy | {metrics['relation_accuracy']:.3f} |",
        f"| answer relevance accuracy | {metrics['answer_relevance_accuracy']:.3f} |",
        f"| entity exact match | {metrics['entity_exact_match']:.3f} |",
        f"| entity average Jaccard | {metrics['entity_average_jaccard']:.3f} |",
        f"| entity average precision | {metrics['entity_average_precision']:.3f} |",
        f"| entity average recall | {metrics['entity_average_recall']:.3f} |",
        f"| entity average F1 | {metrics['entity_average_f1']:.3f} |",
        f"| zero entity overlap rows | {metrics['zero_entity_overlap_rows']} |",
        f"| strict full-row accuracy | {metrics['strict_full_row_accuracy']:.3f} |",
        f"| relaxed_1 | {metrics['relaxed_1']:.3f} |",
        f"| relaxed_2 | {metrics['relaxed_2']:.3f} |",
        f"| relaxed_3 | {metrics['relaxed_3']:.3f} |",
        "",
        "## Top Failure Patterns",
        "",
        "| failure pattern | rows |",
        "|---|---:|",
    ]
    for pattern, count in metrics["failure_counts"].most_common(15):
        lines.append(f"| {pattern} | {count} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "Combined v3 improves the role and entity lanes together, but strict full-row accuracy remains constrained by exact entity-set matching and downstream status/relevance/relation mismatches. Relaxed scores show more useful route signal than strict exact-match scoring.",
        "",
        "## Remaining Bottlenecks",
        "",
        "- Exact entity-set extraction remains brittle.",
        "- Derived status and answer relevance still introduce errors for background and limitation rows.",
        "- Relation accuracy follows role quality but still fails when fine role prediction fails.",
    ])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--role-col", required=True)
    parser.add_argument("--entities-col", required=True)
    parser.add_argument("--status-col", required=True)
    parser.add_argument("--relation-col", required=True)
    parser.add_argument("--answer-col", required=True)
    parser.add_argument("--mismatches-out", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    all_rows = read_rows(args.csv)
    rows = [row for row in all_rows if row.get("include_in_eval", "YES") in {"", "YES"}]
    metrics = evaluate(rows, args.role_col, args.entities_col, args.status_col, args.relation_col, args.answer_col)
    write_mismatches(args.mismatches_out, metrics["mismatch_rows"])
    write_markdown(args.out_md, len(all_rows), len(all_rows) - len(rows), metrics)

    print(f"Total rows: {len(all_rows)}")
    print(f"Evaluated rows: {metrics['evaluated_rows']}")
    print(f"Role accuracy: {metrics['role_accuracy']:.3f}")
    print(f"Operative status accuracy: {metrics['operative_status_accuracy']:.3f}")
    print(f"Relation accuracy: {metrics['relation_accuracy']:.3f}")
    print(f"Answer relevance accuracy: {metrics['answer_relevance_accuracy']:.3f}")
    print(f"Entity exact match: {metrics['entity_exact_match']:.3f}")
    print(f"Entity average Jaccard: {metrics['entity_average_jaccard']:.3f}")
    print(f"Entity average precision: {metrics['entity_average_precision']:.3f}")
    print(f"Entity average recall: {metrics['entity_average_recall']:.3f}")
    print(f"Entity average F1: {metrics['entity_average_f1']:.3f}")
    print(f"Zero entity overlap rows: {metrics['zero_entity_overlap_rows']}")
    print(f"Strict full-row accuracy: {metrics['strict_full_row_accuracy']:.3f}")
    print(f"Relaxed 1: {metrics['relaxed_1']:.3f}")
    print(f"Relaxed 2: {metrics['relaxed_2']:.3f}")
    print(f"Relaxed 3: {metrics['relaxed_3']:.3f}")
    print(f"Mismatches: {args.mismatches_out}")
    print(f"Markdown: {args.out_md}")


if __name__ == "__main__":
    main()
