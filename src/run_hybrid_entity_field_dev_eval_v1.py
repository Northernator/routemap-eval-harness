"""Run hybrid_entity_field_dev_eval_v1.

This experiment tunes only on model_train_dev_role.csv seed_train rows, freezes
the selected hybrid config, then reads heldout_v1_dev and true-blind without
further tuning. Locked test files and prior ablations are not read or modified.
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
    score_pair,
    safe_div,
)
from evaluate_entity_extraction import score_sets
from extract_entities_domain_general_v1 import noun_chunks_topk
from extract_entities_hybrid_v1 import HybridConfig, candidate_spans, extract_entities_hybrid, format_entities


ROOT = Path(__file__).resolve().parents[1]
TRAIN_DEV_PATH = ROOT / "data/v1/gold/model_train_dev_role.csv"
TRUE_BLIND_PATH = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
OUT_DIR = ROOT / "data/v1/entity_field_experiments/hybrid_v1"
PRED_DIR = OUT_DIR / "predictions"
ROWS_DIR = OUT_DIR / "rows"
REPORT_PATH = OUT_DIR / "HYBRID_ENTITY_FIELD_DEV_EVAL_V1_REPORT.md"
SUMMARY_PATH = OUT_DIR / "HYBRID_ENTITY_FIELD_DEV_EVAL_V1_SUMMARY.json"

K_SWEEP = [6, 8, 10]
T_LINK_FUZZY_SWEEP = [0.6, 0.7, 0.8]
T_LINK_EMBED = 0.5
T_CLUSTER = 0.72
MAX_ENTITIES_PER_SEG = 10


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


def strategy_prediction(row, strategy, config=None, embedding_matcher=None, cluster_unlinked=False):
    text = row_text(row)
    title = row_title(row)
    if strategy == "ontology_v1":
        return entity_ontology_v1.extract_entities_ontology_v1(text, title)
    if strategy == "pure_extractive":
        return format_entities(noun_chunks_topk(text))
    if strategy == "hybrid_v1":
        entities = extract_entities_hybrid(text, title, config, embedding_matcher, cluster_unlinked)
        return format_entities(entities)
    raise ValueError(f"unknown strategy: {strategy}")


def prediction_rows(rows, dataset, strategy, config=None, embedding_matcher=None, cluster_unlinked=False):
    output = []
    for row in rows:
        pred_entities = strategy_prediction(row, strategy, config, embedding_matcher, cluster_unlinked)
        output.append(
            {
                "dataset": dataset,
                "strategy": strategy,
                "segment_id": row.get("segment_id", ""),
                "title": row_title(row),
                "text": row_text(row),
                "gold_entities": row.get("gold_entities", ""),
                "pred_entities": pred_entities,
            }
        )
    return output


def mean(values):
    values = list(values)
    return safe_div(sum(values), len(values))


def score_soft_rows(dataset, strategy, rows, matcher_name, threshold, similarity_fn, out_path):
    scored_rows = []
    totals = {"soft_precision": 0.0, "soft_recall": 0.0, "soft_f1": 0.0, "soft_jaccard": 0.0}
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


def score_exact_rows(dataset, strategy, rows, out_path):
    scored_rows = []
    totals = {"jaccard": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "exact": 0.0, "zero_overlap": 0.0}
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
    return {
        "rows": n,
        "jaccard": safe_div(totals["jaccard"], n),
        "precision": safe_div(totals["precision"], n),
        "recall": safe_div(totals["recall"], n),
        "f1": safe_div(totals["f1"], n),
        "exact": safe_div(totals["exact"], n),
        "zero_overlap": safe_div(totals["zero_overlap"], n),
    }


def safe_name(value):
    return str(value).replace(".", "_").replace(" ", "_").replace("/", "_")


def select_config(train_rows, embedding_matcher, cluster_unlinked):
    candidates = []
    for k in K_SWEEP:
        for fuzzy in T_LINK_FUZZY_SWEEP:
            config = HybridConfig(
                k=k,
                t_link_fuzzy=fuzzy,
                t_link_embed=T_LINK_EMBED,
                t_cluster=T_CLUSTER,
                max_entities_per_seg=MAX_ENTITIES_PER_SEG,
            )
            pred_rows = prediction_rows(
                train_rows,
                "in_domain_train",
                "hybrid_v1",
                config,
                embedding_matcher,
                cluster_unlinked,
            )
            metrics = score_soft_rows(
                "in_domain_train",
                "hybrid_v1",
                pred_rows,
                "M3_fuzzy_difflib",
                0.6,
                difflib_similarity,
                ROWS_DIR / f"train_tuning__hybrid_v1__k{k}__fuzzy{safe_name(fuzzy)}__M3_0_6.csv",
            )
            candidates.append({"config": config, "metrics": metrics})
    candidates.sort(
        key=lambda item: (
            -item["metrics"]["soft_f1"],
            -item["metrics"]["soft_precision"],
            item["config"].k,
            item["config"].t_link_fuzzy,
        )
    )
    return candidates[0], candidates


def matcher_specs(embedding_matcher):
    specs = [
        ("M1_normalized_exact", 1.0, normalized_exact_similarity),
        ("M3_fuzzy_difflib", 0.6, difflib_similarity),
    ]
    if embedding_matcher.available:
        specs.append(("M4_embedding_cosine", 0.5, embedding_matcher.similarity))
    return specs


def prepare_hybrid_embeddings(rows, embedding_matcher):
    if not embedding_matcher.available:
        return
    config = HybridConfig(k=max(K_SWEEP), t_link_fuzzy=min(T_LINK_FUZZY_SWEEP))
    values = list(entity_ontology_v1.CANONICAL_ENTITIES)
    for row in rows:
        values.extend(candidate_spans(f"{row_title(row)} {row_text(row)}", config))
        values.extend(parse_entity_cell(row.get("gold_entities", "")))
    embedding_matcher.prepare(values)


def evaluate_dataset(dataset, rows, strategies, config, embedding_matcher, cluster_unlinked, include_exact):
    predictions = {}
    metrics = {}
    for strategy in strategies:
        pred_rows = prediction_rows(rows, dataset, strategy, config, embedding_matcher, cluster_unlinked)
        predictions[strategy] = pred_rows
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
            key = f"{matcher_name}@{threshold}"
            metrics[strategy][key] = score_soft_rows(
                dataset,
                strategy,
                pred_rows,
                matcher_name,
                threshold,
                similarity_fn,
                ROWS_DIR / f"{dataset}__{strategy}__{safe_name(matcher_name)}_{safe_name(threshold)}.csv",
            )
    return predictions, metrics


def transfer_row(strategy, dev_metrics, out_metrics):
    dev_exact = dev_metrics[strategy].get("exact_ontology", {})
    dev_soft = dev_metrics[strategy].get("M3_fuzzy_difflib@0.6", {})
    out_soft = out_metrics[strategy].get("M3_fuzzy_difflib@0.6", {})
    out_embed = out_metrics[strategy].get("M4_embedding_cosine@0.5", {})
    return {
        "strategy": strategy,
        "in_domain_exact_jaccard": dev_exact.get("jaccard"),
        "in_domain_exact_f1": dev_exact.get("f1"),
        "in_domain_soft_f1_difflib_0_6": dev_soft.get("soft_f1"),
        "out_domain_soft_f1_difflib_0_6": out_soft.get("soft_f1"),
        "out_domain_soft_f1_embedding_0_5": out_embed.get("soft_f1"),
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
        "in_domain_exact_f1",
        "in_domain_soft_f1_difflib_0_6",
        "out_domain_soft_f1_difflib_0_6",
        "out_domain_soft_f1_embedding_0_5",
        "in_domain_mean_preds_per_seg",
        "out_domain_mean_preds_per_seg",
    ]
    lines = [
        "# HYBRID_ENTITY_FIELD_DEV_EVAL_V1_REPORT",
        "",
        "ABLATION / DEV EVAL. Parameters were selected only on model_train_dev_role.csv seed_train rows, then frozen for heldout_v1_dev and true-blind reads. Locked test files, frozen true-blind files, production ontology, production evaluator, and prior ablations were not modified.",
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
            ["k", "t_link_fuzzy", "soft_f1", "soft_precision", "soft_recall", "soft_jaccard"],
        ),
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cluster-unlinked", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    ROWS_DIR.mkdir(parents=True, exist_ok=True)

    train_dev_rows = read_rows(TRAIN_DEV_PATH)
    true_blind_rows = read_rows(TRUE_BLIND_PATH)
    train_rows = [row for row in train_dev_rows if "train" in row.get("split", "").lower()]
    dev_rows = [row for row in train_dev_rows if "dev" in row.get("split", "").lower()]
    if not train_rows or not dev_rows:
        raise SystemExit("Expected train/dev rows in split column; found none.")

    embedding_matcher = EmbeddingMatcher.load()
    prepare_hybrid_embeddings(train_rows + dev_rows + true_blind_rows, embedding_matcher)
    chosen, sweep = select_config(train_rows, embedding_matcher, args.cluster_unlinked)
    frozen_config = chosen["config"]
    strategies = ["ontology_v1", "pure_extractive", "hybrid_v1"]

    _dev_predictions, dev_metrics = evaluate_dataset(
        "in_domain_dev",
        dev_rows,
        strategies,
        frozen_config,
        embedding_matcher,
        args.cluster_unlinked,
        include_exact=True,
    )
    _out_predictions, out_metrics = evaluate_dataset(
        "out_domain_true_blind",
        true_blind_rows,
        strategies,
        frozen_config,
        embedding_matcher,
        args.cluster_unlinked,
        include_exact=False,
    )

    transfer_matrix = [transfer_row(strategy, dev_metrics, out_metrics) for strategy in strategies]
    by_strategy = {row["strategy"]: row for row in transfer_matrix}
    ontology = by_strategy["ontology_v1"]
    pure = by_strategy["pure_extractive"]
    hybrid = by_strategy["hybrid_v1"]

    hybrid_keeps_in_domain = (
        hybrid["in_domain_soft_f1_difflib_0_6"] >= 0.95 * ontology["in_domain_soft_f1_difflib_0_6"]
    )
    hybrid_strict_viable = hybrid["in_domain_exact_jaccard"] >= 0.90 * ontology["in_domain_exact_jaccard"]
    hybrid_transfers = (
        hybrid["out_domain_soft_f1_difflib_0_6"] >= 0.50 * pure["out_domain_soft_f1_difflib_0_6"]
        and hybrid["out_domain_soft_f1_difflib_0_6"] >= 3.0 * ontology["out_domain_soft_f1_difflib_0_6"]
    )
    verdicts = {
        "hybrid_keeps_in_domain": hybrid_keeps_in_domain,
        "hybrid_strict_viable": hybrid_strict_viable,
        "hybrid_transfers": hybrid_transfers,
        "clustering_run": args.cluster_unlinked,
    }
    if all(verdicts.values()) or (hybrid_keeps_in_domain and hybrid_transfers):
        recommendation = (
            "Adopt hybrid_v1 as a development candidate entity field with the frozen config below; "
            "develop only on train/dev, then run a fresh blind split for final numbers."
        )
    elif hybrid_transfers:
        recommendation = (
            "Hybrid transfer is promising but in-domain retention is not yet sufficient; continue train/dev work "
            "on precision controls before any fresh blind run."
        )
    else:
        recommendation = (
            "Hybrid_v1 does not yet validate the transfer tradeoff; keep ontology_v1 as default and develop a "
            "stronger open-span layer on train/dev."
        )

    train_sweep = [
        {
            "k": item["config"].k,
            "t_link_fuzzy": item["config"].t_link_fuzzy,
            "soft_f1": item["metrics"]["soft_f1"],
            "soft_precision": item["metrics"]["soft_precision"],
            "soft_recall": item["metrics"]["soft_recall"],
            "soft_jaccard": item["metrics"]["soft_jaccard"],
        }
        for item in sweep
    ]
    train_sweep.sort(key=lambda row: (-row["soft_f1"], row["k"], row["t_link_fuzzy"]))

    summary = {
        "experiment": "hybrid_entity_field_dev_eval_v1",
        "inputs": {
            "train_dev": str(TRAIN_DEV_PATH),
            "true_blind": str(TRUE_BLIND_PATH),
            "locked_test_files_read": False,
        },
        "row_counts": {"train": len(train_rows), "dev": len(dev_rows), "true_blind": len(true_blind_rows)},
        "embeddings": {"available": embedding_matcher.available, "reason": embedding_matcher.reason},
        "frozen_config": {
            "k": frozen_config.k,
            "t_link_fuzzy": frozen_config.t_link_fuzzy,
            "t_link_embed": frozen_config.t_link_embed,
            "t_cluster": frozen_config.t_cluster,
            "max_entities_per_seg": frozen_config.max_entities_per_seg,
            "cluster_unlinked": args.cluster_unlinked,
            "selection_metric": "train soft_f1 using M3_fuzzy_difflib@0.6",
        },
        "train_sweep": train_sweep,
        "metrics": {"in_domain_dev": dev_metrics, "out_domain_true_blind": out_metrics},
        "transfer_matrix": transfer_matrix,
        "verdicts": verdicts,
        "recommendation": recommendation,
        "outputs": {"report": str(REPORT_PATH), "summary": str(SUMMARY_PATH)},
    }
    write_report(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("hybrid_entity_field_dev_eval_v1")
    print(f"embeddings_available={embedding_matcher.available} reason={embedding_matcher.reason}")
    print(f"clustering_run={args.cluster_unlinked}")
    print(
        "frozen_config="
        f"K={frozen_config.k}, T_LINK_FUZZY={frozen_config.t_link_fuzzy}, "
        f"T_LINK_EMBED={frozen_config.t_link_embed}, T_CLUSTER={frozen_config.t_cluster}, "
        f"MAX_ENTITIES_PER_SEG={frozen_config.max_entities_per_seg}"
    )
    print(markdown_table(transfer_matrix, [
        "strategy",
        "in_domain_exact_jaccard",
        "in_domain_exact_f1",
        "in_domain_soft_f1_difflib_0_6",
        "out_domain_soft_f1_difflib_0_6",
        "out_domain_soft_f1_embedding_0_5",
        "in_domain_mean_preds_per_seg",
        "out_domain_mean_preds_per_seg",
    ]))
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
