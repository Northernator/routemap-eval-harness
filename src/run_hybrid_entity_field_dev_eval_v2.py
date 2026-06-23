"""Run hybrid_entity_field_dev_eval_v2.

Tunes hybrid_v2 only on model_train_dev_role.csv train rows, freezes the config,
then evaluates dev and true-blind transfer reads. Locked test files are not read.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import entity_ontology_v1
from entity_matchers_diagnostic import (
    EmbeddingMatcher,
    difflib_similarity,
    normalized_exact_similarity,
    safe_div,
    score_pair,
)
from evaluate_entity_extraction import score_sets
from extract_entities_domain_general_v1 import noun_chunks_topk
from extract_entities_hybrid_v1 import (
    HybridConfig as HybridV1Config,
    candidate_spans as candidate_spans_v1,
    extract_entities_hybrid as extract_entities_hybrid_v1,
    format_entities as format_entities_v1,
)
from extract_entities_hybrid_v2 import (
    HybridV2Config,
    candidate_spans as candidate_spans_v2,
    extract_entities_hybrid_v2,
    format_entities as format_entities_v2,
)


ROOT = Path(__file__).resolve().parents[1]
TRAIN_DEV_PATH = ROOT / "data/v1/gold/model_train_dev_role.csv"
TRUE_BLIND_PATH = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
OUT_DIR = ROOT / "data/v1/entity_field_experiments/hybrid_v2"
PRED_DIR = OUT_DIR / "predictions"
ROWS_DIR = OUT_DIR / "rows"
REPORT_PATH = OUT_DIR / "REPORT.md"
SUMMARY_PATH = OUT_DIR / "SUMMARY.json"

K_SWEEP = [4, 6]
MAX_PER_SEG_SWEEP = [4, 6, 8]
T_LINK_HIGH_SWEEP = [0.85, 0.90]
G_GATE_SWEEP = [1, 2]
P_FLOOR = 0.30

FROZEN_V1_CONFIG = HybridV1Config(
    k=6,
    t_link_fuzzy=0.7,
    t_link_embed=0.5,
    t_cluster=0.72,
    max_entities_per_seg=10,
)


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_rows(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


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


def split_prediction_entities(value):
    return [part.strip() for part in (value or "").split(";") if part.strip()]


def row_text(row):
    return row.get("text") or row.get("segment_text") or ""


def row_title(row):
    return row.get("title") or row.get("source_topic") or ""


def mean(values):
    values = list(values)
    return safe_div(sum(values), len(values))


def harmonic_mean(left, right):
    if left is None or right is None:
        return None
    return safe_div(2 * left * right, left + right)


def strategy_prediction(row, strategy, v2_config, embedding_matcher):
    text = row_text(row)
    title = row_title(row)
    if strategy == "ontology_v1":
        return entity_ontology_v1.extract_entities_ontology_v1(text, title)
    if strategy == "pure_extractive":
        return format_entities_v2(noun_chunks_topk(text))
    if strategy == "hybrid_v1":
        return format_entities_v1(
            extract_entities_hybrid_v1(text, title, FROZEN_V1_CONFIG, None, cluster_unlinked=False)
        )
    if strategy == "hybrid_v2":
        return format_entities_v2(extract_entities_hybrid_v2(text, title, v2_config))
    raise ValueError(f"unknown strategy: {strategy}")


def prediction_rows(rows, dataset, strategy, v2_config, embedding_matcher):
    output = []
    for row in rows:
        output.append(
            {
                "dataset": dataset,
                "strategy": strategy,
                "segment_id": row.get("segment_id", ""),
                "title": row_title(row),
                "text": row_text(row),
                "gold_entities": row.get("gold_entities", ""),
                "pred_entities": strategy_prediction(row, strategy, v2_config, embedding_matcher),
            }
        )
    return output


def safe_name(value):
    return str(value).replace(".", "_").replace(" ", "_").replace("/", "_")


def score_soft_rows(dataset, strategy, rows, matcher_name, threshold, similarity_fn, out_path):
    totals = {"soft_precision": 0.0, "soft_recall": 0.0, "soft_f1": 0.0, "soft_jaccard": 0.0}
    scored_rows = []
    if hasattr(similarity_fn, "prepare_values"):
        values = []
        for row in rows:
            values.extend(parse_entity_cell(row.get("gold_entities", "")))
            values.extend(split_prediction_entities(row.get("pred_entities", "")))
        similarity_fn.prepare_values(values)
    for row in rows:
        gold = parse_entity_cell(row.get("gold_entities", ""))
        pred = split_prediction_entities(row.get("pred_entities", ""))
        scores = score_pair(gold, pred, similarity_fn, threshold)
        for key in totals:
            totals[key] += scores[key]
        scored_rows.append(
            {
                "dataset": dataset,
                "strategy": strategy,
                "matcher": matcher_name,
                "threshold": threshold,
                "segment_id": row.get("segment_id", ""),
                "gold_entities": json.dumps(gold, ensure_ascii=False),
                "pred_entities": json.dumps(pred, ensure_ascii=False),
                "gold_count": scores["gold_count"],
                "pred_count": scores["pred_count"],
                "matches": scores["matches"],
                "soft_precision": scores["soft_precision"],
                "soft_recall": scores["soft_recall"],
                "soft_f1": scores["soft_f1"],
                "soft_jaccard": scores["soft_jaccard"],
                "matched_pairs": json.dumps(scores["matched_pairs"], ensure_ascii=False),
            }
        )
    write_rows(
        out_path,
        scored_rows,
        [
            "dataset",
            "strategy",
            "matcher",
            "threshold",
            "segment_id",
            "gold_entities",
            "pred_entities",
            "gold_count",
            "pred_count",
            "matches",
            "soft_precision",
            "soft_recall",
            "soft_f1",
            "soft_jaccard",
            "matched_pairs",
        ],
    )
    n = len(rows)
    return {
        "rows": n,
        "soft_precision": safe_div(totals["soft_precision"], n),
        "soft_recall": safe_div(totals["soft_recall"], n),
        "soft_f1": safe_div(totals["soft_f1"], n),
        "soft_jaccard": safe_div(totals["soft_jaccard"], n),
    }


def score_soft_rows_summary(rows, threshold, similarity_fn):
    totals = {"soft_precision": 0.0, "soft_recall": 0.0, "soft_f1": 0.0, "soft_jaccard": 0.0}
    for row in rows:
        scores = score_pair(
            parse_entity_cell(row.get("gold_entities", "")),
            split_prediction_entities(row.get("pred_entities", "")),
            similarity_fn,
            threshold,
        )
        for key in totals:
            totals[key] += scores[key]
    n = len(rows)
    return {
        "rows": n,
        "soft_precision": safe_div(totals["soft_precision"], n),
        "soft_recall": safe_div(totals["soft_recall"], n),
        "soft_f1": safe_div(totals["soft_f1"], n),
        "soft_jaccard": safe_div(totals["soft_jaccard"], n),
    }


def score_exact_rows(dataset, strategy, rows, out_path):
    totals = {"jaccard": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "exact": 0.0, "zero_overlap": 0.0}
    scored_rows = []
    for row in rows:
        gold = entity_ontology_v1.split_entity_set(row.get("gold_entities", ""))
        pred = entity_ontology_v1.split_entity_set(row.get("pred_entities", ""))
        scores = score_sets(gold, pred)
        for key in totals:
            totals[key] += float(scores[key])
        scored_rows.append(
            {
                "dataset": dataset,
                "strategy": strategy,
                "segment_id": row.get("segment_id", ""),
                "gold_entities": entity_ontology_v1.format_entity_set(gold),
                "pred_entities": entity_ontology_v1.format_entity_set(pred),
                "jaccard": scores["jaccard"],
                "precision": scores["precision"],
                "recall": scores["recall"],
                "f1": scores["f1"],
                "exact": scores["exact"],
                "zero_overlap": scores["zero_overlap"],
                "missing": entity_ontology_v1.format_entity_set(scores["missing"]),
                "extra": entity_ontology_v1.format_entity_set(scores["extra"]),
            }
        )
    write_rows(
        out_path,
        scored_rows,
        [
            "dataset",
            "strategy",
            "segment_id",
            "gold_entities",
            "pred_entities",
            "jaccard",
            "precision",
            "recall",
            "f1",
            "exact",
            "zero_overlap",
            "missing",
            "extra",
        ],
    )
    n = len(rows)
    return {key: safe_div(value, n) for key, value in totals.items()} | {"rows": n}


def matcher_specs(embedding_matcher):
    specs = [
        ("M1_normalized_exact", 1.0, normalized_exact_similarity),
        ("M3_fuzzy_difflib", 0.6, difflib_similarity),
    ]
    if embedding_matcher.available:
        cache = {}

        def cached_embedding_similarity(left, right):
            key = (left, right)
            if key not in cache:
                cache[key] = embedding_matcher.similarity(left, right)
            return cache[key]

        cached_embedding_similarity.prepare_values = embedding_matcher.prepare
        specs.append(("M4_embedding_cosine", 0.5, cached_embedding_similarity))
    return specs


def score_train_config(train_rows, config):
    pred_rows = []
    for row in train_rows:
        pred_rows.append(
            {
                "segment_id": row.get("segment_id", ""),
                "gold_entities": row.get("gold_entities", ""),
                "pred_entities": format_entities_v2(extract_entities_hybrid_v2(row_text(row), row_title(row), config)),
            }
        )
    return score_soft_rows_summary(pred_rows, 0.6, difflib_similarity)


def select_config(train_rows):
    sweep = []
    for k in K_SWEEP:
        for max_per_seg in MAX_PER_SEG_SWEEP:
            for threshold in T_LINK_HIGH_SWEEP:
                for gate in G_GATE_SWEEP:
                    config = HybridV2Config(k=k, max_per_seg=max_per_seg, t_link_high=threshold, g_gate=gate)
                    metrics = score_train_config(train_rows, config)
                    sweep.append({"config": config, "metrics": metrics})
    eligible = [item for item in sweep if item["metrics"]["soft_precision"] >= P_FLOOR]
    floor_not_met = not eligible
    pool = eligible if eligible else sweep
    pool.sort(
        key=lambda item: (
            -item["metrics"]["soft_f1"],
            -item["metrics"]["soft_precision"],
            item["config"].max_per_seg,
            item["config"].k,
            item["config"].t_link_high,
            item["config"].g_gate,
        )
    )
    return pool[0], sweep, floor_not_met


def prepare_embeddings(rows, embedding_matcher):
    if not embedding_matcher.available:
        return
    values = list(entity_ontology_v1.CANONICAL_ENTITIES)
    for row in rows:
        text = f"{row_title(row)} {row_text(row)}"
        values.extend(candidate_spans_v2(text, HybridV2Config(k=max(K_SWEEP), max_per_seg=max(MAX_PER_SEG_SWEEP))))
        values.extend(parse_entity_cell(row.get("gold_entities", "")))
    embedding_matcher.prepare(values)


def evaluate_dataset(dataset, rows, strategies, v2_config, embedding_matcher, include_exact):
    metrics = {}
    for strategy in strategies:
        pred_rows = prediction_rows(rows, dataset, strategy, v2_config, embedding_matcher)
        write_rows(
            PRED_DIR / f"{dataset}__{strategy}_predictions.csv",
            pred_rows,
            ["dataset", "strategy", "segment_id", "title", "text", "gold_entities", "pred_entities"],
        )
        metrics[strategy] = {
            "mean_preds_per_seg": mean(len(split_prediction_entities(row["pred_entities"])) for row in pred_rows)
        }
        if include_exact:
            metrics[strategy]["exact_ontology"] = score_exact_rows(
                dataset,
                strategy,
                pred_rows,
                ROWS_DIR / f"{dataset}__{strategy}__exact_ontology.csv",
            )
        for matcher_name, threshold, similarity_fn in matcher_specs(embedding_matcher):
            metrics[strategy][f"{matcher_name}@{threshold}"] = score_soft_rows(
                dataset,
                strategy,
                pred_rows,
                matcher_name,
                threshold,
                similarity_fn,
                ROWS_DIR / f"{dataset}__{strategy}__{safe_name(matcher_name)}_{safe_name(threshold)}.csv",
            )
    return metrics


def transfer_row(strategy, dev_metrics, out_metrics, embedding_available):
    dev_exact = dev_metrics[strategy].get("exact_ontology", {})
    dev_soft = dev_metrics[strategy]["M3_fuzzy_difflib@0.6"]
    out_soft = out_metrics[strategy]["M3_fuzzy_difflib@0.6"]
    out_embed = out_metrics[strategy].get("M4_embedding_cosine@0.5")
    out_for_balance = out_embed["soft_f1"] if embedding_available and out_embed else out_soft["soft_f1"]
    return {
        "strategy": strategy,
        "in_domain_exact_jaccard": dev_exact.get("jaccard"),
        "in_domain_exact_precision": dev_exact.get("precision"),
        "in_domain_exact_recall": dev_exact.get("recall"),
        "in_domain_exact_f1": dev_exact.get("f1"),
        "in_domain_soft_precision": dev_soft["soft_precision"],
        "in_domain_soft_recall": dev_soft["soft_recall"],
        "in_domain_soft_f1": dev_soft["soft_f1"],
        "in_domain_soft_jaccard": dev_soft["soft_jaccard"],
        "out_domain_soft_f1_difflib": out_soft["soft_f1"],
        "out_domain_soft_f1_embed": out_embed["soft_f1"] if out_embed else None,
        "balanced_HM": harmonic_mean(dev_soft["soft_f1"], out_for_balance),
        "in_domain_mean_preds_per_seg": dev_metrics[strategy]["mean_preds_per_seg"],
        "out_domain_mean_preds_per_seg": out_metrics[strategy]["mean_preds_per_seg"],
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
        lines.append("| " + " | ".join(fmt(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def write_report(summary):
    columns = [
        "strategy",
        "in_domain_exact_jaccard",
        "in_domain_soft_f1",
        "in_domain_soft_precision",
        "out_domain_soft_f1_difflib",
        "out_domain_soft_f1_embed",
        "balanced_HM",
        "in_domain_mean_preds_per_seg",
        "out_domain_mean_preds_per_seg",
    ]
    lines = [
        "# hybrid_entity_field_dev_eval_v2",
        "",
        "ABLATION / DEV EVAL. Parameters were selected only on model_train_dev_role.csv train rows, then frozen for heldout_v1_dev and true-blind reads. Locked test files, frozen gold/prediction files, production ontology/evaluators, and prior reports were not modified.",
        "",
        "## Frozen Config",
        "",
        "```json",
        json.dumps(summary["frozen_config"], indent=2, sort_keys=True),
        "```",
        "",
        "## Transfer Matrix",
        "",
        markdown_table(summary["transfer_matrix"], columns),
        "",
        "## Verdicts",
        "",
        markdown_table([summary["verdicts"]], list(summary["verdicts"].keys())),
        "",
        "## Recommendation",
        "",
        summary["recommendation"],
        "",
        "## Train Sweep",
        "",
        markdown_table(
            summary["train_sweep"],
            ["k", "max_per_seg", "t_link_high", "g_gate", "soft_precision", "soft_recall", "soft_f1"],
        ),
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    _ = args

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    ROWS_DIR.mkdir(parents=True, exist_ok=True)

    train_dev_rows = read_rows(TRAIN_DEV_PATH)
    true_blind_rows = read_rows(TRUE_BLIND_PATH)
    train_rows = [row for row in train_dev_rows if "train" in row.get("split", "").lower()]
    dev_rows = [row for row in train_dev_rows if "dev" in row.get("split", "").lower()]
    if not train_rows or not dev_rows:
        raise SystemExit("Expected train/dev rows in split column.")

    chosen, sweep, floor_not_met = select_config(train_rows)
    frozen_config = chosen["config"]

    embedding_matcher = EmbeddingMatcher.load()
    strategies = ["ontology_v1", "pure_extractive", "hybrid_v1", "hybrid_v2"]
    dev_metrics = evaluate_dataset("in_domain_dev", dev_rows, strategies, frozen_config, embedding_matcher, True)
    out_metrics = evaluate_dataset("out_domain_true_blind", true_blind_rows, strategies, frozen_config, embedding_matcher, False)
    transfer_matrix = [
        transfer_row(strategy, dev_metrics, out_metrics, embedding_matcher.available) for strategy in strategies
    ]
    by_strategy = {row["strategy"]: row for row in transfer_matrix}
    v2 = by_strategy["hybrid_v2"]
    v1 = by_strategy["hybrid_v1"]
    others = [by_strategy["ontology_v1"], by_strategy["pure_extractive"], by_strategy["hybrid_v1"]]
    v2_pareto_improves_v1 = (
        v2["in_domain_soft_f1"] >= 0.211 and (v2["out_domain_soft_f1_embed"] or 0.0) >= 0.323
    )
    v2_balanced_best = v2["balanced_HM"] is not None and v2["balanced_HM"] > max(row["balanced_HM"] or 0.0 for row in others)
    v2_precision_recovered = v2["in_domain_soft_precision"] >= 0.35
    v2_stretch_met = v2["in_domain_soft_f1"] >= 0.35 and (v2["out_domain_soft_f1_embed"] or 0.0) >= 0.40
    verdicts = {
        "v2_pareto_improves_v1": v2_pareto_improves_v1,
        "v2_balanced_best": v2_balanced_best,
        "v2_precision_recovered": v2_precision_recovered,
        "v2_stretch_met": v2_stretch_met,
        "floor_not_met": floor_not_met,
    }
    if v2_stretch_met and v2_balanced_best:
        recommendation = "Freeze hybrid_v2 as the development candidate and run a fresh blind split for final numbers."
    elif v2_balanced_best or v2_pareto_improves_v1:
        recommendation = "hybrid_v2 is a promising development candidate, but continue train/dev precision work before a fresh blind split."
    elif v2["out_domain_soft_f1_embed"] and v2["out_domain_soft_f1_embed"] > v1["out_domain_soft_f1_embed"]:
        recommendation = "hybrid_v2 improves transfer but does not recover in-domain precision enough; revise the adaptive gate on train/dev."
    else:
        recommendation = "hybrid_v2 does not Pareto-improve v1; keep v1/pure extractive diagnostics and redesign precision controls on train/dev."

    train_sweep = [
        {
            "k": item["config"].k,
            "max_per_seg": item["config"].max_per_seg,
            "t_link_high": item["config"].t_link_high,
            "g_gate": item["config"].g_gate,
            "soft_precision": item["metrics"]["soft_precision"],
            "soft_recall": item["metrics"]["soft_recall"],
            "soft_f1": item["metrics"]["soft_f1"],
            "soft_jaccard": item["metrics"]["soft_jaccard"],
        }
        for item in sweep
    ]
    train_sweep.sort(key=lambda row: (-row["soft_f1"], -row["soft_precision"], row["max_per_seg"], row["k"]))
    summary = {
        "experiment": "hybrid_entity_field_dev_eval_v2",
        "inputs": {
            "train_dev": str(TRAIN_DEV_PATH),
            "true_blind": str(TRUE_BLIND_PATH),
            "locked_test_files_read": False,
        },
        "row_counts": {"train": len(train_rows), "dev": len(dev_rows), "true_blind": len(true_blind_rows)},
        "embeddings": {"available": embedding_matcher.available, "reason": embedding_matcher.reason},
        "clustering": {"run": False, "reason": "hybrid_v2 spec uses adaptive gate, not clustering"},
        "frozen_config": {
            "k": frozen_config.k,
            "max_per_seg": frozen_config.max_per_seg,
            "t_link_high": frozen_config.t_link_high,
            "g_gate": frozen_config.g_gate,
            "precision_floor": P_FLOOR,
            "floor_met": not floor_not_met,
            "selection_metric": "train soft_f1 M3_fuzzy_difflib@0.6 subject to train soft_precision >= 0.30",
        },
        "frozen_v1_config": {
            "k": FROZEN_V1_CONFIG.k,
            "t_link_fuzzy": FROZEN_V1_CONFIG.t_link_fuzzy,
            "t_link_embed": FROZEN_V1_CONFIG.t_link_embed,
            "t_cluster": FROZEN_V1_CONFIG.t_cluster,
            "max_entities_per_seg": FROZEN_V1_CONFIG.max_entities_per_seg,
        },
        "metrics": {"in_domain_dev": dev_metrics, "out_domain_true_blind": out_metrics},
        "transfer_matrix": transfer_matrix,
        "train_sweep": train_sweep,
        "verdicts": verdicts,
        "recommendation": recommendation,
        "outputs": {"report": str(REPORT_PATH), "summary": str(SUMMARY_PATH)},
    }
    write_report(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    columns = [
        "strategy",
        "in_domain_exact_jaccard",
        "in_domain_soft_f1",
        "in_domain_soft_precision",
        "out_domain_soft_f1_difflib",
        "out_domain_soft_f1_embed",
        "balanced_HM",
        "in_domain_mean_preds_per_seg",
        "out_domain_mean_preds_per_seg",
    ]
    print("hybrid_entity_field_dev_eval_v2")
    print(f"embeddings_available={embedding_matcher.available} reason={embedding_matcher.reason}")
    print("clustering_run=False")
    print(
        "frozen_config="
        f"K={frozen_config.k}, MAX_PER_SEG={frozen_config.max_per_seg}, "
        f"T_LINK_HIGH={frozen_config.t_link_high}, G_GATE={frozen_config.g_gate}, "
        f"precision_floor_met={not floor_not_met}"
    )
    print(markdown_table(transfer_matrix, columns))
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
