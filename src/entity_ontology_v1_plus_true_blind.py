"""Ablation-only expanded entity ontology for true_blind_entity_ontology_alignment_v1.

This module must not be used as production ontology_v1. It copies ontology_v1,
then adds frozen true-blind freeform gold entities as extra canonical labels so
Option B can quantify ontology coverage as a named ablation.
"""

import json
from pathlib import Path

import entity_ontology_v1 as base


ROOT = Path(__file__).resolve().parents[1]
FROZEN_GOLD = ROOT / "data/v1/true_blind_natural_language/annotation/true_blind_gold_frozen.csv"


def _clean(value: str) -> str:
    return "" if value is None else str(value).strip()


def _parse_entities(value: str) -> list[str]:
    raw = _clean(value)
    if not raw:
        return []
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [_clean(item) for item in parsed if _clean(item)]
        except json.JSONDecodeError:
            pass
    delimiter = ";" if ";" in raw else ","
    return [_clean(item) for item in raw.split(delimiter) if _clean(item)]


def _gold_entities() -> list[str]:
    if not FROZEN_GOLD.exists():
        return []
    import csv

    found = set()
    with FROZEN_GOLD.open("r", encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            for entity in _parse_entities(row.get("gold_entities", "")):
                found.add(entity)
    return sorted(found, key=lambda value: value.lower())


CANONICAL_ENTITIES = list(base.CANONICAL_ENTITIES)
ENTITY_SYNONYMS = {key: list(values) for key, values in base.ENTITY_SYNONYMS.items()}

for entity in _gold_entities():
    if base.normalize_entity(entity) in base.CANONICAL_ENTITIES:
        continue
    if entity.lower() not in {item.lower() for item in CANONICAL_ENTITIES}:
        CANONICAL_ENTITIES.append(entity)
        ENTITY_SYNONYMS[entity] = sorted({entity, entity.lower()})

NORMALIZED = {entity.lower(): entity for entity in CANONICAL_ENTITIES}
ORDER = {entity: index for index, entity in enumerate(CANONICAL_ENTITIES)}


def normalize_entity(entity: str) -> str:
    value = _clean(entity)
    if not value:
        return ""
    lowered = value.lower()
    if lowered in NORMALIZED:
        return NORMALIZED[lowered]
    for canonical, synonyms in ENTITY_SYNONYMS.items():
        if lowered == canonical.lower() or lowered in {synonym.lower() for synonym in synonyms}:
            return canonical
    return value


def split_entity_set(value: str) -> set[str]:
    entities = set()
    for part in _parse_entities(value):
        normalized = normalize_entity(part)
        if normalized:
            entities.add(normalized)
    return entities


def format_entity_set(entities: set[str]) -> str:
    return "; ".join(sorted(entities, key=lambda entity: (ORDER.get(entity, len(ORDER)), entity.lower())))
