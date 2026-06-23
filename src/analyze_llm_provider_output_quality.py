import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from entity_ontology_v1 import split_entity_set


def read_csv(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def read_jsonl(path):
    rows = []
    with Path(path).open("r", encoding="utf-8-sig") as source:
        for line_number, line in enumerate(source, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append((line_number, json.loads(line)))
            except json.JSONDecodeError as exc:
                rows.append((line_number, {"_parse_error": str(exc), "_raw_line": line}))
    return rows


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def preview(value, limit=260):
    text = " ".join(str(value or "").split())
    return text[:limit]


def parse_raw_response(record):
    raw = record.get("raw_response", "")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def output_shape_stats(output_rows):
    stats = Counter()
    raw_lengths = []
    error_rows = []
    empty_fields = Counter()
    for line_number, record in output_rows:
        if "_parse_error" in record:
            stats["unparseable_jsonl_lines"] += 1
            continue
        extraction = record.get("extraction")
        raw = record.get("raw_response")
        if isinstance(extraction, dict):
            stats["extraction_object"] += 1
            for field in ["role", "entities", "operative_status", "relation", "answer_relevant"]:
                value = extraction.get(field)
                if value in ("", None, []) or value == {}:
                    empty_fields[field] += 1
        if raw is not None:
            stats["raw_response"] += 1
            raw_lengths.append(len(str(raw)))
            parsed = parse_raw_response(record)
            if isinstance(parsed, dict) and "error" in parsed:
                stats["raw_response_error_json"] += 1
                error_rows.append((record.get("segment_id", ""), parsed.get("error", "")))
        if not isinstance(extraction, dict) and raw is None:
            stats["missing_extraction_and_raw"] += 1
    return {
        "stats": stats,
        "average_raw_length": safe_div(sum(raw_lengths), len(raw_lengths)),
        "empty_fields": empty_fields,
        "error_rows": error_rows,
    }


def confusion(rows, gold_col, pred_col):
    matrix = defaultdict(Counter)
    for row in rows:
        matrix[row.get(gold_col, "")][row.get(pred_col, "")] += 1
    return matrix


def top_confusions(rows, gold_col, pred_col):
    counter = Counter()
    for row in rows:
        gold = row.get(gold_col, "")
        pred = row.get(pred_col, "")
        if gold != pred:
            counter[(gold, pred)] += 1
    return counter


def split_entities(value):
    return split_entity_set(value)


def entity_overlap(gold_value, pred_value):
    gold = split_entities(gold_value)
    pred = split_entities(pred_value)
    return safe_div(len(gold & pred), len(gold | pred))


def entity_stats(pred_rows, eval_rows):
    empty_pred = 0
    pred_counts = []
    gold_counts = []
    pred_entity_counts = Counter()
    gold_entity_counts = Counter()
    gold_nonempty_pred_empty = []
    pred_nonempty_zero_overlap = []
    noncanonical = Counter()
    canonical_gold = set()
    for row in pred_rows:
        gold = split_entities(row.get("gold_entities", ""))
        canonical_gold.update(gold)
    for row in pred_rows:
        pred_raw = row.get("pred_entities", "")
        pred = split_entities(pred_raw)
        gold = split_entities(row.get("gold_entities", ""))
        if not pred:
            empty_pred += 1
        pred_counts.append(len(pred))
        gold_counts.append(len(gold))
        pred_entity_counts.update(pred)
        gold_entity_counts.update(gold)
        if gold and not pred:
            gold_nonempty_pred_empty.append(row)
        if pred and not (gold & pred):
            pred_nonempty_zero_overlap.append(row)
        for part in [part.strip() for part in pred_raw.split(";") if part.strip()]:
            if part not in canonical_gold and part.lower() not in {entity.lower() for entity in canonical_gold}:
                noncanonical[part] += 1
    zero_overlap_eval = [row for row in eval_rows if float(row.get("entity_jaccard", "0") or 0) == 0.0]
    return {
        "empty_pred": empty_pred,
        "average_pred_count": safe_div(sum(pred_counts), len(pred_counts)),
        "average_gold_count": safe_div(sum(gold_counts), len(gold_counts)),
        "top_predicted": pred_entity_counts,
        "top_gold": gold_entity_counts,
        "gold_nonempty_pred_empty": gold_nonempty_pred_empty,
        "pred_nonempty_zero_overlap": pred_nonempty_zero_overlap,
        "zero_overlap_eval": zero_overlap_eval,
        "noncanonical": noncanonical,
    }


def role_collapse(pred_counts, total):
    if not pred_counts:
        return "No predicted roles found."
    top = pred_counts.most_common(2)
    top_share = safe_div(sum(count for _, count in top), total)
    if len(top) == 1 or top_share >= 0.80:
        return f"Likely role collapse: top {len(top)} role(s) cover {top_share:.3f} of predictions."
    return f"No severe one/two-role collapse detected: top two roles cover {top_share:.3f}."


def raw_preview_by_segment(output_rows):
    result = {}
    for _, record in output_rows:
        segment_id = record.get("segment_id", "")
        if not segment_id:
            continue
        if "raw_response" in record:
            result[segment_id] = preview(record.get("raw_response", ""))
        elif "extraction" in record:
            result[segment_id] = preview(json.dumps(record.get("extraction", {}), ensure_ascii=False))
        else:
            result[segment_id] = preview(record)
    return result


def failure_rows(pred_rows, eval_rows, raw_preview):
    eval_by_segment = {row["segment_id"]: row for row in eval_rows}
    rows = []
    for row in pred_rows:
        eval_row = eval_by_segment.get(row["segment_id"], {})
        entity_j = eval_row.get("entity_jaccard", f"{entity_overlap(row.get('gold_entities'), row.get('pred_entities')):.6f}")
        rows.append({
            "segment_id": row.get("segment_id", ""),
            "gold_role": row.get("gold_role", ""),
            "pred_role": row.get("pred_role", ""),
            "gold_entities": row.get("gold_entities", ""),
            "pred_entities": row.get("pred_entities", ""),
            "entity_jaccard": entity_j,
            "gold_relation": row.get("gold_relation", ""),
            "pred_relation": row.get("pred_relation", ""),
            "gold_status": row.get("gold_operative_status", ""),
            "pred_status": row.get("pred_operative_status", ""),
            "gold_answer_relevant": row.get("gold_answer_relevant", ""),
            "pred_answer_relevant": row.get("pred_answer_relevant", ""),
            "raw_or_rationale_preview": raw_preview.get(row.get("segment_id", ""), row.get("pred_rationale", "")),
            "failure_pattern": eval_row.get("failure_pattern", ""),
            "text": row.get("text", ""),
        })
    return rows


def write_csv(path, rows):
    fieldnames = [
        "segment_id",
        "gold_role",
        "pred_role",
        "gold_entities",
        "pred_entities",
        "entity_jaccard",
        "gold_relation",
        "pred_relation",
        "gold_status",
        "pred_status",
        "gold_answer_relevant",
        "pred_answer_relevant",
        "raw_or_rationale_preview",
        "failure_pattern",
        "text",
    ]
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def matrix_lines(matrix, gold_labels):
    pred_labels = sorted({pred for counts in matrix.values() for pred in counts})
    lines = ["| gold \\ pred | " + " | ".join(pred_labels) + " |", "|---" + "|---:" * len(pred_labels) + "|"]
    for gold in gold_labels:
        lines.append("| " + gold + " | " + " | ".join(str(matrix[gold][pred]) for pred in pred_labels) + " |")
    return lines


def write_markdown(path, pred_rows, eval_rows, output_stats, e_stats, diag_rows):
    gold_role_counts = Counter(row.get("gold_role", "") for row in pred_rows)
    pred_role_counts = Counter(row.get("pred_role", "") for row in pred_rows)
    role_matrix = confusion(pred_rows, "gold_role", "pred_role")
    role_confusions = top_confusions(pred_rows, "gold_role", "pred_role")
    status_matrix = confusion(pred_rows, "gold_operative_status", "pred_operative_status")
    relation_matrix = confusion(pred_rows, "gold_relation", "pred_relation")
    relevance_matrix = confusion(pred_rows, "gold_answer_relevant", "pred_answer_relevant")
    error_rows = output_stats["error_rows"]
    likely_cause = (
        "Provider calls appear to have failed before semantic extraction: raw_response values contain connection-refused error JSON, "
        "then ingestion normalized missing extraction fields into default BACKGROUND/DESCRIPTIVE/sets_context/MAYBE with empty entities."
        if error_rows else
        "Outputs are valid but low quality; inspect role/entity collapse and prompt compliance before changing prompts."
    )

    lines = [
        "# Ollama llama3.1 Full Output Diagnostics",
        "",
        "## Executive Summary",
        "",
        f"- Total predictions: {len(pred_rows)}",
        f"- Total raw output records: {sum(output_stats['stats'].values()) if output_stats['stats'] else len(pred_rows)}",
        f"- Empty predicted entity rows: {e_stats['empty_pred']}",
        f"- Average predicted entities per row: {e_stats['average_pred_count']:.3f}",
        f"- Average gold entities per row: {e_stats['average_gold_count']:.3f}",
        f"- {role_collapse(pred_role_counts, len(pred_rows))}",
        f"- Likely failure cause: {likely_cause}",
        "",
        "## Output-Level Diagnostics",
        "",
        "| metric | value |",
        "|---|---:|",
        f"| total outputs | {len(pred_rows)} |",
        f"| extraction object count | {output_stats['stats']['extraction_object']} |",
        f"| raw_response count | {output_stats['stats']['raw_response']} |",
        f"| raw_response error JSON count | {output_stats['stats']['raw_response_error_json']} |",
        f"| average raw response length | {output_stats['average_raw_length']:.1f} |",
    ]
    for field, count in output_stats["empty_fields"].most_common():
        lines.append(f"| empty extraction field `{field}` | {count} |")
    lines.extend(["", "## Role Diagnostics", "", "### Gold Role Counts", "", "| role | count |", "|---|---:|"])
    for role, count in gold_role_counts.most_common():
        lines.append(f"| {role} | {count} |")
    lines.extend(["", "### Predicted Role Counts", "", "| role | count |", "|---|---:|"])
    for role, count in pred_role_counts.most_common():
        lines.append(f"| {role} | {count} |")
    lines.extend(["", "### Role Confusion Matrix", ""])
    lines.extend(matrix_lines(role_matrix, sorted(gold_role_counts)))
    lines.extend(["", "### Top Role Confusions", "", "| gold | pred | count |", "|---|---|---:|"])
    for (gold, pred), count in role_confusions.most_common(15):
        lines.append(f"| {gold} | {pred} | {count} |")
    lines.extend(["", "## Entity Diagnostics", "", "| metric | value |", "|---|---:|"])
    lines.extend([
        f"| rows with empty pred_entities | {e_stats['empty_pred']} |",
        f"| average predicted entities per row | {e_stats['average_pred_count']:.3f} |",
        f"| average gold entities per row | {e_stats['average_gold_count']:.3f} |",
        f"| gold non-empty but pred empty | {len(e_stats['gold_nonempty_pred_empty'])} |",
        f"| pred non-empty zero overlap | {len(e_stats['pred_nonempty_zero_overlap'])} |",
        f"| eval zero-overlap rows | {len(e_stats['zero_overlap_eval'])} |",
        f"| non-canonical predicted strings | {sum(e_stats['noncanonical'].values())} |",
    ])
    lines.extend(["", "### Top Predicted Entity Strings", "", "| entity | count |", "|---|---:|"])
    for entity, count in e_stats["top_predicted"].most_common(15):
        lines.append(f"| {entity} | {count} |")
    lines.extend(["", "### Top Gold Entity Strings", "", "| entity | count |", "|---|---:|"])
    for entity, count in e_stats["top_gold"].most_common(15):
        lines.append(f"| {entity} | {count} |")
    lines.extend(["", "## Status Diagnostics", ""])
    lines.extend(matrix_lines(status_matrix, sorted({row.get("gold_operative_status", "") for row in pred_rows})))
    lines.extend(["", "## Relation Diagnostics", ""])
    lines.extend(matrix_lines(relation_matrix, sorted({row.get("gold_relation", "") for row in pred_rows})))
    lines.extend(["", "## Answer Relevance Diagnostics", ""])
    lines.extend(matrix_lines(relevance_matrix, sorted({row.get("gold_answer_relevant", "") for row in pred_rows})))
    worst = sorted(diag_rows, key=lambda row: (float(row["entity_jaccard"]), row["gold_role"] == row["pred_role"], row["segment_id"]))
    lines.extend(["", "## 10 Worst Examples", "", "| segment_id | gold_role | pred_role | entity_j | failure | preview |", "|---|---|---|---:|---|---|"])
    for row in worst[:10]:
        lines.append(f"| {row['segment_id']} | {row['gold_role']} | {row['pred_role']} | {float(row['entity_jaccard']):.3f} | {row['failure_pattern']} | {preview(row['text'], 120)} |")
    role_correct_entities_failed = [row for row in diag_rows if row["gold_role"] == row["pred_role"] and float(row["entity_jaccard"]) == 0.0]
    lines.extend(["", "## 10 Examples Where Role Was Correct But Entities Failed", "", "| segment_id | role | gold_entities | pred_entities |", "|---|---|---|---|"])
    for row in role_correct_entities_failed[:10]:
        lines.append(f"| {row['segment_id']} | {row['gold_role']} | {row['gold_entities']} | {row['pred_entities']} |")
    empty_entities = [row for row in diag_rows if not row["pred_entities"].strip()]
    lines.extend(["", "## 10 Examples Where Entities Were Empty", "", "| segment_id | gold_entities | raw_or_rationale_preview |", "|---|---|---|"])
    for row in empty_entities[:10]:
        lines.append(f"| {row['segment_id']} | {row['gold_entities']} | {row['raw_or_rationale_preview']} |")
    lines.extend([
        "",
        "## Recommendation For Prompt V2",
        "",
        "Do not change the prompt yet if the saved run consists of connection-refused raw responses. First rerun only after confirming Ollama is reachable and the runner records actual model text. Then validate whether raw model JSON contains canonical entity labels. If actual model text still omits entities, prompt v2 should require at least 1-5 canonical entities selected from the ontology when supported by passage text, and should include a negative instruction not to return an empty entity list unless no ontology concept is present.",
    ])
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--eval-rows", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    args = parser.parse_args()

    output_rows = read_jsonl(args.outputs)
    pred_rows = read_csv(args.predictions)
    eval_rows = read_csv(args.eval_rows)
    output_stats = output_shape_stats(output_rows)
    e_stats = entity_stats(pred_rows, eval_rows)
    raw_preview = raw_preview_by_segment(output_rows)
    diag_rows = failure_rows(pred_rows, eval_rows, raw_preview)
    write_csv(args.out_csv, diag_rows)
    write_markdown(args.out_md, pred_rows, eval_rows, output_stats, e_stats, diag_rows)

    pred_role_counts = Counter(row.get("pred_role", "") for row in pred_rows)
    role_confusions = top_confusions(pred_rows, "gold_role", "pred_role")
    likely_cause = (
        "Provider call failure: raw_response contains connection-refused error JSON, normalized into default extraction with empty entities."
        if output_stats["error_rows"] else
        "Semantic/provider formatting failure; inspect raw responses for prompt compliance and canonical entity use."
    )
    print("Predicted role distribution:")
    for role, count in pred_role_counts.most_common():
        print(f"- {role}: {count}")
    print(f"Empty pred_entities count: {e_stats['empty_pred']}")
    print(f"Average predicted entity count: {e_stats['average_pred_count']:.3f}")
    print("Top predicted entity strings:")
    for entity, count in e_stats["top_predicted"].most_common(10):
        print(f"- {entity}: {count}")
    print("Top gold entity strings:")
    for entity, count in e_stats["top_gold"].most_common(10):
        print(f"- {entity}: {count}")
    print("Top role confusions:")
    for (gold, pred), count in role_confusions.most_common(10):
        print(f"- {gold} -> {pred}: {count}")
    print(f"Likely failure cause: {likely_cause}")
    print(f"Markdown: {args.out_md}")
    print(f"CSV: {args.out_csv}")


if __name__ == "__main__":
    main()
