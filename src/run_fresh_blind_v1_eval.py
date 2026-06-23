"""Freeze and evaluate fresh_blind_v1 once with frozen RouteMap-LLM v1."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

import entity_ontology_v1
import evaluate_full_extraction_custom_cols as exact_eval
import evaluate_full_extraction_soft_entities as soft_eval
import full_extraction_rules
import run_llm_entity_extractor as entity_llm
import run_llm_role_classifier as role_llm
from build_llm_entity_route_predictions import (
    BROAD_CANONICALS,
    G_GATE,
    T_LINK_HIGH,
    format_entities,
    llm_adaptive_entities,
    unique_normalized,
)
from entity_matchers_diagnostic import score_pair
from role_taxonomies import ALLOWED_FINE_ROLES, map_role
from train_role_text_baselines import CentroidTfidfLike
from validate_true_blind_gold import validate_rows


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "data/v1/fresh_blind_v1"
ANNOTATION_DIR = OUT_ROOT / "annotation"
PRED_DIR = OUT_ROOT / "predictions"
REPORT_DIR = OUT_ROOT / "reports"
MISMATCH_DIR = OUT_ROOT / "mismatches"

GOLD_PATH = ANNOTATION_DIR / "fresh_blind_gold.csv"
FROZEN_GOLD = ANNOTATION_DIR / "fresh_blind_gold_frozen.csv"
FREEZE_MANIFEST = REPORT_DIR / "FRESH_BLIND_GOLD_FREEZE.json"
ROLE_CACHE = PRED_DIR / "fresh_blind_roles.jsonl"
ENTITY_CACHE = PRED_DIR / "fresh_blind_llm_entities.jsonl"
PREDICTIONS = PRED_DIR / "fresh_blind_v1_predictions.csv"
SUMMARY_PATH = OUT_ROOT / "SUMMARY.json"
HEADLINE_REPORT = REPORT_DIR / "FRESH_BLIND_V1_HEADLINE_REPORT.md"
ROLE_CSV = REPORT_DIR / "role_accuracy_by_taxonomy.csv"
ENTITY_CSV = REPORT_DIR / "entity_quality.csv"
FULL_ROW_CSV = REPORT_DIR / "full_row_scores.csv"
TRAIN_DEV_PATH = ROOT / "data/v1/gold/model_train_dev_role.csv"

ROLES = set(ALLOWED_FINE_ROLES)
TAXONOMIES = ["fine_8", "coarse_5", "coarse_4", "coarse_3"]
PRIOR_TRUE_BLIND = {
    "role8": 0.556,
    "coarse3": 0.681,
    "relaxed_3": 0.125,
    "entity_ceiling": 0.181,
}


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_rows(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fieldnames} for row in rows])


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def role_prompt_sha256():
    payload = json.dumps(
        {"prompt": role_llm.FROZEN_PROMPT, "few_shots": role_llm.FEW_SHOTS},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_gold():
    if not GOLD_PATH.exists():
        raise SystemExit(f"Missing fresh gold: {GOLD_PATH}. Run generate_fresh_blind_v1.py first.")
    rows = read_rows(GOLD_PATH)
    errors, counts = validate_rows(rows)
    if errors:
        raise SystemExit("fresh_blind_v1 gold validation failed:\n" + "\n".join(errors))

    current_hash = file_sha256(GOLD_PATH)
    manifest = {
        "dataset": "fresh_blind_v1",
        "gold_path": str(GOLD_PATH.relative_to(ROOT)),
        "frozen_gold_path": str(FROZEN_GOLD.relative_to(ROOT)),
        "sha256": current_hash,
        "row_count": len(rows),
        "role_counts": dict(sorted(counts["role"].items())),
        "rule": "Freeze before prediction. If this manifest exists with a different fresh_blind_gold.csv hash, refuse to run.",
        "gold_provenance": "synthetic gold by construction from generator-declared segment intent; not model-generated labels",
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if FREEZE_MANIFEST.exists():
        previous = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
        if previous.get("sha256") != current_hash:
            raise SystemExit(
                "Refusing to evaluate: fresh_blind_gold.csv hash differs from existing freeze manifest "
                f"{FREEZE_MANIFEST}"
            )
        if FROZEN_GOLD.exists() and file_sha256(FROZEN_GOLD) != previous.get("sha256"):
            raise SystemExit(f"Refusing to evaluate: frozen gold hash differs from manifest {FREEZE_MANIFEST}")
        if not FROZEN_GOLD.exists():
            shutil.copyfile(GOLD_PATH, FROZEN_GOLD)
        return previous

    shutil.copyfile(GOLD_PATH, FROZEN_GOLD)
    FREEZE_MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def read_jsonl_cache(path):
    cache = {}
    path = Path(path)
    if not path.exists():
        return cache
    with path.open("r", encoding="utf-8-sig") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("segment_id"):
                cache[row["segment_id"]] = row
    return cache


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as target:
        target.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run_role_predictions(rows):
    cache = read_jsonl_cache(ROLE_CACHE)
    called = 0
    cached = 0
    parse_failed = 0
    invalid = 0
    prompt_hash = role_prompt_sha256()
    for row in rows:
        segment_id = row["segment_id"]
        if segment_id in cache:
            cached += 1
            parse_failed += int(bool(cache[segment_id].get("parse_failed")))
            invalid += int(bool(cache[segment_id].get("invalid_label")))
            continue
        raw = role_llm.call_ollama(role_llm.prompt_for(row))
        pred_role, failed, invalid_label, error = role_llm.parse_role(raw)
        result = {
            "segment_id": segment_id,
            "dataset": "fresh_blind_v1",
            "model": role_llm.MODEL,
            "prompt_sha256": prompt_hash,
            "raw_response": raw,
            "pred_role": pred_role,
            "parse_failed": failed,
            "invalid_label": invalid_label,
            "parse_error": error,
        }
        append_jsonl(ROLE_CACHE, result)
        cache[segment_id] = result
        called += 1
        parse_failed += int(bool(failed))
        invalid += int(bool(invalid_label))
        print(f"role {segment_id} pred={pred_role or 'EMPTY'} parse_failed={failed} invalid={bool(invalid_label)}")
    return cache, {"rows": len(rows), "called": called, "cached": cached, "parse_failed": parse_failed, "invalid": invalid}


def run_entity_predictions(rows):
    cache = read_jsonl_cache(ENTITY_CACHE)
    called = 0
    cached = 0
    parse_failed = 0
    for row in rows:
        segment_id = row["segment_id"]
        if segment_id in cache:
            cached += 1
            parse_failed += int(bool(cache[segment_id].get("parse_failed")))
            continue
        raw = entity_llm.call_ollama(entity_llm.build_prompt(row.get("text") or row.get("segment_text") or ""))
        entities, error = entity_llm.parse_entities(raw)
        failed = bool(error)
        result = {
            "segment_id": segment_id,
            "dataset": "fresh_blind_v1",
            "model": entity_llm.MODEL,
            "prompt_sha256": entity_llm.PROMPT_SHA256,
            "raw_response": raw,
            "parsed_entities": entities,
            "parse_failed": failed,
            "parse_error": error or "",
        }
        append_jsonl(ENTITY_CACHE, result)
        cache[segment_id] = result
        called += 1
        parse_failed += int(failed)
        print(f"entity {segment_id} spans={len(entities)} parse_failed={failed}")
    return cache, {"rows": len(rows), "called": called, "cached": cached, "parse_failed": parse_failed}


def wrong_role(gold):
    for role in ALLOWED_FINE_ROLES:
        if role != gold:
            return role
    return ALLOWED_FINE_ROLES[0]


def cached_role(row, cached):
    role = str(cached.get("pred_role", "") if cached else "").strip().upper()
    return role if role in ROLES and not cached.get("parse_failed") and not cached.get("invalid_label") else ""


def cached_spans(cached):
    if not cached or cached.get("parse_failed"):
        return []
    spans = cached.get("parsed_entities", [])
    return [str(span) for span in spans] if isinstance(spans, list) else []


def train_centroid():
    rows = [row for row in read_rows(TRAIN_DEV_PATH) if row.get("split") == "seed_train"]
    model = CentroidTfidfLike()
    model.fit(rows)
    return model


def rule_fields(role, text, title):
    if role not in ROLES:
        return {"operative_status": "", "relation": "", "answer_relevant": ""}
    return full_extraction_rules.infer_full_fields(role, text, title)


def build_prediction_rows(rows, role_cache, entity_cache):
    baseline = train_centroid()
    output = []
    for row in rows:
        text = row.get("text") or row.get("segment_text") or ""
        title = row.get("title") or row.get("source_topic") or ""
        llm_role = cached_role(row, role_cache.get(row["segment_id"]))
        spans = cached_spans(entity_cache.get(row["segment_id"]))
        llm_open = format_entities(unique_normalized(spans))
        llm_adaptive = format_entities(llm_adaptive_entities(spans, text, title))
        llm_rules = rule_fields(llm_role, text, title)

        baseline_role = baseline.predict({"text": text})
        baseline_entities = entity_ontology_v1.extract_entities_ontology_v1(text, title)
        baseline_rules = rule_fields(baseline_role, text, title)

        copied = dict(row)
        copied.update(
            {
                "pred_role": llm_role,
                "pred_entities": llm_adaptive,
                "pred_entities_llm_open": llm_open,
                "pred_operative_status": llm_rules["operative_status"],
                "pred_relation": llm_rules["relation"],
                "pred_answer_relevant": llm_rules["answer_relevant"],
                "pred_route_fields_source": "full_extraction_rules_with_llm_role",
                "pred_role_baseline": baseline_role,
                "pred_entities_baseline_ontology": baseline_entities,
                "pred_operative_status_baseline": baseline_rules["operative_status"],
                "pred_relation_baseline": baseline_rules["relation"],
                "pred_answer_relevant_baseline": baseline_rules["answer_relevant"],
                "pred_role_entity_ceiling": row["gold_role"],
                "pred_entities_entity_ceiling": llm_adaptive,
                "pred_operative_status_entity_ceiling": row["gold_operative_status"],
                "pred_relation_entity_ceiling": row["gold_relation"],
                "pred_answer_relevant_entity_ceiling": row["gold_answer_relevant"],
            }
        )
        output.append(copied)
    return output


def parse_entity_values(value):
    return soft_eval.parse_entity_cell(value)


def semicolon_entities(value):
    return "; ".join(parse_entity_values(value))


def eval_ready_rows(rows):
    ready = []
    for row in rows:
        copied = dict(row)
        copied["gold_entities"] = semicolon_entities(row.get("gold_entities", ""))
        return_role = copied.get("pred_role", "")
        if return_role not in ROLES:
            copied["pred_role"] = wrong_role(copied.get("gold_role", ""))
        for col in ["pred_role_baseline", "pred_role_entity_ceiling"]:
            if copied.get(col, "") not in ROLES:
                copied[col] = wrong_role(copied.get("gold_role", ""))
        ready.append(copied)
    return ready


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def safe_map(role, taxonomy):
    if role not in ROLES:
        return ""
    return map_role(role, taxonomy)


def role_accuracy(rows, pred_col, taxonomy):
    if taxonomy == "fine_8":
        return safe_div(sum(row.get("gold_role") == row.get(pred_col) for row in rows), len(rows))
    return safe_div(
        sum(safe_map(row.get("gold_role", ""), taxonomy) == safe_map(row.get(pred_col, ""), taxonomy) for row in rows),
        len(rows),
    )


def role_accuracy_rows(rows):
    output = []
    for model_name, pred_col in [("RouteMap-LLM", "pred_role"), ("deterministic_baseline", "pred_role_baseline")]:
        for taxonomy in TAXONOMIES:
            output.append(
                {
                    "model": model_name,
                    "taxonomy": taxonomy,
                    "accuracy": role_accuracy(rows, pred_col, taxonomy),
                }
            )
    return output


def exact_entity_quality(rows, entities_col):
    totals = Counter()
    for row in rows:
        gold = set(parse_entity_values(row.get("gold_entities", "")))
        pred = set(parse_entity_values(row.get(entities_col, "")))
        scores = exact_eval.entity_scores(gold, pred)
        totals["jaccard"] += scores["jaccard"]
        totals["exact"] += int(scores["exact"])
        totals["frac"] += int(scores["jaccard"] >= 0.5)
    return {
        "exact_entity_avg_jaccard": safe_div(totals["jaccard"], len(rows)),
        "exact_entity_match": safe_div(totals["exact"], len(rows)),
        "exact_frac_jaccard_ge_0_5": safe_div(totals["frac"], len(rows)),
    }


def soft_entity_quality(rows, entities_col, matcher):
    mode, threshold, similarity_fn, status = soft_eval.entity_matcher(matcher)
    if similarity_fn is None:
        return {
            f"{mode}_available": False,
            f"{mode}_reason": status["reason"],
            f"{mode}_entity_avg_jaccard": None,
            f"{mode}_frac_jaccard_ge_0_5": None,
        }
    soft_eval.prepare_similarity(similarity_fn, rows, entities_col)
    total = 0.0
    frac = 0
    for row in rows:
        scores = score_pair(
            parse_entity_values(row.get("gold_entities", "")),
            parse_entity_values(row.get(entities_col, "")),
            similarity_fn,
            threshold,
        )
        total += scores["soft_jaccard"]
        frac += int(scores["soft_jaccard"] >= 0.5)
    return {
        f"{mode}_available": True,
        f"{mode}_reason": status["reason"],
        f"{mode}_entity_avg_jaccard": safe_div(total, len(rows)),
        f"{mode}_frac_jaccard_ge_0_5": safe_div(frac, len(rows)),
    }


def entity_quality_rows(rows):
    output = []
    for model_name, entities_col in [
        ("RouteMap-LLM adaptive", "pred_entities"),
        ("RouteMap-LLM open", "pred_entities_llm_open"),
        ("deterministic ontology", "pred_entities_baseline_ontology"),
    ]:
        record = {"model": model_name}
        record.update(exact_entity_quality(rows, entities_col))
        record.update(soft_entity_quality(rows, entities_col, "difflib"))
        record.update(soft_entity_quality(rows, entities_col, "embedding"))
        output.append(record)
    return output


def model_specs():
    return {
        "RouteMap-LLM": {
            "role_col": "pred_role",
            "entities_col": "pred_entities",
            "status_col": "pred_operative_status",
            "relation_col": "pred_relation",
            "answer_col": "pred_answer_relevant",
        },
        "deterministic_baseline": {
            "role_col": "pred_role_baseline",
            "entities_col": "pred_entities_baseline_ontology",
            "status_col": "pred_operative_status_baseline",
            "relation_col": "pred_relation_baseline",
            "answer_col": "pred_answer_relevant_baseline",
        },
        "entity_only_ceiling": {
            "role_col": "pred_role_entity_ceiling",
            "entities_col": "pred_entities_entity_ceiling",
            "status_col": "pred_operative_status_entity_ceiling",
            "relation_col": "pred_relation_entity_ceiling",
            "answer_col": "pred_answer_relevant_entity_ceiling",
        },
    }


def run_full_row(rows):
    ready = eval_ready_rows(rows)
    output = []
    for model_name, spec in model_specs().items():
        exact_metrics = exact_eval.evaluate(
            ready,
            spec["role_col"],
            spec["entities_col"],
            spec["status_col"],
            spec["relation_col"],
            spec["answer_col"],
        )
        exact_eval.write_mismatches(
            MISMATCH_DIR / f"fresh_blind_v1__{model_name}__exact_mismatches.csv",
            exact_metrics["mismatch_rows"],
        )
        output.append(full_row_record(model_name, "exact", exact_metrics))
        for matcher in ["difflib", "embedding"]:
            metrics = soft_eval.evaluate(
                ready,
                spec["role_col"],
                spec["entities_col"],
                spec["status_col"],
                spec["relation_col"],
                spec["answer_col"],
                matcher,
            )
            soft_eval.write_mismatches(
                MISMATCH_DIR / f"fresh_blind_v1__{model_name}__soft_{matcher}_mismatches.csv",
                metrics["mismatch_rows"],
            )
            output.append(full_row_record(model_name, f"soft-{matcher}", metrics))
    return output


def full_row_record(model_name, metric_mode, metrics):
    return {
        "model": model_name,
        "metric_mode": metric_mode,
        "entity_avg_jaccard": metrics.get("entity_average_softjaccard", metrics.get("entity_average_jaccard")),
        "strict": metrics.get("strict_full_row_accuracy"),
        "relaxed_1": metrics.get("relaxed_1"),
        "relaxed_2": metrics.get("relaxed_2"),
        "relaxed_3": metrics.get("relaxed_3"),
        "role8_accuracy": metrics.get("role_accuracy"),
        "answer_accuracy": metrics.get("answer_relevance_accuracy"),
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


def write_headline_report(summary):
    role_cols = ["model", "taxonomy", "accuracy"]
    entity_cols = [
        "model",
        "exact_entity_avg_jaccard",
        "soft_difflib_entity_avg_jaccard",
        "soft_difflib_frac_jaccard_ge_0_5",
        "soft_embedding_entity_avg_jaccard",
        "soft_embedding_frac_jaccard_ge_0_5",
    ]
    full_cols = ["model", "metric_mode", "entity_avg_jaccard", "strict", "relaxed_1", "relaxed_2", "relaxed_3", "answer_accuracy"]
    prior_rows = [
        {
            "metric": "role8",
            "prior_true_blind": PRIOR_TRUE_BLIND["role8"],
            "fresh_blind_v1": summary["headline"]["route_llm_role8"],
        },
        {
            "metric": "coarse3",
            "prior_true_blind": PRIOR_TRUE_BLIND["coarse3"],
            "fresh_blind_v1": summary["headline"]["route_llm_coarse3"],
        },
        {
            "metric": "relaxed_3_soft_embedding",
            "prior_true_blind": PRIOR_TRUE_BLIND["relaxed_3"],
            "fresh_blind_v1": summary["headline"]["route_llm_relaxed3_soft_embedding"],
        },
        {
            "metric": "entity_ceiling_relaxed3_soft_embedding",
            "prior_true_blind": PRIOR_TRUE_BLIND["entity_ceiling"],
            "fresh_blind_v1": summary["headline"]["entity_ceiling_relaxed3_soft_embedding"],
        },
    ]
    lines = [
        "# FRESH_BLIND_V1_HEADLINE_REPORT",
        "",
        summary["headline_statement"],
        "",
        "## Gold Freeze",
        "",
        f"- SHA256: {summary['freeze_manifest']['sha256']}",
        f"- Rows: {summary['freeze_manifest']['row_count']}",
        "",
        "## Role Accuracy",
        "",
        markdown_table(summary["role_accuracy_by_taxonomy"], role_cols),
        "",
        "## Entity Quality",
        "",
        markdown_table(summary["entity_quality"], entity_cols),
        "",
        "## Full Row Scores",
        "",
        markdown_table(summary["full_row_scores"], full_cols),
        "",
        "## Prior True-Blind Side By Side",
        "",
        markdown_table(prior_rows, ["metric", "prior_true_blind", "fresh_blind_v1"]),
        "",
        "## Caveat",
        "",
        "fresh_blind_v1 is synthetic gold by construction. Treat it as an internal generalization check, then upgrade with independent human annotation via fresh_blind_annotation_template.csv or real external documents before publishing a credible headline.",
    ]
    HEADLINE_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def headline(summary_rows, role_rows):
    lookup_role = {(row["model"], row["taxonomy"]): row["accuracy"] for row in role_rows}
    lookup_full = {(row["model"], row["metric_mode"]): row for row in summary_rows}
    route_soft = lookup_full[("RouteMap-LLM", "soft-embedding")]
    ceiling_soft = lookup_full[("entity_only_ceiling", "soft-embedding")]
    return {
        "route_llm_role8": lookup_role[("RouteMap-LLM", "fine_8")],
        "route_llm_coarse3": lookup_role[("RouteMap-LLM", "coarse_3")],
        "route_llm_relaxed3_soft_embedding": route_soft.get("relaxed_3"),
        "route_llm_relaxed1_soft_embedding": route_soft.get("relaxed_1"),
        "entity_ceiling_relaxed3_soft_embedding": ceiling_soft.get("relaxed_3"),
        "route_llm_strict_soft_embedding": route_soft.get("strict"),
    }


def headline_statement(headline_values):
    holds_role = headline_values["route_llm_coarse3"] >= 0.65
    holds_relaxed = headline_values["route_llm_relaxed3_soft_embedding"] >= PRIOR_TRUE_BLIND["relaxed_3"] - 0.03
    if holds_role and holds_relaxed:
        result = "Frozen RouteMap-LLM broadly holds on synthetic fresh_blind_v1."
    elif holds_role:
        result = "Frozen RouteMap-LLM role behavior holds, but full-row relaxed score drops on synthetic fresh_blind_v1."
    else:
        result = "Frozen RouteMap-LLM does not cleanly hold on synthetic fresh_blind_v1."
    return (
        f"{result} The binding constraint is the gap between entity coverage and full-row route/answer survival, "
        f"with relaxed_3={fmt(headline_values['route_llm_relaxed3_soft_embedding'])} versus "
        f"entity-only ceiling={fmt(headline_values['entity_ceiling_relaxed3_soft_embedding'])}."
    )


def main():
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)

    manifest = freeze_gold()
    rows = read_rows(FROZEN_GOLD)

    role_llm.ensure_ollama()
    role_cache, role_cache_summary = run_role_predictions(rows)
    entity_cache, entity_cache_summary = run_entity_predictions(rows)
    prediction_rows = build_prediction_rows(rows, role_cache, entity_cache)
    write_rows(PREDICTIONS, prediction_rows)

    role_rows = role_accuracy_rows(prediction_rows)
    entity_rows = entity_quality_rows(prediction_rows)
    full_rows = run_full_row(prediction_rows)

    write_rows(ROLE_CSV, role_rows, ["model", "taxonomy", "accuracy"])
    write_rows(ENTITY_CSV, entity_rows)
    write_rows(FULL_ROW_CSV, full_rows)

    headline_values = headline(full_rows, role_rows)
    summary = {
        "experiment": "fresh_blind_v1",
        "offline_generation": True,
        "single_read": True,
        "freeze_manifest": manifest,
        "frozen_prompt_identifiers": {
            "role_model": role_llm.MODEL,
            "role_prompt_sha256": role_prompt_sha256(),
            "entity_model": entity_llm.MODEL,
            "entity_prompt_sha256": entity_llm.PROMPT_SHA256,
            "adaptive_gate": {"G_GATE": G_GATE, "T_LINK_HIGH": T_LINK_HIGH, "BROAD_CANONICALS": sorted(BROAD_CANONICALS)},
        },
        "role_cache_summary": role_cache_summary,
        "entity_cache_summary": entity_cache_summary,
        "role_accuracy_by_taxonomy": role_rows,
        "entity_quality": entity_rows,
        "full_row_scores": full_rows,
        "prior_true_blind": PRIOR_TRUE_BLIND,
        "headline": headline_values,
        "headline_statement": headline_statement(headline_values),
        "outputs": {
            "predictions": str(PREDICTIONS),
            "role_accuracy_by_taxonomy": str(ROLE_CSV),
            "entity_quality": str(ENTITY_CSV),
            "full_row_scores": str(FULL_ROW_CSV),
            "headline_report": str(HEADLINE_REPORT),
            "summary": str(SUMMARY_PATH),
            "mismatches": str(MISMATCH_DIR),
        },
    }
    write_headline_report(summary)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("fresh_blind_v1_eval")
    print(f"gold_sha256={manifest['sha256']}")
    print(f"row_count={manifest['row_count']}")
    print(f"ollama_model={role_llm.MODEL}")
    print("role_cache_summary=" + json.dumps(role_cache_summary, sort_keys=True))
    print("entity_cache_summary=" + json.dumps(entity_cache_summary, sort_keys=True))
    print("\nrole_accuracy_by_taxonomy")
    print(markdown_table(role_rows, ["model", "taxonomy", "accuracy"]))
    print("\nentity_quality")
    print(
        markdown_table(
            entity_rows,
            [
                "model",
                "exact_entity_avg_jaccard",
                "soft_difflib_entity_avg_jaccard",
                "soft_difflib_frac_jaccard_ge_0_5",
                "soft_embedding_entity_avg_jaccard",
                "soft_embedding_frac_jaccard_ge_0_5",
            ],
        )
    )
    print("\nfull_row_scores")
    print(markdown_table(full_rows, ["model", "metric_mode", "entity_avg_jaccard", "strict", "relaxed_1", "relaxed_2", "relaxed_3", "answer_accuracy"]))
    print("headline_statement=" + summary["headline_statement"])
    print(f"report={HEADLINE_REPORT}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
