import csv
import json
from pathlib import Path

from entity_ontology_v1 import CANONICAL_ENTITIES, normalize_entity


ROOT = Path(__file__).resolve().parents[1]
ABLATION_ROOT = ROOT / "data/v1/true_blind_natural_language/ablations/entity_ontology_alignment_v1"
ALIAS_DIR = ABLATION_ROOT / "alias_map"
CANDIDATES = ROOT / "data/v1/true_blind_natural_language/audits/entity_alignment/TRUE_BLIND_ENTITY_ALIAS_CANDIDATES.csv"
FROZEN_GOLD = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"
REVIEW_OUT = ALIAS_DIR / "true_blind_entity_alias_map_v1_REVIEW.csv"
APPLIED_OUT = ALIAS_DIR / "true_blind_entity_alias_map_v1.csv"

REVIEW_COLUMNS = [
    "gold_entity",
    "mapped_canonical",
    "confidence",
    "support_count",
    "example_rows",
    "reason",
    "approved",
]
APPLIED_COLUMNS = ["gold_entity", "mapped_canonical"]


def clean(value):
    return "" if value is None else str(value).strip()


def canonical_or_blank(value):
    normalized = normalize_entity(clean(value))
    return normalized if normalized in CANONICAL_ENTITIES else ""


def parse_entities(value):
    raw = clean(value)
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [clean(item).lower() for item in parsed if clean(item)]
        except json.JSONDecodeError:
            pass
    delimiter = ";" if ";" in raw else ","
    return [clean(item).lower() for item in raw.split(delimiter) if clean(item)]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def unique_gold_entities():
    entities = set()
    for row in read_csv(FROZEN_GOLD):
        entities.update(parse_entities(row.get("gold_entities", "")))
    return sorted(entities)


def build_review_rows(gold_entities):
    by_gold = {}
    for row in read_csv(CANDIDATES):
        gold_entity = clean(row.get("gold_entity")).lower()
        if not gold_entity:
            continue
        mapped = canonical_or_blank(row.get("predicted_entity", ""))
        confidence = clean(row.get("confidence"))
        approved = "yes" if confidence in {"high", "medium"} and mapped else ""
        current = by_gold.get(gold_entity)
        candidate = {
            "gold_entity": gold_entity,
            "mapped_canonical": mapped,
            "confidence": confidence or "none",
            "support_count": clean(row.get("support_count")) or "0",
            "example_rows": clean(row.get("example_rows")),
            "reason": clean(row.get("reason")),
            "approved": approved,
        }
        rank = {"high": 0, "medium": 1, "low": 2, "none": 3}
        if current is None or rank.get(candidate["confidence"], 3) < rank.get(current["confidence"], 3):
            by_gold[gold_entity] = candidate
    for entity in gold_entities:
        if entity not in by_gold:
            by_gold[entity] = {
                "gold_entity": entity,
                "mapped_canonical": "",
                "confidence": "none",
                "support_count": "0",
                "example_rows": "",
                "reason": "no_candidate",
                "approved": "",
            }
    return [by_gold[entity] for entity in sorted(by_gold)]


def applied_rows(review_rows):
    rows = []
    seen = set()
    for row in review_rows:
        if clean(row.get("approved")).lower() != "yes":
            continue
        mapped = canonical_or_blank(row.get("mapped_canonical"))
        gold_entity = clean(row.get("gold_entity")).lower()
        if not mapped or not gold_entity or gold_entity in seen:
            continue
        seen.add(gold_entity)
        rows.append({"gold_entity": gold_entity, "mapped_canonical": mapped})
    return rows


def print_stats(gold_entities, review_rows, applied):
    mapped_high_medium = sum(
        1
        for row in review_rows
        if row["confidence"] in {"high", "medium"}
        and clean(row.get("approved")).lower() == "yes"
        and canonical_or_blank(row.get("mapped_canonical"))
    )
    mapped_low_approved = sum(
        1
        for row in review_rows
        if row["confidence"] == "low"
        and clean(row.get("approved")).lower() == "yes"
        and canonical_or_blank(row.get("mapped_canonical"))
    )
    total = len(applied)
    coverage = total / len(gold_entities) if gold_entities else 0.0
    print("true_blind_entity_alias_map_v1")
    print(f"unique_gold_entities={len(gold_entities)}")
    print(f"mapped_high_medium={mapped_high_medium}")
    print(f"mapped_low_approved={mapped_low_approved}")
    print(f"total_applied={total}")
    print(f"coverage_fraction={coverage:.6f}")
    print(f"review_csv={REVIEW_OUT.relative_to(ROOT)}")
    print(f"applied_csv={APPLIED_OUT.relative_to(ROOT)}")


def main():
    gold_entities = unique_gold_entities()
    review_rows = build_review_rows(gold_entities)
    applied = applied_rows(review_rows)
    write_csv(REVIEW_OUT, review_rows, REVIEW_COLUMNS)
    write_csv(APPLIED_OUT, applied, APPLIED_COLUMNS)
    print_stats(gold_entities, review_rows, applied)


if __name__ == "__main__":
    main()
