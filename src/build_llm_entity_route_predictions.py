"""Build offline LLM-entity/real-route prediction files.

Reads cached LLM entity JSONL only. This script must not call Ollama or any
provider; missing cache rows are a hard stop.
"""

from __future__ import annotations

import csv
import difflib
import json
from pathlib import Path

import entity_ontology_v1
from extract_entities_hybrid_v2 import (
    BROAD_CANONICALS,
    HybridV2Config,
    exact_link,
    extract_entities_hybrid_v2,
    format_entities,
    normalize,
    ordered_entities,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "data/v1/full_extraction_experiments/llm_entities/outputs"
OUT_DIR = ROOT / "data/v1/full_extraction_experiments/llm_real_route"
PRED_DIR = OUT_DIR / "predictions"
SUMMARY_PATH = OUT_DIR / "BUILD_SUMMARY.json"

TRUE_BLIND_CACHE = SOURCE_DIR / "true_blind_llm_entities.jsonl"
DEV_CACHE = SOURCE_DIR / "dev_llm_entities.jsonl"

G_GATE = 1
T_LINK_HIGH = 0.85

DATASETS = {
    "true_blind_combined_v3": {
        "source": ROOT / "data/v1/true_blind_natural_language/predictions/combined_v3_true_blind_predictions.csv",
        "cache": TRUE_BLIND_CACHE,
        "prediction": PRED_DIR / "true_blind_combined_v3__llm_real_route.csv",
    },
    "true_blind_R6": {
        "source": ROOT / "data/v1/true_blind_natural_language/predictions/R6_true_blind_predictions.csv",
        "cache": TRUE_BLIND_CACHE,
        "prediction": PRED_DIR / "true_blind_R6__llm_real_route.csv",
    },
    "dev": {
        "source": ROOT / "data/v1/gold/heldout_full_extraction_pred_v2.csv",
        "cache": DEV_CACHE,
        "prediction": PRED_DIR / "dev__llm_real_route.csv",
    },
}


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_rows(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_cache(path):
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"Missing LLM entity cache: {path}")
    cache = {}
    with path.open("r", encoding="utf-8-sig") as source:
        for line in source:
            if not line.strip():
                continue
            row = json.loads(line)
            segment_id = row.get("segment_id", "")
            if segment_id:
                cache[segment_id] = row
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


def ontology_hits(text, title=""):
    return entity_ontology_v1.split_entity_set(entity_ontology_v1.extract_entities_ontology_v1(text, title))


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


def fuzzy_link(span, threshold=T_LINK_HIGH):
    span_norm = normalize(span)
    if not span_norm:
        return ""
    best_score = 0.0
    best_canonical = ""
    for canonical, label_norm in ONTOLOGY_LABELS:
        if canonical in BROAD_CANONICALS:
            continue
        score = difflib.SequenceMatcher(None, span_norm, label_norm).ratio()
        if score > best_score or (
            score == best_score and ORDER.get(canonical, 9999) < ORDER.get(best_canonical, 9999)
        ):
            best_score = score
            best_canonical = canonical
    return best_canonical if best_score >= threshold else ""


def linked_canonical(span):
    exact = exact_link(span)
    if exact:
        return exact
    return fuzzy_link(span, T_LINK_HIGH)


def llm_adaptive_entities(spans, text, title):
    hits = ontology_hits(text, title)
    if len(hits) < G_GATE:
        return unique_normalized(spans)
    linked = [linked_canonical(span) for span in spans]
    return ordered_entities(list(hits) + [entity for entity in linked if entity])


def parsed_spans(cached):
    if not cached or cached.get("parse_failed"):
        return []
    spans = cached.get("parsed_entities", [])
    if not isinstance(spans, list):
        return []
    return [str(span) for span in spans]


def ensure_columns(row, cached):
    text = row_text(row)
    title = row_title(row)
    spans = parsed_spans(cached)
    copied = dict(row)
    if "pred_entities_v2" not in copied:
        copied["pred_entities_v2"] = format_entities(extract_entities_hybrid_v2(text, title, HybridV2Config()))
    copied["pred_entities_llm_open"] = format_entities(unique_normalized(spans))
    copied["pred_entities_llm_adaptive"] = format_entities(llm_adaptive_entities(spans, text, title))
    copied["pred_role_goldother"] = row.get("gold_role", "")
    copied["pred_operative_status_goldother"] = row.get("gold_operative_status", "")
    copied["pred_relation_goldother"] = row.get("gold_relation", "")
    copied["pred_answer_relevant_goldother"] = row.get("gold_answer_relevant", "")
    return copied


def build_dataset(dataset, spec):
    rows = read_rows(spec["source"])
    cache = read_cache(spec["cache"])
    output = []
    missing = []
    parse_failed = 0
    empty_open = 0
    empty_adaptive = 0
    for row in rows:
        segment_id = row.get("segment_id", "")
        cached = cache.get(segment_id)
        if cached is None:
            missing.append(segment_id)
            continue
        parse_failed += int(bool(cached.get("parse_failed")))
        copied = ensure_columns(row, cached)
        empty_open += int(not copied["pred_entities_llm_open"])
        empty_adaptive += int(not copied["pred_entities_llm_adaptive"])
        output.append(copied)
    if missing:
        raise SystemExit(f"Missing cached LLM rows for {dataset}: {', '.join(missing[:10])}")
    fieldnames = list(output[0].keys()) if output else []
    write_rows(spec["prediction"], output, fieldnames)
    return {
        "dataset": dataset,
        "source": str(spec["source"]),
        "cache": str(spec["cache"]),
        "prediction": str(spec["prediction"]),
        "cache_rows_available": len(cache),
        "rows": len(output),
        "parse_failed": parse_failed,
        "empty_llm_open": empty_open,
        "empty_llm_adaptive": empty_adaptive,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    build_results = [build_dataset(dataset, spec) for dataset, spec in DATASETS.items()]
    summary = {
        "experiment": "llm_entities_real_route_build",
        "offline": True,
        "g_gate": G_GATE,
        "t_link_high": T_LINK_HIGH,
        "build_results": build_results,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    print("llm_entities_real_route_build")
    for row in build_results:
        print(
            f"{row['dataset']}: rows={row['rows']} cache_rows={row['cache_rows_available']} "
            f"parse_failed={row['parse_failed']} empty_open={row['empty_llm_open']} "
            f"empty_adaptive={row['empty_llm_adaptive']}"
        )
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
