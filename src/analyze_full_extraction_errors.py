import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


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

DETAIL_COLUMNS = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "pred_role",
    "role_failed",
    "gold_relation",
    "pred_relation",
    "relation_failed",
    "gold_operative_status",
    "pred_operative_status",
    "operative_status_failed",
    "gold_answer_relevant",
    "pred_answer_relevant",
    "answer_relevant_failed",
    "gold_entities",
    "pred_entities",
    "entity_jaccard",
    "entity_failed",
    "failure_pattern",
    "notes",
]


FIELD_PAIRS = [
    ("role", "gold_role", "pred_role"),
    ("operative_status", "gold_operative_status", "pred_operative_status"),
    ("relation", "gold_relation", "pred_relation"),
    ("answer_relevant", "gold_answer_relevant", "pred_answer_relevant"),
]


def split_entities(value):
    return {
        part.strip().lower()
        for part in (value or "").split(";")
        if part.strip()
    }


def display_entities(entities):
    return "; ".join(sorted(entities))


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def bool_text(value):
    return "1" if value else "0"


def failure_pattern(failed_fields):
    return "+".join(failed_fields) if failed_fields else "none"


def confusion(rows, gold_col, pred_col):
    matrix = defaultdict(Counter)
    for row in rows:
        matrix[(row.get(gold_col) or "").strip()][(row.get(pred_col) or "").strip()] += 1
    return matrix


def confusion_pairs(matrix):
    pairs = []
    for gold, pred_counts in matrix.items():
        for pred, count in pred_counts.items():
            if gold != pred:
                pairs.append((gold, pred, count))
    return sorted(pairs, key=lambda item: (-item[2], item[0], item[1]))


def matrix_markdown(title, matrix):
    lines = [f"## {title}", "", "| gold | pred | count |", "|---|---|---:|"]
    for gold in sorted(matrix):
        for pred, count in sorted(matrix[gold].items()):
            lines.append(f"| {gold or '(blank)'} | {pred or '(blank)'} | {count} |")
    lines.append("")
    return lines


def analyze(csv_path):
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    total = len(rows)
    correct = {name: 0 for name, _, _ in FIELD_PAIRS}
    exact_entities = 0
    partial_entities = 0
    zero_entities = 0
    jaccard_total = 0.0
    strict_correct = 0
    detail_rows = []
    missing_entities = Counter()
    extra_entities = Counter()
    pattern_counts = Counter()

    role_matrix = confusion(rows, "gold_role", "pred_role")
    relation_matrix = confusion(rows, "gold_relation", "pred_relation")
    status_matrix = confusion(rows, "gold_operative_status", "pred_operative_status")

    for row in rows:
        failures = []
        flags = {}
        for name, gold_col, pred_col in FIELD_PAIRS:
            failed = (row.get(gold_col) or "").strip() != (row.get(pred_col) or "").strip()
            flags[name] = failed
            if failed:
                failures.append(name)
            else:
                correct[name] += 1

        gold_entities = split_entities(row.get("gold_entities"))
        pred_entities = split_entities(row.get("pred_entities"))
        missing = gold_entities - pred_entities
        extra = pred_entities - gold_entities
        for entity in missing:
            missing_entities[entity] += 1
        for entity in extra:
            extra_entities[entity] += 1

        intersection = gold_entities & pred_entities
        union = gold_entities | pred_entities
        entity_jaccard = safe_div(len(intersection), len(union))
        jaccard_total += entity_jaccard
        entity_failed = gold_entities != pred_entities
        if entity_failed:
            failures.append("entity")
        if not entity_failed:
            exact_entities += 1
        elif intersection:
            partial_entities += 1
        else:
            zero_entities += 1

        pattern = failure_pattern(failures)
        pattern_counts[pattern] += 1
        if pattern == "none":
            strict_correct += 1

        detail_rows.append({
            "segment_id": row.get("segment_id", ""),
            "title": row.get("title", ""),
            "text": row.get("text", ""),
            "gold_role": row.get("gold_role", ""),
            "pred_role": row.get("pred_role", ""),
            "role_failed": bool_text(flags["role"]),
            "gold_relation": row.get("gold_relation", ""),
            "pred_relation": row.get("pred_relation", ""),
            "relation_failed": bool_text(flags["relation"]),
            "gold_operative_status": row.get("gold_operative_status", ""),
            "pred_operative_status": row.get("pred_operative_status", ""),
            "operative_status_failed": bool_text(flags["operative_status"]),
            "gold_answer_relevant": row.get("gold_answer_relevant", ""),
            "pred_answer_relevant": row.get("pred_answer_relevant", ""),
            "answer_relevant_failed": bool_text(flags["answer_relevant"]),
            "gold_entities": row.get("gold_entities", ""),
            "pred_entities": row.get("pred_entities", ""),
            "entity_jaccard": f"{entity_jaccard:.3f}",
            "entity_failed": bool_text(entity_failed),
            "failure_pattern": pattern,
            "notes": row.get("notes", ""),
        })

    metrics = {
        "total_rows": total,
        "role_accuracy": safe_div(correct["role"], total),
        "operative_status_accuracy": safe_div(correct["operative_status"], total),
        "relation_accuracy": safe_div(correct["relation"], total),
        "answer_relevance_accuracy": safe_div(correct["answer_relevant"], total),
        "entity_exact_match": safe_div(exact_entities, total),
        "entity_average_jaccard": safe_div(jaccard_total, total),
        "strict_full_row_accuracy": safe_div(strict_correct, total),
        "exact_entity_rows": exact_entities,
        "partial_entity_rows": partial_entities,
        "zero_entity_rows": zero_entities,
        "strict_mismatch_rows": total - strict_correct,
    }

    return {
        "rows": rows,
        "detail_rows": detail_rows,
        "metrics": metrics,
        "role_matrix": role_matrix,
        "relation_matrix": relation_matrix,
        "status_matrix": status_matrix,
        "role_pairs": confusion_pairs(role_matrix),
        "missing_entities": missing_entities,
        "extra_entities": extra_entities,
        "pattern_counts": pattern_counts,
    }


def write_detail_csv(path, detail_rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=DETAIL_COLUMNS)
        writer.writeheader()
        writer.writerows(detail_rows)


def example_rows(detail_rows, predicate, limit=10):
    return [row for row in detail_rows if predicate(row)][:limit]


def write_markdown(path, analysis):
    metrics = analysis["metrics"]
    detail_rows = analysis["detail_rows"]
    role_pairs = analysis["role_pairs"]
    missing_entities = analysis["missing_entities"]
    extra_entities = analysis["extra_entities"]
    pattern_counts = analysis["pattern_counts"]

    lines = [
        "# Held-Out Full Extraction Error Analysis",
        "",
        "## Executive Summary",
        "",
        f"- Total rows: {metrics['total_rows']}",
        f"- Role accuracy: {metrics['role_accuracy']:.3f}",
        f"- Operative status accuracy: {metrics['operative_status_accuracy']:.3f}",
        f"- Relation accuracy: {metrics['relation_accuracy']:.3f}",
        f"- Answer relevance accuracy: {metrics['answer_relevance_accuracy']:.3f}",
        f"- Entity exact match: {metrics['entity_exact_match']:.3f}",
        f"- Entity average Jaccard: {metrics['entity_average_jaccard']:.3f}",
        f"- Strict full-row accuracy: {metrics['strict_full_row_accuracy']:.3f}",
        f"- Strict mismatch rows: {metrics['strict_mismatch_rows']}",
        "",
        "## Biggest Bottlenecks",
        "",
        "- Role errors are the main upstream failure, especially overprediction of `CLAIM`.",
        "- Relation and operative-status errors often cascade from wrong role predictions.",
        "- Entity extraction has low exact match and many zero-overlap rows, showing that held-out entity wording is not covered by the current prediction heuristic.",
        "- Answer relevance is comparatively strong but still fails for background rows predicted as answer-bearing roles.",
        "",
    ]

    lines.extend(matrix_markdown("Role Confusion Matrix", analysis["role_matrix"]))

    lines.extend(["## Top Role Confusion Pairs", "", "| gold_role | pred_role | count |", "|---|---|---:|"])
    for gold, pred, count in role_pairs[:10]:
        lines.append(f"| {gold} | {pred} | {count} |")
    lines.append("")

    lines.extend(matrix_markdown("Relation Confusion Matrix", analysis["relation_matrix"]))
    lines.extend(matrix_markdown("Operative Status Confusion Matrix", analysis["status_matrix"]))

    lines.extend([
        "## Entity Diagnostics",
        "",
        f"- Rows with exact entity match: {metrics['exact_entity_rows']}",
        f"- Rows with partial entity overlap: {metrics['partial_entity_rows']}",
        f"- Rows with zero entity overlap: {metrics['zero_entity_rows']}",
        "",
        "### Most Common Missing Gold Entities",
        "",
        "| entity | count |",
        "|---|---:|",
    ])
    for entity, count in missing_entities.most_common(10):
        lines.append(f"| {entity} | {count} |")

    lines.extend(["", "### Most Common Extra Predicted Entities", "", "| entity | count |", "|---|---:|"])
    for entity, count in extra_entities.most_common(10):
        lines.append(f"| {entity} | {count} |")

    lines.extend(["", "## Strict Mismatch Clusters", "", "| failure_pattern | count |", "|---|---:|"])
    for pattern, count in pattern_counts.most_common(15):
        lines.append(f"| {pattern} | {count} |")

    lines.extend(["", "## Examples: Top Role Errors", "", "| segment_id | gold_role | pred_role | text |", "|---|---|---|---|"])
    for row in example_rows(detail_rows, lambda item: item["role_failed"] == "1"):
        text = " ".join(row["text"].split())[:160]
        lines.append(f"| {row['segment_id']} | {row['gold_role']} | {row['pred_role']} | {text} |")

    lines.extend(["", "## Examples: Top Entity Errors", "", "| segment_id | gold_entities | pred_entities | jaccard | text |", "|---|---|---|---:|---|"])
    for row in example_rows(detail_rows, lambda item: item["entity_failed"] == "1"):
        text = " ".join(row["text"].split())[:140]
        lines.append(f"| {row['segment_id']} | {row['gold_entities']} | {row['pred_entities']} | {row['entity_jaccard']} | {text} |")

    lines.extend([
        "",
        "## Recommended Next Improvement Order",
        "",
        "1. Improve semantic role coverage for held-out background, definition, result, and method wording without tuning directly to exact row strings.",
        "2. Add a richer entity recognizer for held-out concepts such as `route provenance`, `retrieval trace`, `permission boundary`, and release-review terms.",
        "3. Decouple relation prediction from role-only mapping so `supports_retrieval`, `maps_to`, and `requires` can be detected independently.",
        "4. Tighten answer relevance for background/context rows so source-context passages do not become `YES` when role prediction is wrong.",
        "5. Re-run this analysis after each change and keep a second held-out split untouched.",
        "",
    ])

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def print_console(analysis, out_md, out_csv):
    metrics = analysis["metrics"]
    print(f"Total rows: {metrics['total_rows']}")
    print(f"Role accuracy: {metrics['role_accuracy']:.3f}")
    print(f"Operative status accuracy: {metrics['operative_status_accuracy']:.3f}")
    print(f"Relation accuracy: {metrics['relation_accuracy']:.3f}")
    print(f"Answer relevance accuracy: {metrics['answer_relevance_accuracy']:.3f}")
    print(f"Entity exact match: {metrics['entity_exact_match']:.3f}")
    print(f"Entity average Jaccard: {metrics['entity_average_jaccard']:.3f}")
    print(f"Strict full-row accuracy: {metrics['strict_full_row_accuracy']:.3f}")
    print()

    print("Top 10 role confusion pairs:")
    for gold, pred, count in analysis["role_pairs"][:10]:
        print(f"- {gold} -> {pred}: {count}")
    print()

    print("Top 10 missing gold entities:")
    for entity, count in analysis["missing_entities"].most_common(10):
        print(f"- {entity}: {count}")
    print()

    print("Top 10 extra predicted entities:")
    for entity, count in analysis["extra_entities"].most_common(10):
        print(f"- {entity}: {count}")
    print()

    print("Top 10 failure patterns:")
    for pattern, count in analysis["pattern_counts"].most_common(10):
        print(f"- {pattern}: {count}")
    print()

    print(f"Markdown report: {out_md}")
    print(f"CSV report: {out_csv}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    analysis = analyze(args.csv)
    write_detail_csv(args.out_csv, analysis["detail_rows"])
    write_markdown(args.out_md, analysis)
    print_console(analysis, args.out_md, args.out_csv)


if __name__ == "__main__":
    main()
