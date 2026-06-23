"""Evaluate frozen fresh_blind_v2 with repaired fallback entities."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import entity_ontology_v1
import evaluate_full_extraction_custom_cols as exact_eval
import evaluate_full_extraction_soft_entities as soft_eval
import extract_entities_domain_general_v1 as domain_entities
import full_extraction_rules
import run_llm_entity_extractor as entity_llm
import run_llm_role_classifier as role_llm
from entity_matchers_diagnostic import score_pair
from generate_fresh_blind_v2 import BANNED_MARKERS, ROLES, telegraph_probe_accuracy, tokens, validation_metrics
from role_taxonomies import ALLOWED_FINE_ROLES, map_role


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "data/v1/fresh_blind_v2"
ANNOTATION_DIR = OUT_ROOT / "annotation"
PRED_DIR = OUT_ROOT / "predictions"
REPORT_DIR = OUT_ROOT / "reports"
MISMATCH_DIR = OUT_ROOT / "mismatches"

GOLD_PATH = ANNOTATION_DIR / "fresh_blind_v2_gold.csv"
FROZEN_GOLD = ANNOTATION_DIR / "fresh_blind_v2_gold_frozen.csv"
FREEZE_MANIFEST = REPORT_DIR / "FRESH_BLIND_V2_GOLD_FREEZE.json"
ROLE_CACHE = PRED_DIR / "fresh_blind_v2_roles.jsonl"
ENTITY_CACHE = PRED_DIR / "fresh_blind_v2_llm_entities.jsonl"
PREDICTIONS = PRED_DIR / "fresh_blind_v2_predictions.csv"
SUMMARY_PATH = OUT_ROOT / "SUMMARY.json"
HEADLINE_REPORT = REPORT_DIR / "FRESH_BLIND_V2_HEADLINE_REPORT.md"
ROLE_CSV = REPORT_DIR / "role_accuracy_by_taxonomy.csv"
ENTITY_CSV = REPORT_DIR / "entity_quality.csv"
FULL_ROW_CSV = REPORT_DIR / "full_row_scores.csv"

TAXONOMIES = ["fine_8", "coarse_5", "coarse_4", "coarse_3"]
PRIOR_TRUE_BLIND = {"role8": 0.556, "coarse3": 0.681, "relaxed_3": 0.125, "entity_ceiling": 0.181}
FRESH_V1 = {"role8": 0.981, "coarse3": 0.981, "relaxed_3": 0.00625, "entity_ceiling": 0.0125}


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
    payload = json.dumps({"prompt": role_llm.FROZEN_PROMPT, "few_shots": role_llm.FEW_SHOTS}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def freeze_guard():
    if not FREEZE_MANIFEST.exists():
        raise SystemExit(f"Missing freeze manifest: {FREEZE_MANIFEST}. Run generate_fresh_blind_v2.py first.")
    if not FROZEN_GOLD.exists():
        raise SystemExit(f"Missing frozen gold: {FROZEN_GOLD}. Run generate_fresh_blind_v2.py first.")
    manifest = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    mutable_hash = file_sha256(GOLD_PATH)
    frozen_hash = file_sha256(FROZEN_GOLD)
    if manifest.get("sha256") != mutable_hash:
        raise SystemExit("Refusing to evaluate: fresh_blind_v2_gold.csv hash differs from freeze manifest.")
    if manifest.get("sha256") != frozen_hash:
        raise SystemExit("Refusing to evaluate: fresh_blind_v2_gold_frozen.csv hash differs from freeze manifest.")
    return manifest


def read_jsonl_cache(path):
    cache = {}
    if not Path(path).exists():
        return cache
    with Path(path).open("r", encoding="utf-8-sig") as source:
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
    called = cached = parse_failed = invalid = 0
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
            "dataset": "fresh_blind_v2",
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
    called = cached = parse_failed = 0
    for row in rows:
        segment_id = row["segment_id"]
        if segment_id in cache:
            cached += 1
            parse_failed += int(bool(cache[segment_id].get("parse_failed")))
            continue
        raw, call_error = call_entity_ollama(row.get("segment_text") or row.get("text") or "")
        if call_error:
            entities, error = [], call_error
        else:
            entities, error = entity_llm.parse_entities(raw)
        failed = bool(error)
        result = {
            "segment_id": segment_id,
            "dataset": "fresh_blind_v2",
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


def call_entity_ollama(text, timeout=45):
    prompt = entity_llm.build_prompt(text)
    base_url = role_llm.OLLAMA_BASE_URL
    try:
        response = entity_llm.request_json(
            f"{base_url}/api/generate",
            {
                "model": entity_llm.MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            },
            timeout=timeout,
        )
        return response.get("response", ""), ""
    except RuntimeError as exc:
        return "", str(exc)


def parse_entity_values(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
            return [str(item).strip() for item in parsed if str(item).strip()] if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return [part.strip() for part in text.split(";") if part.strip()]


def format_entities(values):
    output = []
    seen = set()
    for value in values:
        cleaned = domain_entities.clean_span(value)
        key = cleaned.lower()
        if cleaned and key not in seen and domain_entities.valid_span(cleaned):
            seen.add(key)
            output.append(cleaned)
    return "; ".join(output)


def cached_role(row, cached):
    role = str(cached.get("pred_role", "") if cached else "").strip().upper()
    if role in ROLES and not cached.get("parse_failed") and not cached.get("invalid_label"):
        return role
    return ""


def cached_open_entities(cached):
    if not cached or cached.get("parse_failed"):
        return []
    spans = cached.get("parsed_entities", [])
    return [str(span) for span in spans] if isinstance(spans, list) else []


def repaired_entities(text, llm_open):
    usable = [span for span in domain_entities.dedupe_spans(llm_open) if domain_entities.valid_span(span)]
    if len(usable) >= 2:
        return usable[:8], "llm_open"
    fallback = domain_entities.noun_chunks_topk(text)
    return domain_entities.dedupe_spans(usable + fallback)[:8], "noun_chunks_topk_fallback"


def rule_fields(role, text, title):
    if role not in ROLES:
        return {"operative_status": "", "relation": "", "answer_relevant": ""}
    return full_extraction_rules.infer_full_fields(role, text, title)


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "can", "for", "from", "has",
    "have", "if", "in", "into", "is", "it", "its", "more", "not", "of", "on", "or", "so",
    "than", "that", "the", "their", "then", "this", "to", "under", "when", "where", "while",
    "with", "without",
}


def nb_train(rows):
    class_counts = Counter()
    feature_counts = {role: Counter() for role in ROLES}
    feature_totals = Counter()
    vocab = set()
    for row in rows:
        role = row["gold_role"]
        class_counts[role] += 1
        for feature in tokens(row["segment_text"]):
            feature_counts[role][feature] += 1
            feature_totals[role] += 1
            vocab.add(feature)
    return class_counts, feature_counts, feature_totals, vocab


def nb_predict(model, text):
    class_counts, feature_counts, feature_totals, vocab = model
    class_total = sum(class_counts.values())
    vocab_size = max(1, len(vocab))
    scores = {}
    for role in ROLES:
        score = math.log((class_counts[role] + 1) / (class_total + len(ROLES)))
        denom = feature_totals[role] + vocab_size
        for feature in tokens(text):
            score += math.log((feature_counts[role].get(feature, 0) + 1) / denom)
        scores[role] = score
    return max(scores.items(), key=lambda item: (item[1], item[0]))[0]


def lexical_cv_predictions(rows, folds=5):
    output = {}
    ordered = sorted(rows, key=lambda row: row["segment_id"])
    for fold in range(folds):
        train = [row for index, row in enumerate(ordered) if index % folds != fold]
        test = [row for index, row in enumerate(ordered) if index % folds == fold]
        model = nb_train(train)
        for row in test:
            output[row["segment_id"]] = nb_predict(model, row["segment_text"])
    return output


def build_prediction_rows(rows, role_cache, entity_cache):
    lexical = lexical_cv_predictions(rows)
    output = []
    for row in rows:
        text = row.get("segment_text") or row.get("text") or ""
        title = row.get("title") or row.get("source_topic") or ""
        llm_role = cached_role(row, role_cache.get(row["segment_id"]))
        llm_open_values = cached_open_entities(entity_cache.get(row["segment_id"]))
        repaired_values, repaired_source = repaired_entities(text, llm_open_values)
        lexical_role = lexical[row["segment_id"]]
        llm_rules = rule_fields(llm_role, text, title)
        lexical_rules = rule_fields(lexical_role, text, title)
        copied = dict(row)
        copied.update(
            {
                "pred_role": llm_role,
                "pred_entities": format_entities(repaired_values),
                "pred_entities_repaired_source": repaired_source,
                "pred_entities_llm_open": format_entities(llm_open_values),
                "pred_entities_ontology": entity_ontology_v1.extract_entities_ontology_v1(text, title),
                "pred_operative_status": llm_rules["operative_status"],
                "pred_relation": llm_rules["relation"],
                "pred_answer_relevant": llm_rules["answer_relevant"],
                "pred_role_lexical_baseline": lexical_role,
                "pred_entities_lexical_baseline": format_entities(repaired_values),
                "pred_operative_status_lexical_baseline": lexical_rules["operative_status"],
                "pred_relation_lexical_baseline": lexical_rules["relation"],
                "pred_answer_relevant_lexical_baseline": lexical_rules["answer_relevant"],
                "pred_role_entity_ceiling": row["gold_role"],
                "pred_entities_entity_ceiling": format_entities(repaired_values),
                "pred_operative_status_entity_ceiling": row["gold_operative_status"],
                "pred_relation_entity_ceiling": row["gold_relation"],
                "pred_answer_relevant_entity_ceiling": row["gold_answer_relevant"],
            }
        )
        output.append(copied)
    return output


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def safe_map(role, taxonomy):
    if role not in ROLES:
        return ""
    return map_role(role, taxonomy)


def role_accuracy(rows, pred_col, taxonomy):
    if taxonomy == "fine_8":
        return safe_div(sum(row.get("gold_role") == row.get(pred_col) for row in rows), len(rows))
    return safe_div(sum(safe_map(row.get("gold_role", ""), taxonomy) == safe_map(row.get(pred_col, ""), taxonomy) for row in rows), len(rows))


def role_accuracy_rows(rows):
    output = []
    for model_name, pred_col in [("RouteMap-LLM", "pred_role"), ("lexical_baseline", "pred_role_lexical_baseline")]:
        for taxonomy in TAXONOMIES:
            output.append({"model": model_name, "taxonomy": taxonomy, "accuracy": role_accuracy(rows, pred_col, taxonomy)})
    return output


def predicted_verbatim_rate(rows, entities_col):
    total = verbatim = empty = 0
    for row in rows:
        values = parse_entity_values(row.get(entities_col, ""))
        empty += int(not values)
        text = row.get("segment_text", "").lower()
        for value in values:
            total += 1
            verbatim += int(value.lower() in text)
    return safe_div(verbatim, total), empty


def exact_entity_quality(rows, entities_col):
    jaccard = exact = frac = 0
    for row in rows:
        gold = set(parse_entity_values(row.get("gold_entities", "")))
        pred = set(parse_entity_values(row.get(entities_col, "")))
        scores = exact_eval.entity_scores(gold, pred)
        jaccard += scores["jaccard"]
        exact += int(scores["exact"])
        frac += int(scores["jaccard"] >= 0.5)
    return {
        "exact_entity_avg_jaccard": safe_div(jaccard, len(rows)),
        "exact_entity_match": safe_div(exact, len(rows)),
        "exact_frac_jaccard_ge_0_5": safe_div(frac, len(rows)),
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
    for model_name, col in [
        ("repaired_fallback", "pred_entities"),
        ("llm_open", "pred_entities_llm_open"),
        ("ontology", "pred_entities_ontology"),
    ]:
        verbatim, empty = predicted_verbatim_rate(rows, col)
        record = {"model": model_name, "pred_verbatim_rate": verbatim, "empty_row_count": empty}
        record.update(exact_entity_quality(rows, col))
        record.update(soft_entity_quality(rows, col, "difflib"))
        record.update(soft_entity_quality(rows, col, "embedding"))
        output.append(record)
    return output


def semicolon_gold_rows(rows):
    ready = []
    for row in rows:
        copied = dict(row)
        copied["gold_entities"] = "; ".join(parse_entity_values(row.get("gold_entities", "")))
        for col in ["pred_role", "pred_role_lexical_baseline", "pred_role_entity_ceiling"]:
            if copied.get(col, "") not in ROLES:
                copied[col] = next(role for role in ALLOWED_FINE_ROLES if role != copied.get("gold_role", ""))
        ready.append(copied)
    return ready


def model_specs():
    return {
        "RouteMap-LLM": {
            "role_col": "pred_role",
            "entities_col": "pred_entities",
            "status_col": "pred_operative_status",
            "relation_col": "pred_relation",
            "answer_col": "pred_answer_relevant",
        },
        "lexical_baseline": {
            "role_col": "pred_role_lexical_baseline",
            "entities_col": "pred_entities_lexical_baseline",
            "status_col": "pred_operative_status_lexical_baseline",
            "relation_col": "pred_relation_lexical_baseline",
            "answer_col": "pred_answer_relevant_lexical_baseline",
        },
        "entity_only_ceiling": {
            "role_col": "pred_role_entity_ceiling",
            "entities_col": "pred_entities_entity_ceiling",
            "status_col": "pred_operative_status_entity_ceiling",
            "relation_col": "pred_relation_entity_ceiling",
            "answer_col": "pred_answer_relevant_entity_ceiling",
        },
    }


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


def run_full_row(rows):
    ready = semicolon_gold_rows(rows)
    output = []
    for model_name, spec in model_specs().items():
        exact_metrics = exact_eval.evaluate(ready, spec["role_col"], spec["entities_col"], spec["status_col"], spec["relation_col"], spec["answer_col"])
        exact_eval.write_mismatches(MISMATCH_DIR / f"fresh_blind_v2__{model_name}__exact_mismatches.csv", exact_metrics["mismatch_rows"])
        output.append(full_row_record(model_name, "exact", exact_metrics))
        for matcher in ["difflib", "embedding"]:
            metrics = soft_eval.evaluate(ready, spec["role_col"], spec["entities_col"], spec["status_col"], spec["relation_col"], spec["answer_col"], matcher)
            soft_eval.write_mismatches(MISMATCH_DIR / f"fresh_blind_v2__{model_name}__soft_{matcher}_mismatches.csv", metrics["mismatch_rows"])
            output.append(full_row_record(model_name, f"soft-{matcher}", metrics))
    return output


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


def lookup(rows, model, key, taxonomy=None, mode=None):
    for row in rows:
        if row.get("model") != model:
            continue
        if taxonomy and row.get("taxonomy") != taxonomy:
            continue
        if mode and row.get("metric_mode") != mode:
            continue
        return row.get(key)
    return None


def credibility_readout(role_rows, manifest):
    llm_role8 = lookup(role_rows, "RouteMap-LLM", "accuracy", taxonomy="fine_8")
    lexical_role8 = lookup(role_rows, "lexical_baseline", "accuracy", taxonomy="fine_8")
    flag = "plausible" if 0.45 <= llm_role8 <= 0.85 else "suspect (likely residual leakage)"
    return {
        "telegraph_probe_lexical_baseline_role8": manifest.get("telegraph_probe_8role_accuracy"),
        "llm_role8_minus_lexical_baseline_role8": llm_role8 - lexical_role8,
        "plausibility_flag": flag,
    }


def headline(role_rows, full_rows, credibility):
    llm_role8 = lookup(role_rows, "RouteMap-LLM", "accuracy", taxonomy="fine_8")
    llm_coarse3 = lookup(role_rows, "RouteMap-LLM", "accuracy", taxonomy="coarse_3")
    llm_soft = next(row for row in full_rows if row["model"] == "RouteMap-LLM" and row["metric_mode"] == "soft-embedding")
    ceiling_soft = next(row for row in full_rows if row["model"] == "entity_only_ceiling" and row["metric_mode"] == "soft-embedding")
    return {
        "route_llm_role8": llm_role8,
        "route_llm_coarse3": llm_coarse3,
        "route_llm_relaxed3_soft_embedding": llm_soft["relaxed_3"],
        "entity_ceiling_relaxed3_soft_embedding": ceiling_soft["relaxed_3"],
        "plausibility_flag": credibility["plausibility_flag"],
    }


def headline_statement(values):
    return (
        f"fresh_blind_v2 role read is {values['plausibility_flag']} with role8={fmt(values['route_llm_role8'])}; "
        f"full-row soft relaxed_3={fmt(values['route_llm_relaxed3_soft_embedding'])} versus entity ceiling={fmt(values['entity_ceiling_relaxed3_soft_embedding'])}."
    )


def write_headline_report(summary):
    role_cols = ["model", "taxonomy", "accuracy"]
    entity_cols = ["model", "exact_entity_avg_jaccard", "soft_embedding_entity_avg_jaccard", "soft_embedding_frac_jaccard_ge_0_5", "pred_verbatim_rate", "empty_row_count"]
    full_cols = ["model", "metric_mode", "entity_avg_jaccard", "strict", "relaxed_1", "relaxed_2", "relaxed_3", "answer_accuracy"]
    comparison = [
        {"source": "prior_true_blind", **PRIOR_TRUE_BLIND},
        {"source": "fresh_blind_v1", **FRESH_V1},
        {
            "source": "fresh_blind_v2",
            "role8": summary["headline"]["route_llm_role8"],
            "coarse3": summary["headline"]["route_llm_coarse3"],
            "relaxed_3": summary["headline"]["route_llm_relaxed3_soft_embedding"],
            "entity_ceiling": summary["headline"]["entity_ceiling_relaxed3_soft_embedding"],
        },
    ]
    lines = [
        "# FRESH_BLIND_V2_HEADLINE_REPORT",
        "",
        summary["headline_statement"],
        "",
        "## Validation Gate",
        "",
        markdown_table([summary["validation_gate"]], ["verbatim_entity_rate", "banned_marker_hit_rate", "entity_vocab_diversity", "telegraph_probe_8role_accuracy"]),
        "",
        "## Credibility Readout",
        "",
        markdown_table([summary["credibility_readout"]], ["telegraph_probe_lexical_baseline_role8", "llm_role8_minus_lexical_baseline_role8", "plausibility_flag"]),
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
        "## Comparison",
        "",
        markdown_table(comparison, ["source", "role8", "coarse3", "relaxed_3", "entity_ceiling"]),
        "",
        "## Caveat",
        "",
        "fresh_blind_v2 is still synthetic gold. Treat it as an artifact probe and internal generalization check; upgrade through independent human annotation or real external documents before reporting a credible benchmark.",
    ]
    HEADLINE_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    MISMATCH_DIR.mkdir(parents=True, exist_ok=True)
    manifest = freeze_guard()
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

    validation_gate = dict(manifest["validation_metrics"])
    validation_gate["telegraph_probe_8role_accuracy"] = manifest["telegraph_probe_8role_accuracy"]
    credibility = credibility_readout(role_rows, manifest)
    headline_values = headline(role_rows, full_rows, credibility)
    summary = {
        "experiment": "fresh_blind_v2",
        "single_read": True,
        "freeze_manifest": manifest,
        "validation_gate": validation_gate,
        "frozen_prompt_identifiers": {
            "role_model": role_llm.MODEL,
            "role_prompt_sha256": role_prompt_sha256(),
            "entity_model": entity_llm.MODEL,
            "entity_prompt_sha256": entity_llm.PROMPT_SHA256,
            "entity_primary": "repaired_fallback: llm_open else noun_chunks_topk if fewer than 2 usable LLM spans",
            "banned_markers": BANNED_MARKERS,
        },
        "role_cache_summary": role_cache_summary,
        "entity_cache_summary": entity_cache_summary,
        "role_accuracy_by_taxonomy": role_rows,
        "entity_quality": entity_rows,
        "full_row_scores": full_rows,
        "credibility_readout": credibility,
        "headline": headline_values,
        "headline_statement": headline_statement(headline_values),
        "prior_true_blind": PRIOR_TRUE_BLIND,
        "fresh_blind_v1": FRESH_V1,
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

    print("fresh_blind_v2_eval")
    print(f"gold_sha256={manifest['sha256']}")
    print(f"row_count={manifest['row_count']}")
    print("validation_gate=" + json.dumps(validation_gate, sort_keys=True))
    print("role_cache_summary=" + json.dumps(role_cache_summary, sort_keys=True))
    print("entity_cache_summary=" + json.dumps(entity_cache_summary, sort_keys=True))
    print("\nrole_accuracy_by_taxonomy")
    print(markdown_table(role_rows, ["model", "taxonomy", "accuracy"]))
    print("\nentity_quality")
    print(markdown_table(entity_rows, ["model", "exact_entity_avg_jaccard", "soft_embedding_entity_avg_jaccard", "soft_embedding_frac_jaccard_ge_0_5", "pred_verbatim_rate", "empty_row_count"]))
    print("\nfull_row_scores")
    print(markdown_table(full_rows, ["model", "metric_mode", "entity_avg_jaccard", "strict", "relaxed_1", "relaxed_2", "relaxed_3", "answer_accuracy"]))
    print("credibility_readout=" + json.dumps(credibility, sort_keys=True))
    print("headline_statement=" + summary["headline_statement"])
    print(f"report={HEADLINE_REPORT}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
