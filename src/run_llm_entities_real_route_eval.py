"""Evaluate cached LLM entities with real RouteMap route fields."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import evaluate_full_extraction_custom_cols as exact_eval
import evaluate_full_extraction_soft_entities as soft_eval
from build_llm_entity_route_predictions import DATASETS, OUT_DIR, SUMMARY_PATH as BUILD_SUMMARY_PATH
from entity_matchers_diagnostic import score_pair


PRED_DIR = OUT_DIR / "predictions"
REPORT_DIR = OUT_DIR / "reports"
MISMATCH_DIR = OUT_DIR / "mismatches"
REPORT_PATH = OUT_DIR / "FULL_EXTRACTION_LLM_REAL_ROUTE_REPORT.md"
SUMMARY_PATH = OUT_DIR / "SUMMARY.json"

VARIANTS = {
    "baseline_v0": "pred_entities",
    "v2_reference": "pred_entities_v2",
    "llm_open": "pred_entities_llm_open",
    "llm_adaptive": "pred_entities_llm_adaptive",
}

GOLD_OTHER_VARIANTS = {
    "gold_other_llm_open": "pred_entities_llm_open",
    "gold_other_llm_adaptive": "pred_entities_llm_adaptive",
}

MODES = ["exact", "soft-difflib", "soft-embedding"]


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def eval_rows(path):
    rows = read_rows(path)
    return rows, [row for row in rows if row.get("include_in_eval", "YES") in {"", "YES"}]


def route_cols(variant):
    if variant.startswith("gold_other"):
        return {
            "role_col": "pred_role_goldother",
            "status_col": "pred_operative_status_goldother",
            "relation_col": "pred_relation_goldother",
            "answer_col": "pred_answer_relevant_goldother",
        }
    return {
        "role_col": "pred_role",
        "status_col": "pred_operative_status",
        "relation_col": "pred_relation",
        "answer_col": "pred_answer_relevant",
    }


def mean_preds(rows, entities_col):
    counts = [len(soft_eval.parse_entity_cell(row.get(entities_col, ""))) for row in rows]
    return sum(counts) / len(counts) if counts else 0.0


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
    return count / len(rows) if rows else 0.0


def run_exact(dataset, variant, csv_path, entities_col):
    all_rows, rows = eval_rows(csv_path)
    cols = route_cols(variant)
    metrics = exact_eval.evaluate(
        rows,
        cols["role_col"],
        entities_col,
        cols["status_col"],
        cols["relation_col"],
        cols["answer_col"],
    )
    mismatch_path = MISMATCH_DIR / f"{dataset}__{variant}__exact_mismatches.csv"
    report_path = REPORT_DIR / f"{dataset}__{variant}__exact.md"
    exact_eval.write_mismatches(mismatch_path, metrics["mismatch_rows"])
    exact_eval.write_markdown(report_path, len(all_rows), len(all_rows) - len(rows), metrics)
    return metrics, rows


def run_soft(dataset, variant, csv_path, entities_col, matcher):
    all_rows, rows = eval_rows(csv_path)
    cols = route_cols(variant)
    metrics = soft_eval.evaluate(
        rows,
        cols["role_col"],
        entities_col,
        cols["status_col"],
        cols["relation_col"],
        cols["answer_col"],
        matcher,
    )
    mismatch_path = MISMATCH_DIR / f"{dataset}__{variant}__soft_{matcher}_mismatches.csv"
    report_path = REPORT_DIR / f"{dataset}__{variant}__soft_{matcher}.md"
    soft_eval.write_mismatches(mismatch_path, metrics["mismatch_rows"])
    soft_eval.write_markdown(report_path, len(all_rows), len(all_rows) - len(rows), metrics)
    return metrics, rows


def metric_row(dataset, variant, route_mode, metric_mode, metrics, rows, entities_col, frac=None):
    return {
        "dataset": dataset,
        "variant": variant,
        "route_mode": route_mode,
        "metric_mode": metric_mode,
        "entity_avg_jaccard": metrics.get("entity_average_softjaccard", metrics.get("entity_average_jaccard")),
        "strict": metrics.get("strict_full_row_accuracy"),
        "relaxed_1": metrics.get("relaxed_1"),
        "relaxed_2": metrics.get("relaxed_2"),
        "relaxed_3": metrics.get("relaxed_3"),
        "role_accuracy": metrics.get("role_accuracy"),
        "frac_softj_ge_0_5": frac,
        "mean_preds_per_seg": mean_preds(rows, entities_col),
        "evaluated_rows": metrics.get("evaluated_rows", len(rows)),
        "entity_matcher_available": metrics.get("entity_matcher_available", True),
        "entity_matcher_reason": metrics.get("entity_matcher_reason", ""),
    }


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


def score_all():
    table_rows = []
    embeddings = {"available": None, "reason": ""}
    for dataset, spec in DATASETS.items():
        csv_path = spec["prediction"]
        if not csv_path.exists():
            raise SystemExit(f"Missing prediction file: {csv_path}. Run build_llm_entity_route_predictions.py first.")
        for variant, entities_col in VARIANTS.items():
            exact_metrics, exact_rows = run_exact(dataset, variant, csv_path, entities_col)
            table_rows.append(metric_row(dataset, variant, "real-route", "exact", exact_metrics, exact_rows, entities_col))
            for matcher in ["difflib", "embedding"]:
                soft_metrics, soft_rows = run_soft(dataset, variant, csv_path, entities_col, matcher)
                if matcher == "embedding":
                    embeddings = {
                        "available": soft_metrics.get("entity_matcher_available", False),
                        "reason": soft_metrics.get("entity_matcher_reason", ""),
                    }
                frac = frac_softj_ge_05(soft_rows, entities_col, matcher)
                table_rows.append(
                    metric_row(
                        dataset,
                        variant,
                        "real-route",
                        f"soft-{matcher}",
                        soft_metrics,
                        soft_rows,
                        entities_col,
                        frac,
                    )
                )
        for variant, entities_col in GOLD_OTHER_VARIANTS.items():
            exact_metrics, exact_rows = run_exact(dataset, variant, csv_path, entities_col)
            table_rows.append(metric_row(dataset, variant, "gold-other", "exact", exact_metrics, exact_rows, entities_col))
            for matcher in ["difflib", "embedding"]:
                soft_metrics, soft_rows = run_soft(dataset, variant, csv_path, entities_col, matcher)
                frac = frac_softj_ge_05(soft_rows, entities_col, matcher)
                table_rows.append(
                    metric_row(
                        dataset,
                        variant,
                        "gold-other",
                        f"soft-{matcher}",
                        soft_metrics,
                        soft_rows,
                        entities_col,
                        frac,
                    )
                )
    return table_rows, embeddings


def metric_value(row, key):
    value = row.get(key)
    return value if isinstance(value, (int, float)) else 0.0


def best_row(rows, datasets, variants, route_mode):
    candidates = [
        row
        for row in rows
        if row["dataset"] in datasets
        and row["variant"] in variants
        and row["route_mode"] == route_mode
        and row["metric_mode"] == "soft-embedding"
    ]
    return max(candidates, key=lambda row: metric_value(row, "relaxed_1"))


def build_verdicts(table_rows):
    by_key = {
        (row["dataset"], row["variant"], row["route_mode"], row["metric_mode"]): row
        for row in table_rows
    }
    tb_datasets = ["true_blind_combined_v3", "true_blind_R6"]
    llm_variants = ["llm_open", "llm_adaptive"]
    gold_variants = ["gold_other_llm_open", "gold_other_llm_adaptive"]
    best_real = best_row(table_rows, tb_datasets, llm_variants, "real-route")
    best_gold = best_row(table_rows, tb_datasets, gold_variants, "gold-other")
    gaps = {}
    for dataset in tb_datasets:
        for llm_variant, gold_variant in [
            ("llm_open", "gold_other_llm_open"),
            ("llm_adaptive", "gold_other_llm_adaptive"),
        ]:
            real = by_key[(dataset, llm_variant, "real-route", "soft-embedding")]
            gold = by_key[(dataset, gold_variant, "gold-other", "soft-embedding")]
            gaps[f"{dataset}__{llm_variant}"] = metric_value(gold, "relaxed_1") - metric_value(real, "relaxed_1")

    dev_adaptive = by_key[("dev", "llm_adaptive", "real-route", "soft-embedding")]
    dev_v2 = by_key[("dev", "v2_reference", "real-route", "soft-embedding")]
    out_adaptive = best_row(table_rows, tb_datasets, ["llm_adaptive"], "real-route")
    out_open = best_row(table_rows, tb_datasets, ["llm_open"], "real-route")
    ceiling = metric_value(best_gold, "relaxed_1")
    real = metric_value(best_real, "relaxed_1")
    return {
        "real_outdomain_relaxed_moves": real > 0.0,
        "entity_vs_route_gap": gaps,
        "entity_vs_route_gap_max": max(gaps.values()) if gaps else 0.0,
        "roles_now_dominant_blocker": ceiling > 0 and real < 0.5 * ceiling,
        "adaptive_best_both": (
            metric_value(dev_adaptive, "relaxed_1") >= metric_value(dev_v2, "relaxed_1") - 0.02
            and metric_value(out_adaptive, "relaxed_1") >= metric_value(out_open, "relaxed_1") - 0.02
        ),
        "best_true_blind_real_route": {
            "dataset": best_real["dataset"],
            "variant": best_real["variant"],
            "relaxed_1": best_real["relaxed_1"],
        },
        "best_true_blind_gold_other": {
            "dataset": best_gold["dataset"],
            "variant": best_gold["variant"],
            "relaxed_1": best_gold["relaxed_1"],
        },
    }


def recommendation(verdicts):
    if verdicts["adaptive_best_both"]:
        entity_choice = "Adopt llm_adaptive as the single entity variant: it preserves dev performance against v2 and stays within tolerance of llm_open out-of-domain."
    else:
        entity_choice = "Do not adopt llm_adaptive as a single default yet; keep llm_open/adaptive side by side for the next blind read."
    if verdicts["real_outdomain_relaxed_moves"] and verdicts["roles_now_dominant_blocker"]:
        bottleneck = "LLM entities move real out-of-domain full-row off zero, but route fields now dominate the remaining loss."
    elif verdicts["real_outdomain_relaxed_moves"]:
        bottleneck = "LLM entities move real out-of-domain full-row off zero; inspect role/status/relation residuals before changing route fields."
    else:
        bottleneck = "LLM entities do not move real out-of-domain relaxed_1 off zero; entity blocking remains unresolved."
    return f"{entity_choice} {bottleneck} Next step: run a roles-focused phase, then use a fresh blind split for the final headline number."


def write_report(summary):
    columns = [
        "variant",
        "route_mode",
        "metric_mode",
        "entity_avg_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
        "role_accuracy",
        "frac_softj_ge_0_5",
    ]
    lines = [
        "# FULL_EXTRACTION_LLM_REAL_ROUTE_REPORT",
        "",
        "Offline diagnostic read. Cached LLM entity spans are reused; no provider calls are made.",
    ]
    for dataset in DATASETS:
        rows = [row for row in summary["table_rows"] if row["dataset"] == dataset]
        lines.extend(["", f"## {dataset}", "", markdown_table(rows, columns)])
    lines.extend(
        [
            "",
            "## Verdicts",
            "",
            markdown_table([summary["verdicts"]], list(summary["verdicts"].keys())),
            "",
            "## Recommendation",
            "",
            summary["recommendation"],
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def print_soft_embedding_tables(table_rows):
    columns = [
        "dataset",
        "variant",
        "route_mode",
        "entity_avg_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
        "role_accuracy",
        "frac_softj_ge_0_5",
    ]
    rows = [row for row in table_rows if row["metric_mode"] == "soft-embedding"]
    for dataset in DATASETS:
        print(f"\n{dataset} soft-embedding")
        print(markdown_table([row for row in rows if row["dataset"] == dataset], columns))


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
        "experiment": "llm_entities_real_route",
        "offline": True,
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
    print("llm_entities_real_route_eval")
    print(f"embeddings_available={embeddings['available']} reason={embeddings['reason']}")
    print_soft_embedding_tables(table_rows)
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
