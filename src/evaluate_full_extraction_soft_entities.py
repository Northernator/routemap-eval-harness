"""Full-extraction evaluator with soft entity matching only.

Role/status/relation/answer/coarse logic is imported from the custom-cols
evaluator. Only entity scoring is replaced by greedy soft matching.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from entity_matchers_diagnostic import (
    EmbeddingMatcher,
    difflib_similarity,
    score_pair,
    safe_div,
)
from evaluate_full_extraction_custom_cols import failure_pattern, map_role, read_rows


_EMBEDDING_MATCHER = None
_EMBEDDING_CACHE = {}


def parse_entity_cell(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    delimiter = ";" if ";" in text else ","
    return [part.strip() for part in text.split(delimiter) if part.strip()]


def entity_matcher(entity_matcher_name):
    if entity_matcher_name == "difflib":
        return "soft_difflib", 0.6, difflib_similarity, {"available": True, "reason": "difflib stdlib"}
    if entity_matcher_name == "embedding":
        global _EMBEDDING_MATCHER
        if _EMBEDDING_MATCHER is None:
            _EMBEDDING_MATCHER = EmbeddingMatcher.load()
        matcher = _EMBEDDING_MATCHER
        if not matcher.available:
            return "soft_embedding", 0.5, None, {"available": False, "reason": matcher.reason}

        def cached_similarity(left, right):
            key = (left, right)
            if key not in _EMBEDDING_CACHE:
                _EMBEDDING_CACHE[key] = matcher.similarity(left, right)
            return _EMBEDDING_CACHE[key]

        cached_similarity.prepare_values = matcher.prepare
        return "soft_embedding", 0.5, cached_similarity, {"available": True, "reason": matcher.reason}
    raise ValueError(f"unknown entity matcher: {entity_matcher_name}")


def prepare_similarity(similarity_fn, rows, entities_col):
    if not hasattr(similarity_fn, "prepare_values"):
        return
    values = []
    for row in rows:
        values.extend(parse_entity_cell(row.get("gold_entities", "")))
        values.extend(parse_entity_cell(row.get(entities_col, "")))
    similarity_fn.prepare_values(values)


def soft_entity_scores(gold_values, pred_values, similarity_fn, threshold):
    scores = score_pair(gold_values, pred_values, similarity_fn, threshold)
    return {
        "exact": scores["soft_jaccard"] == 1.0,
        "jaccard": scores["soft_jaccard"],
        "precision": scores["soft_precision"],
        "recall": scores["soft_recall"],
        "f1": scores["soft_f1"],
        "zero_overlap": scores["matches"] == 0,
        "matches": scores["matches"],
        "matched_pairs": scores["matched_pairs"],
    }


def evaluate(rows, role_col, entities_col, status_col, relation_col, answer_col, matcher_name):
    mode, threshold, similarity_fn, matcher_status = entity_matcher(matcher_name)
    if similarity_fn is None:
        return {
            "evaluated_rows": len(rows),
            "entity_matcher_mode": mode,
            "entity_matcher_available": False,
            "entity_matcher_reason": matcher_status["reason"],
            "mismatch_rows": [],
            "failure_counts": Counter(),
        }
    prepare_similarity(similarity_fn, rows, entities_col)
    counts = Counter()
    failure_counts = Counter()
    mismatch_rows = []
    for row in rows:
        gold_entities = parse_entity_cell(row.get("gold_entities", ""))
        pred_entities = parse_entity_cell(row.get(entities_col, ""))
        entity = soft_entity_scores(gold_entities, pred_entities, similarity_fn, threshold)
        role_ok = row.get("gold_role") == row.get(role_col)
        status_ok = row.get("gold_operative_status") == row.get(status_col)
        relation_ok = row.get("gold_relation") == row.get(relation_col)
        answer_ok = row.get("gold_answer_relevant") == row.get(answer_col)
        coarse_4_ok = map_role(row.get("gold_role", ""), "coarse_4") == map_role(row.get(role_col, ""), "coarse_4")
        coarse_3_ok = map_role(row.get("gold_role", ""), "coarse_3") == map_role(row.get(role_col, ""), "coarse_3")
        strict_ok = role_ok and status_ok and relation_ok and answer_ok and entity["exact"]
        relaxed_1_ok = role_ok and answer_ok and entity["jaccard"] >= 0.5
        relaxed_2_ok = coarse_4_ok and answer_ok and entity["jaccard"] >= 0.5
        relaxed_3_ok = coarse_3_ok and answer_ok and entity["jaccard"] >= 0.5
        counts["role"] += int(role_ok)
        counts["status"] += int(status_ok)
        counts["relation"] += int(relation_ok)
        counts["answer"] += int(answer_ok)
        counts["entity_exact"] += int(entity["exact"])
        counts["entity_zero_overlap"] += int(entity["zero_overlap"])
        counts["strict"] += int(strict_ok)
        counts["relaxed_1"] += int(relaxed_1_ok)
        counts["relaxed_2"] += int(relaxed_2_ok)
        counts["relaxed_3"] += int(relaxed_3_ok)
        counts["entity_jaccard"] += entity["jaccard"]
        counts["entity_precision"] += entity["precision"]
        counts["entity_recall"] += entity["recall"]
        counts["entity_f1"] += entity["f1"]
        pattern = failure_pattern(role_ok, status_ok, relation_ok, answer_ok, entity["exact"], entity["jaccard"])
        if pattern != "none":
            failure_counts[pattern] += 1
            mismatch_rows.append(
                {
                    "segment_id": row.get("segment_id", ""),
                    "title": row.get("title", ""),
                    "text": row.get("text") or row.get("segment_text", ""),
                    "gold_role": row.get("gold_role", ""),
                    "pred_role": row.get(role_col, ""),
                    "gold_entities": json.dumps(gold_entities, ensure_ascii=False),
                    "pred_entities": json.dumps(pred_entities, ensure_ascii=False),
                    "entity_jaccard": f"{entity['jaccard']:.6f}",
                    "entity_precision": f"{entity['precision']:.6f}",
                    "entity_recall": f"{entity['recall']:.6f}",
                    "entity_f1": f"{entity['f1']:.6f}",
                    "matched_pairs": json.dumps(entity["matched_pairs"], ensure_ascii=False),
                    "gold_operative_status": row.get("gold_operative_status", ""),
                    "pred_operative_status": row.get(status_col, ""),
                    "gold_relation": row.get("gold_relation", ""),
                    "pred_relation": row.get(relation_col, ""),
                    "gold_answer_relevant": row.get("gold_answer_relevant", ""),
                    "pred_answer_relevant": row.get(answer_col, ""),
                    "failure_pattern": pattern,
                }
            )
    total = len(rows)
    return {
        "evaluated_rows": total,
        "entity_matcher_mode": mode,
        "entity_matcher_available": True,
        "entity_matcher_reason": matcher_status["reason"],
        "role_accuracy": safe_div(counts["role"], total),
        "operative_status_accuracy": safe_div(counts["status"], total),
        "relation_accuracy": safe_div(counts["relation"], total),
        "answer_relevance_accuracy": safe_div(counts["answer"], total),
        "entity_exact_match": safe_div(counts["entity_exact"], total),
        "entity_average_jaccard": safe_div(counts["entity_jaccard"], total),
        "entity_average_softjaccard": safe_div(counts["entity_jaccard"], total),
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
        "entity_precision",
        "entity_recall",
        "entity_f1",
        "matched_pairs",
        "gold_operative_status",
        "pred_operative_status",
        "gold_relation",
        "pred_relation",
        "gold_answer_relevant",
        "pred_answer_relevant",
        "failure_pattern",
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path, total_rows, excluded_rows, metrics):
    lines = [
        "# Full Extraction Soft-Entity Evaluation",
        "",
        f"| total rows | {total_rows} |",
        f"| excluded rows | {excluded_rows} |",
        f"| evaluated rows | {metrics['evaluated_rows']} |",
        f"| entity matcher | {metrics['entity_matcher_mode']} |",
        f"| role accuracy | {metrics.get('role_accuracy', 0.0):.3f} |",
        f"| entity average soft Jaccard | {metrics.get('entity_average_softjaccard', 0.0):.3f} |",
        f"| strict full-row accuracy | {metrics.get('strict_full_row_accuracy', 0.0):.3f} |",
        f"| relaxed_1 | {metrics.get('relaxed_1', 0.0):.3f} |",
        f"| relaxed_2 | {metrics.get('relaxed_2', 0.0):.3f} |",
        f"| relaxed_3 | {metrics.get('relaxed_3', 0.0):.3f} |",
        "",
        "## Top Failure Patterns",
        "",
        "| failure pattern | rows |",
        "|---|---:|",
    ]
    for pattern, count in metrics.get("failure_counts", Counter()).most_common(15):
        lines.append(f"| {pattern} | {count} |")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
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
    parser.add_argument("--entity-matcher", choices=["difflib", "embedding"], required=True)
    args = parser.parse_args()
    all_rows = read_rows(args.csv)
    rows = [row for row in all_rows if row.get("include_in_eval", "YES") in {"", "YES"}]
    metrics = evaluate(
        rows,
        args.role_col,
        args.entities_col,
        args.status_col,
        args.relation_col,
        args.answer_col,
        args.entity_matcher,
    )
    write_mismatches(args.mismatches_out, metrics["mismatch_rows"])
    write_markdown(args.out_md, len(all_rows), len(all_rows) - len(rows), metrics)
    print(f"Total rows: {len(all_rows)}")
    print(f"Evaluated rows: {metrics['evaluated_rows']}")
    print(f"Entity matcher: {metrics['entity_matcher_mode']} available={metrics['entity_matcher_available']}")
    print(f"Role accuracy: {metrics.get('role_accuracy', 0.0):.3f}")
    print(f"Entity average soft Jaccard: {metrics.get('entity_average_softjaccard', 0.0):.3f}")
    print(f"Strict full-row accuracy: {metrics.get('strict_full_row_accuracy', 0.0):.3f}")
    print(f"Relaxed 1: {metrics.get('relaxed_1', 0.0):.3f}")
    print(f"Relaxed 2: {metrics.get('relaxed_2', 0.0):.3f}")
    print(f"Relaxed 3: {metrics.get('relaxed_3', 0.0):.3f}")
    print(f"Mismatches: {args.mismatches_out}")
    print(f"Markdown: {args.out_md}")


if __name__ == "__main__":
    main()
