"""Evaluate cached LLM entity extraction in full-row setting."""

from __future__ import annotations

import csv
import difflib
import json
from pathlib import Path

import entity_ontology_v1
import evaluate_full_extraction_custom_cols as exact_eval
import evaluate_full_extraction_soft_entities as soft_eval
from entity_matchers_diagnostic import score_pair
from extract_entities_hybrid_v2 import BROAD_CANONICALS, HybridV2Config, exact_link, ontology_hits
from extract_entities_hybrid_v2 import extract_entities_hybrid_v2, format_entities, normalize, ordered_entities
from run_llm_entity_extractor import PROMPT_SHA256


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/v1/full_extraction_experiments/llm_entities"
OUTPUT_DIR = OUT_DIR / "outputs"
PRED_DIR = OUT_DIR / "predictions"
REPORT_DIR = OUT_DIR / "reports"
MISMATCH_DIR = OUT_DIR / "mismatches"
REPORT_PATH = OUT_DIR / "FULL_EXTRACTION_LLM_ENTITIES_REPORT.md"
SUMMARY_PATH = OUT_DIR / "SUMMARY.json"

DEV_SOURCE = ROOT / "data/v1/gold/heldout_full_extraction_pred_v2.csv"
TRUE_BLIND_SOURCE = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
DEV_CACHE = OUTPUT_DIR / "dev_llm_entities.jsonl"
TRUE_BLIND_CACHE = OUTPUT_DIR / "true_blind_llm_entities.jsonl"

DATASETS = {
    "dev": {"source": DEV_SOURCE, "cache": DEV_CACHE, "prediction": PRED_DIR / "dev__llm_entities.csv"},
    "true_blind": {
        "source": TRUE_BLIND_SOURCE,
        "cache": TRUE_BLIND_CACHE,
        "prediction": PRED_DIR / "true_blind__llm_entities.csv",
    },
}

VARIANTS = {
    "ontology": "pred_entities_ontology",
    "v2": "pred_entities_v2",
    "llm_open": "pred_entities_llm_open",
    "llm_hybrid": "pred_entities_llm_hybrid",
    "gold_other_llm_open": "pred_entities_llm_open",
    "gold_other_llm_hybrid": "pred_entities_llm_hybrid",
}


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_rows(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_cache(path):
    cache = {}
    if not Path(path).exists():
        raise SystemExit(f"Missing LLM cache: {path}")
    with Path(path).open("r", encoding="utf-8") as source:
        for line in source:
            if line.strip():
                row = json.loads(line)
                cache[row.get("segment_id", "")] = row
    return cache


def row_text(row):
    return row.get("text") or row.get("segment_text") or ""


def row_title(row):
    return row.get("title") or row.get("source_topic") or ""


def unique_normalized(values):
    output = []
    seen = set()
    for value in values:
        norm = normalize(value)
        if not norm or norm in seen:
            continue
        output.append(norm)
        seen.add(norm)
    return output


def ontology_label_index():
    labels = []
    seen = set()
    for canonical in entity_ontology_v1.CANONICAL_ENTITIES:
        for label in [canonical] + entity_ontology_v1.ENTITY_SYNONYMS.get(canonical, []):
            key = normalize(label)
            if key and key not in seen:
                labels.append((canonical, key))
                seen.add(key)
    return labels


ONTOLOGY_LABELS = ontology_label_index()
ORDER = {entity: index for index, entity in enumerate(entity_ontology_v1.CANONICAL_ENTITIES)}


def fuzzy_link(span, threshold=0.85):
    span_norm = normalize(span)
    if not span_norm:
        return ""
    best = (0.0, "")
    for canonical, label_norm in ONTOLOGY_LABELS:
        if canonical in BROAD_CANONICALS:
            continue
        score = difflib.SequenceMatcher(None, span_norm, label_norm).ratio()
        if score > best[0] or (score == best[0] and ORDER.get(canonical, 9999) < ORDER.get(best[1], 9999)):
            best = (score, canonical)
    return best[1] if best[0] >= threshold else ""


def llm_hybrid_entities(spans, text, title):
    hits = ontology_hits(text, title)
    exact_linked = []
    fuzzy_linked = []
    open_spans = []
    for span in spans:
        exact = exact_link(span)
        if exact:
            exact_linked.append(exact)
            continue
        fuzzy = fuzzy_link(span, 0.85)
        if fuzzy:
            fuzzy_linked.append(fuzzy)
            continue
        norm = normalize(span)
        if norm:
            open_spans.append(norm)
    if len(hits) >= 1:
        return ordered_entities(list(hits) + exact_linked)
    return ordered_entities(list(hits) + exact_linked + fuzzy_linked + unique_normalized(open_spans))


def ensure_prediction_columns(row, parsed_entities):
    text = row_text(row)
    title = row_title(row)
    copied = dict(row)
    copied["pred_entities_ontology"] = entity_ontology_v1.extract_entities_ontology_v1(text, title)
    copied["pred_entities_v2"] = format_entities(extract_entities_hybrid_v2(text, title, HybridV2Config()))
    copied["pred_entities_llm_open"] = format_entities(unique_normalized(parsed_entities))
    copied["pred_entities_llm_hybrid"] = format_entities(llm_hybrid_entities(parsed_entities, text, title))
    copied["pred_role_goldother"] = row.get("gold_role", "")
    copied["pred_operative_status_goldother"] = row.get("gold_operative_status", "")
    copied["pred_relation_goldother"] = row.get("gold_relation", "")
    copied["pred_answer_relevant_goldother"] = row.get("gold_answer_relevant", "")
    if "pred_role" not in copied:
        copied["pred_role"] = row.get("gold_role", "")
    if "pred_operative_status" not in copied:
        copied["pred_operative_status"] = row.get("gold_operative_status", "")
    if "pred_relation" not in copied:
        copied["pred_relation"] = row.get("gold_relation", "")
    if "pred_answer_relevant" not in copied:
        copied["pred_answer_relevant"] = row.get("gold_answer_relevant", "")
    return copied


def build_predictions(dataset_name, spec):
    rows = read_rows(spec["source"])
    cache = read_cache(spec["cache"])
    output = []
    parse_failed = 0
    for row in rows:
        segment_id = row.get("segment_id", "")
        cached = cache.get(segment_id)
        if not cached:
            raise SystemExit(f"Missing cached LLM output for {dataset_name} segment_id={segment_id}")
        parse_failed += int(bool(cached.get("parse_failed")))
        output.append(ensure_prediction_columns(row, cached.get("parsed_entities", [])))
    fieldnames = list(output[0].keys()) if output else []
    write_rows(spec["prediction"], output, fieldnames)
    return {
        "dataset": dataset_name,
        "rows": len(output),
        "parse_failed": parse_failed,
        "parse_failure_rate": parse_failed / len(output) if output else 0.0,
        "prediction": str(spec["prediction"]),
    }


def eval_rows(path):
    rows = read_rows(path)
    return rows, [row for row in rows if row.get("include_in_eval", "YES") in {"", "YES"}]


def role_cols_for_variant(variant):
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
    mode, threshold, similarity_fn, status = soft_eval.entity_matcher(matcher_name)
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
    cols = role_cols_for_variant(variant)
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
    cols = role_cols_for_variant(variant)
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


def metric_row(dataset, variant, mode, metrics, rows, entities_col, frac=None):
    return {
        "dataset": dataset,
        "variant": variant,
        "metric_mode": mode,
        "entity_avg_jaccard": metrics.get("entity_average_softjaccard", metrics.get("entity_average_jaccard", 0.0)),
        "strict": metrics.get("strict_full_row_accuracy", 0.0),
        "relaxed_1": metrics.get("relaxed_1", 0.0),
        "relaxed_2": metrics.get("relaxed_2", 0.0),
        "relaxed_3": metrics.get("relaxed_3", 0.0),
        "role_accuracy": metrics.get("role_accuracy", 0.0),
        "mean_preds_per_seg": mean_preds(rows, entities_col),
        "frac_softj_ge_0_5": frac,
    }


def fmt(value):
    if value is None:
        return "NA"
    if isinstance(value, (float, int)):
        return f"{value:.6f}"
    return str(value)


def markdown_table(rows, columns):
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(fmt(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def write_report(summary):
    columns = [
        "variant",
        "metric_mode",
        "entity_avg_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
        "role_accuracy",
        "frac_softj_ge_0_5",
        "mean_preds_per_seg",
    ]
    lines = [
        "# FULL_EXTRACTION_LLM_ENTITIES_REPORT",
        "",
        "Development read. LLM entity outputs are cached JSONL from local Ollama llama3.1 at temperature 0. Prompt is frozen and train-derived; no locked test files were read.",
        "",
        f"Prompt SHA256: `{PROMPT_SHA256}`",
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


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)

    build_results = [build_predictions(dataset, spec) for dataset, spec in DATASETS.items()]
    table_rows = []
    embeddings = {"available": None, "reason": ""}
    for dataset, spec in DATASETS.items():
        csv_path = spec["prediction"]
        for variant, entities_col in VARIANTS.items():
            exact_metrics, exact_rows = run_exact(dataset, variant, csv_path, entities_col)
            table_rows.append(metric_row(dataset, variant, "exact", exact_metrics, exact_rows, entities_col))
            for matcher in ["difflib", "embedding"]:
                soft_metrics, soft_rows = run_soft(dataset, variant, csv_path, entities_col, matcher)
                if matcher == "embedding":
                    embeddings = {
                        "available": soft_metrics.get("entity_matcher_available", False),
                        "reason": soft_metrics.get("entity_matcher_reason", ""),
                    }
                frac = frac_softj_ge_05(soft_rows, entities_col, matcher)
                table_rows.append(metric_row(dataset, variant, f"soft-{matcher}", soft_metrics, soft_rows, entities_col, frac))

    by_key = {(row["dataset"], row["variant"], row["metric_mode"]): row for row in table_rows}
    true_blind_llm_open = by_key[("true_blind", "llm_open", "soft-embedding")]
    true_blind_llm_hybrid = by_key[("true_blind", "llm_hybrid", "soft-embedding")]
    best_true_blind_llm = max([true_blind_llm_open, true_blind_llm_hybrid], key=lambda row: row["entity_avg_jaccard"])
    true_blind_v2 = by_key[("true_blind", "v2", "soft-embedding")]
    dev_llm_hybrid = by_key[("dev", "llm_hybrid", "soft-embedding")]
    dev_ontology = by_key[("dev", "ontology", "soft-embedding")]
    gold_other_open = by_key[("true_blind", "gold_other_llm_open", "soft-embedding")]
    gold_other_hybrid = by_key[("true_blind", "gold_other_llm_hybrid", "soft-embedding")]
    goldother_ceiling = max(gold_other_open["relaxed_1"], gold_other_hybrid["relaxed_1"])
    verdicts = {
        "llm_beats_v2_outdomain_meanJ": best_true_blind_llm["entity_avg_jaccard"] > 0.170,
        "llm_unblocks_relaxed_outdomain": best_true_blind_llm["relaxed_1"] > 0.05,
        "llm_goldother_ceiling_outdomain": goldother_ceiling,
        "llm_indomain_no_regression": dev_llm_hybrid["relaxed_1"] + 0.02 >= dev_ontology["relaxed_1"],
    }
    if verdicts["llm_unblocks_relaxed_outdomain"]:
        recommendation = "LLM entities move true-blind relaxed rows off zero; compare open vs hybrid on a fresh blind split before adoption."
    elif goldother_ceiling > 0.05:
        recommendation = "LLM entities improve the entity ceiling, but route-field errors still block real relaxed rows; next test should pair LLM entities with stronger role/status/relation."
    else:
        recommendation = "LLM entities did not clear the relaxed entity bar often enough; keep improving entity extraction/scoring before pipeline adoption."
    summary = {
        "experiment": "llm_entity_extractor_eval",
        "prompt_sha256": PROMPT_SHA256,
        "build_results": build_results,
        "embeddings": embeddings,
        "table_rows": table_rows,
        "verdicts": verdicts,
        "recommendation": recommendation,
        "outputs": {"report": str(REPORT_PATH), "summary": str(SUMMARY_PATH)},
    }
    write_report(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("llm_entity_full_extraction_eval")
    print(f"embeddings_available={embeddings['available']} reason={embeddings['reason']}")
    columns = [
        "variant",
        "metric_mode",
        "entity_avg_jaccard",
        "strict",
        "relaxed_1",
        "relaxed_2",
        "relaxed_3",
        "role_accuracy",
        "frac_softj_ge_0_5",
        "mean_preds_per_seg",
    ]
    for dataset in DATASETS:
        print(f"\n{dataset}")
        print(markdown_table([row for row in table_rows if row["dataset"] == dataset], columns))
    print("verdicts=" + json.dumps(verdicts, sort_keys=True))
    print(f"report={REPORT_PATH}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
