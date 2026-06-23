"""Ablation-only hybrid entity extractor for hybrid_entity_field_dev_eval_v1.

This module combines domain-general mention detection with ontology_v1 linking.
Constants are selected by the experiment orchestrator on train only, then frozen
for dev and true-blind reads. It is not the production ontology or evaluator.
"""

from __future__ import annotations

import argparse
import csv
import difflib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import entity_ontology_v1
from entity_matchers_diagnostic import EmbeddingMatcher, normalize
from extract_entities_domain_general_v1 import dedupe_spans, noun_chunks_topk, proper_quoted


K = 8
T_LINK_FUZZY = 0.7
T_LINK_EMBED = 0.5
T_CLUSTER = 0.72
MAX_ENTITIES_PER_SEG = 10


@dataclass(frozen=True)
class HybridConfig:
    k: int = K
    t_link_fuzzy: float = T_LINK_FUZZY
    t_link_embed: float = T_LINK_EMBED
    t_cluster: float = T_CLUSTER
    max_entities_per_seg: int = MAX_ENTITIES_PER_SEG


CANONICAL_SET = set(entity_ontology_v1.CANONICAL_ENTITIES)
ORDER = {entity: index for index, entity in enumerate(entity_ontology_v1.CANONICAL_ENTITIES)}


def ontology_label_index():
    labels = []
    seen = set()
    for canonical in entity_ontology_v1.CANONICAL_ENTITIES:
        for label in [canonical] + entity_ontology_v1.ENTITY_SYNONYMS.get(canonical, []):
            key = normalize(label)
            if key and key not in seen:
                labels.append((canonical, label, key))
                seen.add(key)
    return labels


ONTOLOGY_LABELS = ontology_label_index()
EMBEDDING_LINK_CACHE = {}


def unique_keep_order(values):
    output = []
    seen = set()
    for value in values:
        text = "" if value is None else str(value).strip()
        key = normalize(text)
        if not key or key in seen:
            continue
        output.append(text)
        seen.add(key)
    return output


def candidate_spans(text, config=HybridConfig()):
    spans = []
    spans.extend(proper_quoted(text))
    spans.extend(noun_chunks_topk(text)[: config.k])
    return dedupe_spans(spans)


def direct_ontology_link(span):
    linked = entity_ontology_v1.normalize_entity(span)
    return linked if linked in CANONICAL_SET else ""


def fuzzy_ontology_link(span, threshold):
    span_norm = normalize(span)
    if not span_norm:
        return ""
    best = (0.0, "")
    for canonical, _label, label_norm in ONTOLOGY_LABELS:
        score = difflib.SequenceMatcher(None, span_norm, label_norm).ratio()
        if score > best[0] or (score == best[0] and ORDER.get(canonical, 9999) < ORDER.get(best[1], 9999)):
            best = (score, canonical)
    return best[1] if best[0] >= threshold else ""


def embedding_ontology_link(span, threshold, embedding_matcher=None):
    if embedding_matcher is None or not embedding_matcher.available:
        return ""
    cache_key = (id(embedding_matcher), span, threshold)
    if cache_key in EMBEDDING_LINK_CACHE:
        return EMBEDDING_LINK_CACHE[cache_key]
    embedding_matcher.prepare([span] + list(entity_ontology_v1.CANONICAL_ENTITIES))
    best = (0.0, "")
    for canonical in entity_ontology_v1.CANONICAL_ENTITIES:
        score = embedding_matcher.similarity(span, canonical)
        if score > best[0] or (score == best[0] and ORDER.get(canonical, 9999) < ORDER.get(best[1], 9999)):
            best = (score, canonical)
    linked = best[1] if best[0] >= threshold else ""
    EMBEDDING_LINK_CACHE[cache_key] = linked
    return linked


def link_span(span, config=HybridConfig(), embedding_matcher=None):
    for linker in (
        lambda: direct_ontology_link(span),
        lambda: fuzzy_ontology_link(span, config.t_link_fuzzy),
        lambda: embedding_ontology_link(span, config.t_link_embed, embedding_matcher),
    ):
        linked = linker()
        if linked:
            return linked, "linked"
    return normalize(span), "open"


def cluster_unlinked_spans(spans, config=HybridConfig(), embedding_matcher=None):
    clusters = []
    for span in unique_keep_order(spans):
        placed = False
        for cluster in clusters:
            label = cluster["label"]
            if embedding_matcher is not None and embedding_matcher.available:
                score = embedding_matcher.similarity(span, label)
            else:
                score = difflib.SequenceMatcher(None, normalize(span), normalize(label)).ratio()
            if score >= config.t_cluster:
                cluster["members"].append(span)
                placed = True
                break
        if not placed:
            clusters.append({"label": span, "members": [span]})
    labels = []
    for cluster in clusters:
        counts = Counter(cluster["members"])
        label = sorted(
            counts,
            key=lambda value: (-counts[value], -len(normalize(value)), normalize(value)),
        )[0]
        labels.append(normalize(label))
    return labels


def extract_entities_hybrid(
    text,
    title="",
    config=HybridConfig(),
    embedding_matcher=None,
    cluster_unlinked=False,
):
    full_text = f"{title or ''} {text or ''}".strip()
    linked = []
    unlinked = []
    for span in candidate_spans(full_text, config):
        entity, kind = link_span(span, config, embedding_matcher)
        if not entity:
            continue
        if kind == "linked":
            linked.append(entity)
        else:
            unlinked.append(entity)
    open_entities = (
        cluster_unlinked_spans(unlinked, config, embedding_matcher)
        if cluster_unlinked
        else unique_keep_order(unlinked)
    )
    ordered = []
    seen = set()
    for entity in linked + open_entities:
        key = entity if entity in CANONICAL_SET else normalize(entity)
        if not key or key in seen:
            continue
        ordered.append(entity)
        seen.add(key)
    ordered.sort(key=lambda entity: (0 if entity in CANONICAL_SET else 1, ORDER.get(entity, 9999), normalize(entity)))
    return ordered[: config.max_entities_per_seg]


def format_entities(entities):
    return "; ".join(entities)


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_predictions(gold_path, out_path, config=HybridConfig(), cluster_unlinked=False, use_embeddings=False):
    embedding_matcher = EmbeddingMatcher.load() if use_embeddings else None
    rows = []
    for row in read_rows(gold_path):
        text = row.get("text") or row.get("segment_text") or ""
        title = row.get("title", "")
        entities = extract_entities_hybrid(text, title, config, embedding_matcher, cluster_unlinked)
        rows.append(
            {
                "segment_id": row.get("segment_id", ""),
                "text": text,
                "gold_entities": row.get("gold_entities", ""),
                "pred_entities": format_entities(entities),
            }
        )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(out_path).open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=["segment_id", "text", "gold_entities", "pred_entities"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--k", type=int, default=K)
    parser.add_argument("--t-link-fuzzy", type=float, default=T_LINK_FUZZY)
    parser.add_argument("--t-link-embed", type=float, default=T_LINK_EMBED)
    parser.add_argument("--t-cluster", type=float, default=T_CLUSTER)
    parser.add_argument("--max-entities-per-seg", type=int, default=MAX_ENTITIES_PER_SEG)
    parser.add_argument("--cluster-unlinked", action="store_true")
    parser.add_argument("--use-embeddings", action="store_true")
    args = parser.parse_args()
    config = HybridConfig(
        k=args.k,
        t_link_fuzzy=args.t_link_fuzzy,
        t_link_embed=args.t_link_embed,
        t_cluster=args.t_cluster,
        max_entities_per_seg=args.max_entities_per_seg,
    )
    rows = write_predictions(args.gold, args.out, config, args.cluster_unlinked, args.use_embeddings)
    print("hybrid_entity_field_dev_eval_v1 extractor")
    print(f"rows={len(rows)}")
    print(f"config={config}")
    print(f"cluster_unlinked={args.cluster_unlinked}")
    print(f"out={args.out}")


if __name__ == "__main__":
    main()
