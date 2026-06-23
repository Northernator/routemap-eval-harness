"""Ablation-only precision-controlled hybrid entity extractor v2.

hybrid_entity_field_dev_eval_v2 uses train-only parameter selection and frozen
dev/true-blind reads. This module does not modify ontology_v1 or any evaluator.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import math
import re
import string
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import entity_ontology_v1
from entity_matchers_diagnostic import normalize
from extract_entities_domain_general_v1 import STOPWORDS, noun_chunks_topk, proper_quoted, span_words


K = 6
MAX_PER_SEG = 6
T_LINK_HIGH = 0.9
G_GATE = 1

BROAD_CANONICALS = {
    "controls",
    "evaluation",
    "governance",
    "retrieval",
    "RouteMap",
    "RouteMap segment",
    "source context",
    "risk management",
}

GENERIC_LOWER_UNIGRAMS = {
    "assistant",
    "case",
    "cases",
    "data",
    "document",
    "evidence",
    "field",
    "flow",
    "item",
    "layer",
    "model",
    "note",
    "object",
    "policy",
    "process",
    "record",
    "request",
    "requests",
    "review",
    "route",
    "routing",
    "service",
    "signal",
    "status",
    "step",
    "system",
    "task",
    "team",
    "tool",
    "user",
    "workflow",
}


@dataclass(frozen=True)
class HybridV2Config:
    k: int = K
    max_per_seg: int = MAX_PER_SEG
    t_link_high: float = T_LINK_HIGH
    g_gate: int = G_GATE


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
EXACT_LABEL_TO_CANONICAL = {key: canonical for canonical, _label, key in ONTOLOGY_LABELS}


def clean_span(value):
    text = "" if value is None else str(value).strip()
    return text.strip(string.whitespace + "\"'`.,;:()[]{}<>")


def unique_keep_order(values):
    output = []
    seen = set()
    for value in values:
        span = clean_span(value)
        key = normalize(span)
        if not key or key in seen:
            continue
        output.append(span)
        seen.add(key)
    return output


def is_quoted_span(text, span):
    escaped = re.escape(clean_span(span))
    return bool(re.search(rf"[\"']{escaped}[\"']", text))


def is_pure_number_or_punctuation(span):
    text = clean_span(span)
    return not text or bool(re.fullmatch(r"[\W\d_]+", text))


def segment_token_counts(text):
    return Counter(normalize(token) for token in re.findall(r"[A-Za-z0-9][\w&/-]*", text) if normalize(token))


def is_low_specificity_unigram(span, counts):
    words = span_words(span)
    if len(words) != 1:
        return False
    word = words[0]
    norm = normalize(word)
    if not norm:
        return True
    if norm in STOPWORDS:
        return True
    return word.islower() and counts.get(norm, 0) <= 1 and norm in GENERIC_LOWER_UNIGRAMS


def specificity_score(span, text, counts):
    words = [word for word in span_words(span) if normalize(word) and normalize(word) not in STOPWORDS]
    num_content_words = len(words)
    has_capital = any(char.isupper() for char in span)
    quoted = is_quoted_span(text, span)
    freq = max((counts.get(normalize(word), 0) for word in words), default=0)
    return num_content_words + (0.5 if has_capital else 0.0) + (0.25 if quoted else 0.0) + math.log1p(freq)


def candidate_spans(text, config=HybridV2Config()):
    proper = proper_quoted(text)
    chunks = noun_chunks_topk(text)[: config.k]
    return unique_keep_order(proper + chunks)


def filtered_spans(text, config=HybridV2Config()):
    counts = segment_token_counts(text)
    scored = []
    for index, span in enumerate(candidate_spans(text, config)):
        if is_pure_number_or_punctuation(span):
            continue
        if is_low_specificity_unigram(span, counts):
            continue
        score = specificity_score(span, text, counts)
        if score <= 0:
            continue
        scored.append((score, -len(span_words(span)), index, span))
    scored.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [span for _score, _length, _index, span in scored[: config.max_per_seg]]


def exact_link(span):
    key = normalize(span)
    return EXACT_LABEL_TO_CANONICAL.get(key, "")


def fuzzy_link(span, threshold):
    span_norm = normalize(span)
    if not span_norm:
        return ""
    best = (0.0, "")
    for canonical, _label, label_norm in ONTOLOGY_LABELS:
        if canonical in BROAD_CANONICALS:
            continue
        score = difflib.SequenceMatcher(None, span_norm, label_norm).ratio()
        if score > best[0] or (score == best[0] and ORDER.get(canonical, 9999) < ORDER.get(best[1], 9999)):
            best = (score, canonical)
    return best[1] if best[0] >= threshold else ""


def link_span(span, config=HybridV2Config()):
    exact = exact_link(span)
    if exact:
        return exact, "exact"
    fuzzy = fuzzy_link(span, config.t_link_high)
    if fuzzy:
        return fuzzy, "fuzzy"
    return normalize(span), "open"


def ontology_hits(text, title=""):
    return entity_ontology_v1.split_entity_set(entity_ontology_v1.extract_entities_ontology_v1(text, title))


def ordered_entities(entities):
    output = []
    seen = set()
    for entity in entities:
        key = entity if entity in CANONICAL_SET else normalize(entity)
        if not key or key in seen:
            continue
        output.append(entity)
        seen.add(key)
    output.sort(key=lambda entity: (0 if entity in CANONICAL_SET else 1, ORDER.get(entity, 9999), normalize(entity)))
    return output


def extract_entities_hybrid_v2(text, title="", config=HybridV2Config()):
    text = "" if text is None else str(text)
    title = "" if title is None else str(title)
    full_text = f"{title} {text}".strip()
    hits = ontology_hits(text, title)
    spans = filtered_spans(full_text, config)
    linked = []
    open_spans = []
    exact_linked = []
    for span in spans:
        entity, kind = link_span(span, config)
        if kind == "exact":
            exact_linked.append(entity)
        elif kind == "fuzzy":
            linked.append(entity)
        elif entity:
            open_spans.append(entity)
    if len(hits) >= config.g_gate:
        entities = list(hits) + exact_linked
    else:
        entities = list(hits) + exact_linked + linked + open_spans
    return ordered_entities(entities)


def format_entities(entities):
    return "; ".join(entities)


def read_rows(path):
    with Path(path).open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def write_predictions(gold_path, out_path, config=HybridV2Config()):
    rows = []
    for row in read_rows(gold_path):
        text = row.get("text") or row.get("segment_text") or ""
        title = row.get("title", "")
        rows.append(
            {
                "segment_id": row.get("segment_id", ""),
                "text": text,
                "gold_entities": row.get("gold_entities", ""),
                "pred_entities": format_entities(extract_entities_hybrid_v2(text, title, config)),
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
    parser.add_argument("--max-per-seg", type=int, default=MAX_PER_SEG)
    parser.add_argument("--t-link-high", type=float, default=T_LINK_HIGH)
    parser.add_argument("--g-gate", type=int, default=G_GATE)
    args = parser.parse_args()
    config = HybridV2Config(args.k, args.max_per_seg, args.t_link_high, args.g_gate)
    rows = write_predictions(args.gold, args.out, config)
    print("hybrid_entity_field_dev_eval_v2 extractor")
    print(f"rows={len(rows)}")
    print(f"config={config}")
    print(f"out={args.out}")


if __name__ == "__main__":
    main()
