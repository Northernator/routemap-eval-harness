"""Evaluate cached LLM roles + entities in real full-route predictions."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import evaluate_full_extraction_custom_cols as exact_eval
import evaluate_full_extraction_soft_entities as soft_eval
from build_llm_full_route_predictions import DATASETS, OUT_DIR, PRED_DIR, SUMMARY_PATH as BUILD_SUMMARY_PATH, variant_col
from entity_matchers_diagnostic import score_pair
from entity_ontology_v1 import split_entity_set
from role_taxonomies import ALLOWED_FINE_ROLES, map_role


REPORT_DIR = OUT_DIR / "reports"
MISMATCH_DIR = OUT_DIR / "mismatches"
REPORT_PATH = OUT_DIR / "LLM_FULL_ROUTE_REPORT.md"
SUMMARY_PATH = OUT_DIR / "SUMMARY.json"

PRIOR_REFERENCES = {
    "true_blind_original_relaxed_1": 0.000,
    "combined_v3_llm_entities_relaxed_1": 0.042,
    "combined_v3_llm_entities_relaxed_3": 0.125,
    "entity_only_ceiling": 0.181,
}

VARIANTS = {
    "ORIGINAL": {
        "role_col": "pred_role",
        "entities_col": "pred_entities",
        "status_col": "pred_operative_status",
        "relation_col": "pred_relation",
        "answer_col": "pred_answer_relevant",
        "route_mode": "real-route",
    },
    "ROLE_LLM_ONLY": {
        "role_col": variant_col("pred_role", "role_llm_only"),
        "entities_col": variant_col("pred_entities", "role_llm_only"),
        "status_col": variant_col("pred_operative_status", "role_llm_only"),
        "relation_col": variant_col("pred_relation", "role_llm_only"),
        "answer_col": variant_col("pred_answer_relevant", "role_llm_only"),
        "route_mode": "real-route",
    },
    "ENT_LLM_ONLY": {
        "role_col": variant_col("pred_role", "ent_llm_only"),
        "entities_col": variant_col("pred_entities", "ent_llm_only"),
        "status_col": variant_col("pred_operative_status", "ent_llm_only"),
        "relation_col": variant_col("pred_relation", "ent_llm_only"),
        "answer_col": variant_col("pred_answer_relevant", "ent_llm_only"),
        "route_mode": "real-route",
    },
    "FULL_LLM_adaptive": {
        "role_col": variant_col("pred_role", "full_llm_adaptive"),
        "entities_col": variant_col("pred_entities", "full_llm_adaptive"),
        "status_col": variant_col("pred_operative_status", "full_llm_adaptive"),
        "relation_col": variant_col("pred_relation", "full_llm_adaptive"),
        "answer_col": variant_col("pred_answer_relevant", "full_llm_adaptive"),
        "route_mode": "real-route",
    },
    "FULL_LLM_open": {
        "role_col": variant_col("pred_role", "full_llm_open"),
        "entities_col": variant_col("pred_entities", "full_llm_open"),
        "status_col": variant_col("pred_operative_status", "full_llm_open"),
        "relation_col": variant_col("pred_relation", "full_llm_open"),
        "answer_col": variant_col("pred_answer_relevant", "full_llm_open"),
        "route_mode": "real-route",
    },
    "DIAGNOSTIC_gold_other": {
        "role_col": variant_col("pred_role", "diagnostic_gold_other"),
        "entities_col": variant_col("pred_entities", "diagnostic_gold_other"),
        "status_col": variant_col("pred_operative_status", "diagnostic_gold_other"),
        "relation_col": variant_col("pred_relation", "diagnostic_gold_other"),
        "answer_col": variant_col("pred_answer_relevant", "diagnostic_gold_other"),
        "route_mode": "gold-other",
    },
}

PROGRESSION_ORDER = list(VARIANTS.keys())
ROLES = set(ALLOWED_FINE_ROLES)


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def eval_rows(path):
    rows = read_rows(path)
    return rows, [row for row in rows if row.get("include_in_eval", "YES") in {"", "YES"}]


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def safe_map_role(role, taxonomy):
    if role not in ROLES:
        return ""
    return map_role(role, taxonomy)


def row_role_acc(rows, role_col, taxonomy=None):
    correct = 0
    for row in rows:
        gold = row.get("gold_role", "")
        pred = row.get(role_col, "")
        if taxonomy:
            correct += int(safe_map_role(gold, taxonomy) == safe_map_role(pred, taxonomy) and safe_map_role(gold, taxonomy) != "")
        else:
            correct += int(gold == pred and pred in ROLES)
    return safe_div(correct, len(rows))


def frac_exact_j_ge_05(rows, entities_col):
    count = 0
    for row in rows:
        gold = split_entity_set(row.get("gold_entities", ""))
        pred = split_entity_set(row.get(entities_col, ""))
        count += int(exact_eval.entity_scores(gold, pred)["jaccard"] >= 0.5)
    return safe_div(count, len(rows))


def frac_softj_ge_05(rows, entities_col, matcher_name):
    _mode, threshold, similarity_fn, _status = soft_eval.entity_matcher(matcher_name)
    if similarity_fn is None:
        return None
    soft_eval.prepare_similarity(similarity_fn, rows, entities_col)
    count = 0
    for row in rows:
        scores = score_pair(
            soft_eval.parse_entity_cell(row.get("gold_entities", "")),
            soft_eval.parse_entity_cell(row.get(entities_col, "")),
            similarity_fn,
            threshold,
        )
        count += int(scores["soft_jaccard"] >= 0.5)
    return safe_div(count, len(rows))


def fallback_role_safe_copy(rows, role_col):
    copied_rows = []
    substitutions = 0
    fallback = next(iter(ALLOWED_FINE_ROLES))
    for row in rows:
        copied = dict(row)
        if copied.get(role_col, "") not in ROLES:
            gold = copied.get("gold_role", "")
            copied[role_col] = next((role for role in ALLOWED_FINE_ROLES if role != gold), fallback)
            substitutions += 1
        copied_rows.append(copied)
    return copied_rows, substitutions


def add_extra_metrics(metrics, rows, spec, mode, matcher=None):
    metrics = dict(metrics)
    metrics["role8_accuracy"] = row_role_acc(rows, spec["role_col"])
    metrics["role_coarse3_accuracy"] = row_role_acc(rows, spec["role_col"], "coarse_3")
    metrics["answer_accuracy"] = metrics.get("answer_relevance_accuracy", 0.0)
    if mode == "exact":
        metrics["frac_jaccard_ge_0_5"] = frac_exact_j_ge_05(rows, spec["entities_col"])
    else:
        metrics["frac_jaccard_ge_0_5"] = frac_softj_ge_05(rows, spec["entities_col"], matcher)
    return metrics


def run_exact(dataset, variant, csv_path, spec):
    all_rows, rows = eval_rows(csv_path)
    eval_safe_rows, role_substitutions = fallback_role_safe_copy(rows, spec["role_col"])
    metrics = exact_eval.evaluate(
        eval_safe_rows,
        spec["role_col"],
        spec["entities_col"],
        spec["status_col"],
        spec["relation_col"],
        spec["answer_col"],
    )
    metrics = add_extra_metrics(metrics, rows, spec, "exact")
    metrics["invalid_role_substitutions_for_eval"] = role_substitutions
    mismatch_path = MISMATCH_DIR / f"{dataset}__{variant}__exact_mismatches.csv"
    report_path = REPORT_DIR / f"{dataset}__{variant}__exact.md"
    exact_eval.write_mismatches(mismatch_path, metrics["mismatch_rows"])
    exact_eval.write_markdown(report_path, len(all_rows), len(all_rows) - len(rows), metrics)
    return metrics, rows


def run_soft(dataset, variant, csv_path, spec, matcher):
    all_rows, rows = eval_rows(csv_path)
    eval_safe_rows, role_substitutions = fallback_role_safe_copy(rows, spec["role_col"])
    metrics = soft_eval.evaluate(
        eval_safe_rows,
        spec["role_col"],
        spec["entities_col"],
        spec["status_col"],
        spec["relation_col"],
        spec["answer_col"],
        matcher,
    )
    metrics = add_extra_metrics(metrics, rows, spec, f"soft-{matcher}", matcher)
    metrics["invalid_role_substitutions_for_eval"] = role_substitutions
    mismatch_path = MISMATCH_DIR / f"{dataset}__{variant}__soft_{matcher}_mismatches.csv"
    report_path = REPORT_DIR / f"{dataset}__{variant}__soft_{matcher}.md"
    soft_eval.write_mismatches(mismatch_path, metrics["mismatch_rows"])
    soft_eval.write_markdown(report_path, len(all_rows), len(all_rows) - len(rows), metrics)
    return metrics, rows


def metric_row(dataset, variant, metric_mode, metrics, rows, spec):
    return {
        "dataset": dataset,
        "variant": variant,
        "route_mode": spec["route_mode"],
        "metric_mode": metric_mode,
        "entity_avg_jaccard": metrics.get("entity_average_softjaccard", metrics.get("entity_average_jaccard")),
        "strict": metrics.get("strict_full_row_accuracy"),
        "relaxed_1": metrics.get("relaxed_1"),
        "relaxed_2": metrics.get("relaxed_2"),
        "relaxed_3": metrics.get("relaxed_3"),
        "role8_accuracy": metrics.get("role8_accuracy"),
        "role_coarse3_accuracy": metrics.get("role_coarse3_accuracy"),
        "answer_accuracy": metrics.get("answer_accuracy"),
        "frac_jaccard_ge_0_5": metrics.get("frac_jaccard_ge_0_5"),
        "evaluated_rows": metrics.get("evaluated_rows", len(rows)),
        "entity_matcher_available": metrics.get("entity_matcher_available", True),
        "entity_matcher_reason": metrics.get("entity_matcher_reason", ""),
        "invalid_role_substitutions_for_eval": metrics.get("invalid_role_substitutions_for_eval", 0),
    }


def score_all():
    table_rows = []
    embeddings = {"available": None, "reason": ""}
    for dataset, dataset_spec in DATASETS.items():
        csv_path = dataset_spec["prediction"]
        if not csv_path.exists():
            raise SystemExit(f"Missing prediction file: {csv_path}. Run build_llm_full_route_predictions.py first.")
        for variant in PROGRESSION_ORDER:
            spec = VARIANTS[variant]
            exact_metrics, exact_rows = run_exact(dataset, variant, csv_path, spec)
            table_rows.append(metric_row(dataset, variant, "exact", exact_metrics, exact_rows, spec))
            for matcher in ["difflib", "embedding"]:
                soft_metrics, soft_rows = run_soft(dataset, variant, csv_path, spec, matcher)
                if matcher == "embedding":
                    embeddings = {
                        "available": soft_metrics.get("entity_matcher_available", False),
                        "reason": soft_metrics.get("entity_matcher_reason", ""),
                    }
                table_rows.append(metric_row(dataset, variant, f"soft-{matcher}", soft_metrics, soft_rows, spec))
    return table_rows, embeddings


def fmt(value):
    if value is None:
        return "NA"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (float, int)):
        return f"{value:.6f}"
    return str(value)


def markdown_table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def metric_value(row, key):
    value = row.get(key)
    return value if isinstance(value, (int, float)) else 0.0


def by_key(table_rows):
    return {(row["dataset"], row["variant"], row["metric_mode"]): row for row in table_rows}


def soft_embedding_rows(table_rows, dataset=None):
    rows = [row for row in table_rows if row["metric_mode"] == "soft-embedding"]
    if dataset:
        rows = [row for row in rows if row["dataset"] == dataset]
    return rows


def best_full_llm_row(table_rows, key):
    candidates = [
        row
        for row in soft_embedding_rows(table_rows)
        if row["dataset"].startswith("true_blind") and row["variant"] in {"FULL_LLM_adaptive", "FULL_LLM_open"}
    ]
    return max(candidates, key=lambda row: metric_value(row, key))


def background_to_claim_count():
    cache_path = DATASETS["true_blind_combined_v3"]["role_cache"]
    source_path = DATASETS["true_blind_combined_v3"]["source"]
    cache = {}
    with Path(cache_path).open("r", encoding="utf-8-sig") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            cache[row.get("segment_id", "")] = row
    count = 0
    total_background = 0
    for row in read_rows(source_path):
        if row.get("gold_role", "") != "BACKGROUND":
            continue
        total_background += 1
        pred = str(cache.get(row.get("segment_id", ""), {}).get("pred_role", "")).strip().upper()
        count += int(pred == "CLAIM")
    return {"count": count, "gold_background_rows": total_background}


def build_verdicts(table_rows):
    lookup = by_key(table_rows)
    tb_best_r1 = best_full_llm_row(table_rows, "relaxed_1")
    tb_best_r3 = best_full_llm_row(table_rows, "relaxed_3")
    ceiling = PRIOR_REFERENCES["entity_only_ceiling"]
    role_contrib_by_dataset = {}
    for dataset in ["true_blind_combined_v3", "true_blind_R6"]:
        original = lookup[(dataset, "ORIGINAL", "soft-embedding")]
        role_only = lookup[(dataset, "ROLE_LLM_ONLY", "soft-embedding")]
        role_contrib_by_dataset[dataset] = metric_value(role_only, "relaxed_3") - metric_value(original, "relaxed_3")
    dev_adaptive = lookup[("dev", "FULL_LLM_adaptive", "soft-embedding")]
    dev_original = lookup[("dev", "ORIGINAL", "soft-embedding")]
    b2c = background_to_claim_count()
    return {
        "full_llm_relaxed1_beats_prior": metric_value(tb_best_r1, "relaxed_1")
        > PRIOR_REFERENCES["combined_v3_llm_entities_relaxed_1"],
        "full_llm_relaxed3_value": metric_value(tb_best_r3, "relaxed_3"),
        "full_llm_relaxed3_dataset": tb_best_r3["dataset"],
        "full_llm_relaxed3_variant": tb_best_r3["variant"],
        "approaches_entity_ceiling": metric_value(tb_best_r3, "relaxed_3") >= 0.8 * ceiling,
        "role_llm_contribution": role_contrib_by_dataset["true_blind_combined_v3"],
        "role_llm_contribution_by_dataset": role_contrib_by_dataset,
        "indomain_no_regression": metric_value(dev_adaptive, "relaxed_1") >= metric_value(dev_original, "relaxed_1") - 0.02,
        "background_to_claim_count": b2c["count"],
        "background_gold_rows": b2c["gold_background_rows"],
        "best_true_blind_full_llm_relaxed1": {
            "dataset": tb_best_r1["dataset"],
            "variant": tb_best_r1["variant"],
            "relaxed_1": tb_best_r1["relaxed_1"],
            "relaxed_3": tb_best_r1["relaxed_3"],
        },
    }


def recommendation(verdicts):
    if verdicts["full_llm_relaxed1_beats_prior"] and verdicts["indomain_no_regression"]:
        lock = "FULL_LLM_adaptive is the best-rounded lock candidate; keep FULL_LLM_open as an out-of-domain comparison lane."
    else:
        lock = "Do not lock the combined LLM RouteMap as the sole configuration yet."
    if verdicts["approaches_entity_ceiling"]:
        binding = "The new binding constraint is entity row quality/coverage rather than role taxonomy."
    else:
        binding = "The run still sits below the entity-only ceiling, so entity coverage plus residual route fields remain binding."
    return f"{lock} Fresh blind split is warranted for a clean headline after this diagnostic read. {binding}"


def write_report(summary):
    columns = [
        "variant",
        "metric_mode",
        "entity_avg_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
        "role8_accuracy",
        "role_coarse3_accuracy",
        "answer_accuracy",
        "frac_jaccard_ge_0_5",
    ]
    lines = [
        "# LLM_FULL_ROUTE_REPORT",
        "",
        "Offline diagnostic read. Cached LLM role and entity outputs are reused; no provider calls are made.",
        "",
        "## Prior reference points",
        "",
        markdown_table([PRIOR_REFERENCES], list(PRIOR_REFERENCES.keys())),
    ]
    for dataset in DATASETS:
        rows = [row for row in summary["table_rows"] if row["dataset"] == dataset]
        lines.extend(["", f"## {dataset}", "", markdown_table(rows, columns)])
    lines.extend(
        [
            "",
            "## Verdicts",
            "",
            "```json",
            json.dumps(summary["verdicts"], indent=2, sort_keys=True),
            "```",
            "",
            "## Recommendation",
            "",
            summary["recommendation"],
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def print_progression(table_rows, dataset):
    columns = [
        "variant",
        "entity_avg_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
        "role8_accuracy",
        "role_coarse3_accuracy",
        "answer_accuracy",
        "frac_jaccard_ge_0_5",
    ]
    rows = sorted(
        soft_embedding_rows(table_rows, dataset),
        key=lambda row: PROGRESSION_ORDER.index(row["variant"]),
    )
    print(f"\n{dataset} soft-embedding progression")
    print(markdown_table(rows, columns))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)
    table_rows, embeddings = score_all()
    build_summary = {}
    if BUILD_SUMMARY_PATH.exists():
        build_summary = json.loads(BUILD_SUMMARY_PATH.read_text(encoding="utf-8"))
    verdicts = build_verdicts(table_rows)
    summary = {
        "experiment": "llm_full_route_eval",
        "offline": True,
        "prior_references": PRIOR_REFERENCES,
        "build_summary": build_summary,
        "embeddings": embeddings,
        "table_rows": table_rows,
        "verdicts": verdicts,
        "recommendation": recommendation(verdicts),
        "outputs": {
            "report": str(REPORT_PATH),
            "summary": str(SUMMARY_PATH),
            "predictions": str(PRED_DIR),
            "reports": str(REPORT_DIR),
            "mismatches": str(MISMATCH_DIR),
        },
    }
    write_report(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("llm_full_route_eval")
    print(f"embeddings_available={embeddings['available']} reason={embeddings['reason']}")
    for dataset in ["true_blind_combined_v3", "true_blind_R6", "dev"]:
        print_progression(table_rows, dataset)
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
