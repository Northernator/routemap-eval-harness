"""Build offline LLM-role + LLM-entity full-route prediction files."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from build_llm_entity_route_predictions import (
    BROAD_CANONICALS,
    G_GATE,
    T_LINK_HIGH,
    format_entities,
    llm_adaptive_entities,
    parsed_spans,
    unique_normalized,
)
from llm_output_parsing import extract_json_object_from_text
from role_taxonomies import ALLOWED_FINE_ROLES


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/v1/full_extraction_experiments/llm_full_route"
PRED_DIR = OUT_DIR / "predictions"
SUMMARY_PATH = OUT_DIR / "BUILD_SUMMARY.json"

ROLE_CACHE_DIR = ROOT / "data/v1/role_experiments/llm_role_classifier/outputs"
ENTITY_CACHE_DIR = ROOT / "data/v1/full_extraction_experiments/llm_entities/outputs"

TRUE_BLIND_ROLE_CACHE = ROLE_CACHE_DIR / "true_blind_roles.jsonl"
DEV_ROLE_CACHE = ROLE_CACHE_DIR / "dev_roles.jsonl"
TRUE_BLIND_ENTITY_CACHE = ENTITY_CACHE_DIR / "true_blind_llm_entities.jsonl"
DEV_ENTITY_CACHE = ENTITY_CACHE_DIR / "dev_llm_entities.jsonl"

DATASETS = {
    "true_blind_combined_v3": {
        "source": ROOT / "data/v1/true_blind_natural_language/predictions/combined_v3_true_blind_predictions.csv",
        "role_cache": TRUE_BLIND_ROLE_CACHE,
        "entity_cache": TRUE_BLIND_ENTITY_CACHE,
        "prediction": PRED_DIR / "true_blind_combined_v3__llm_full_route.csv",
    },
    "true_blind_R6": {
        "source": ROOT / "data/v1/true_blind_natural_language/predictions/R6_true_blind_predictions.csv",
        "role_cache": TRUE_BLIND_ROLE_CACHE,
        "entity_cache": TRUE_BLIND_ENTITY_CACHE,
        "prediction": PRED_DIR / "true_blind_R6__llm_full_route.csv",
    },
    "dev": {
        "source": ROOT / "data/v1/gold/heldout_full_extraction_pred_v2.csv",
        "role_cache": DEV_ROLE_CACHE,
        "entity_cache": DEV_ENTITY_CACHE,
        "prediction": PRED_DIR / "dev__llm_full_route.csv",
    },
}

VARIANT_SUFFIXES = [
    "role_llm_only",
    "ent_llm_only",
    "full_llm_adaptive",
    "full_llm_open",
    "diagnostic_gold_other",
]

ROLES = set(ALLOWED_FINE_ROLES)


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_rows(path, rows, fieldnames):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_cache(path, label):
    path = Path(path)
    if not path.exists():
        raise SystemExit(f"Missing required {label} cache: {path}")
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


def normalize_role(value):
    role = str(value or "").strip().upper().replace("-", "_").replace(" ", "_")
    return role if role in ROLES else ""


def cached_llm_role(cached):
    if not cached or cached.get("parse_failed") or cached.get("invalid_label"):
        return ""
    role = normalize_role(cached.get("pred_role", ""))
    if role:
        return role
    parsed, _error = extract_json_object_from_text(cached.get("raw_response", ""))
    if isinstance(parsed, dict):
        return normalize_role(parsed.get("role", ""))
    return ""


def cached_llm_entities(cached, row):
    if not cached or cached.get("parse_failed"):
        return "", ""
    spans = parsed_spans(cached)
    llm_open = format_entities(unique_normalized(spans))
    llm_adaptive = format_entities(llm_adaptive_entities(spans, row_text(row), row_title(row)))
    return llm_open, llm_adaptive


def variant_col(base, suffix):
    return f"{base}__{suffix}"


def add_variant(row, suffix, role, entities, status, relation, answer):
    row[variant_col("pred_role", suffix)] = role
    row[variant_col("pred_entities", suffix)] = entities
    row[variant_col("pred_operative_status", suffix)] = status
    row[variant_col("pred_relation", suffix)] = relation
    row[variant_col("pred_answer_relevant", suffix)] = answer


def add_columns(row, role_cached, entity_cached):
    copied = dict(row)
    llm_role = cached_llm_role(role_cached)
    llm_open, llm_adaptive = cached_llm_entities(entity_cached, row)

    copied["pred_role_llm"] = llm_role
    copied["pred_entities_llm_open"] = llm_open
    copied["pred_entities_llm_adaptive"] = llm_adaptive

    original_role = row.get("pred_role", "")
    original_entities = row.get("pred_entities", "")
    original_status = row.get("pred_operative_status", "")
    original_relation = row.get("pred_relation", "")
    original_answer = row.get("pred_answer_relevant", "")

    add_variant(
        copied,
        "role_llm_only",
        llm_role,
        original_entities,
        original_status,
        original_relation,
        original_answer,
    )
    add_variant(
        copied,
        "ent_llm_only",
        original_role,
        llm_adaptive,
        original_status,
        original_relation,
        original_answer,
    )
    add_variant(
        copied,
        "full_llm_adaptive",
        llm_role,
        llm_adaptive,
        original_status,
        original_relation,
        original_answer,
    )
    add_variant(
        copied,
        "full_llm_open",
        llm_role,
        llm_open,
        original_status,
        original_relation,
        original_answer,
    )
    add_variant(
        copied,
        "diagnostic_gold_other",
        llm_role,
        llm_adaptive,
        row.get("gold_operative_status", ""),
        row.get("gold_relation", ""),
        row.get("gold_answer_relevant", ""),
    )
    return copied


def empty_counts(rows):
    counts = {}
    for suffix in VARIANT_SUFFIXES:
        counts[suffix] = {
            "empty_role": sum(not row.get(variant_col("pred_role", suffix), "") for row in rows),
            "empty_entities": sum(not row.get(variant_col("pred_entities", suffix), "") for row in rows),
        }
    return counts


def build_dataset(dataset, spec):
    source_rows = read_rows(spec["source"])
    role_cache = read_cache(spec["role_cache"], "LLM role")
    entity_cache = read_cache(spec["entity_cache"], "LLM entity")
    output = []

    role_missing = 0
    entity_missing = 0
    role_parse_failed = 0
    role_invalid = 0
    entity_parse_failed = 0
    joined_both = 0

    for row in source_rows:
        segment_id = row.get("segment_id", "")
        role_cached = role_cache.get(segment_id)
        entity_cached = entity_cache.get(segment_id)
        role_missing += int(role_cached is None)
        entity_missing += int(entity_cached is None)
        role_parse_failed += int(bool(role_cached and role_cached.get("parse_failed")))
        role_invalid += int(bool(role_cached and role_cached.get("invalid_label")))
        entity_parse_failed += int(bool(entity_cached and entity_cached.get("parse_failed")))
        joined_both += int(role_cached is not None and entity_cached is not None)
        output.append(add_columns(row, role_cached, entity_cached))

    fieldnames = list(output[0].keys()) if output else []
    write_rows(spec["prediction"], output, fieldnames)
    return {
        "dataset": dataset,
        "source": str(spec["source"]),
        "prediction": str(spec["prediction"]),
        "rows": len(source_rows),
        "role_cache": str(spec["role_cache"]),
        "role_cache_rows_available": len(role_cache),
        "entity_cache": str(spec["entity_cache"]),
        "entity_cache_rows_available": len(entity_cache),
        "cache_rows_joined_both": joined_both,
        "role_missing": role_missing,
        "entity_missing": entity_missing,
        "role_parse_failed": role_parse_failed,
        "role_invalid": role_invalid,
        "entity_parse_failed": entity_parse_failed,
        "empty_counts": empty_counts(output),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    build_results = [build_dataset(dataset, spec) for dataset, spec in DATASETS.items()]
    summary = {
        "experiment": "llm_full_route_build",
        "offline": True,
        "g_gate": G_GATE,
        "t_link_high": T_LINK_HIGH,
        "broad_canonicals": sorted(BROAD_CANONICALS),
        "build_results": build_results,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    print("llm_full_route_build")
    for row in build_results:
        print(
            f"{row['dataset']}: rows={row['rows']} joined={row['cache_rows_joined_both']} "
            f"role_missing={row['role_missing']} entity_missing={row['entity_missing']} "
            f"role_parse_failed={row['role_parse_failed']} role_invalid={row['role_invalid']} "
            f"entity_parse_failed={row['entity_parse_failed']}"
        )
        print("empty_counts=" + json.dumps(row["empty_counts"], sort_keys=True))
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
