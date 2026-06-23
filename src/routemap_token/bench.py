"""TokenRouteQA benchmark for token-importance routing."""

from __future__ import annotations

import json
import math
import random
import re
import csv
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context import contextual_features, contextual_importance_score
from .policy import route_action, route_score
from .prior import build_idf, classify_token, discover_corpus_docs, token_prior_score
from .trace import emit_trace


THRESHOLDS = [round(index / 100, 2) for index in range(5, 96, 5)]
LOW_IDF_CLEAR_PERCENTILE = 0.35


@dataclass(frozen=True)
class TokenQASample:
    sample_id: str
    context: str
    question: str
    answer: str
    evidence: str
    needed_phrases: tuple[str, ...] = ()


def load_dataset(root: str | Path = ".") -> tuple[list[TokenQASample], str]:
    samples = _load_real_gold(Path(root))
    if samples:
        return samples, "v1_full_extraction_gold"
    return _fallback_dataset(), "fallback_constructed_token_route_qa"


def score_sample(sample: TokenQASample, idf_map: dict[str, float], threshold: float) -> list[dict[str, Any]]:
    tokens = tokenize_with_spans(sample.context)
    question_tokens = {_normalize_token(token) for token, _, _ in tokenize_with_spans(sample.question) if re.search(r"\w", token)}
    needed_indices, _located, _total = needed_token_indices(sample)
    normalized_tokens = [_normalize_token(token) for token, _start, _end in tokens]
    first_content_indices = _first_content_indices(tokens)
    seen_counts: dict[str, int] = {}
    low_idf_cutoff = _idf_percentile(idf_map, LOW_IDF_CLEAR_PERCENTILE)
    rows: list[dict[str, Any]] = []
    for index, (token, start, end) in enumerate(tokens):
        left = tokens[index - 1][0] if index else None
        right = tokens[index + 1][0] if index + 1 < len(tokens) else None
        normalized = normalized_tokens[index]
        occurrence_index = seen_counts.get(normalized, 0)
        seen_counts[normalized] = occurrence_index + 1
        idf = idf_map.get(normalized, max(idf_map.values(), default=1.0))
        static_class = classify_token(token)
        static_score = token_prior_score(token, idf_map)
        features = contextual_features(
            token,
            question_tokens=question_tokens,
            position_info={
                "index": index,
                "sentence_initial": index == 0 or (index > 0 and tokens[index - 1][0] in {".", "?", "!"}),
                "first_content_token": index in first_content_indices,
                "after_newline": start > 0 and sample.context[start - 1] == "\n",
            },
            neighbors=(left, right),
            idf=idf,
            low_idf_cutoff=low_idf_cutoff,
            occurrence_index=occurrence_index,
        )
        contextual = contextual_importance_score(static_score, features)
        score = route_score(static_score, contextual)
        action = route_action(token, score, threshold=threshold, features=features)
        rows.append(
            {
                "sample_id": sample.sample_id,
                "token": token,
                "static_class": static_class,
                "idf": idf,
                "context_features": features,
                "route_score": score,
                "route_action": action,
                "later_needed": index in needed_indices,
            }
        )
    return rows


def run_benchmark(
    *,
    root: str | Path = ".",
    threshold: float = 0.5,
    trace_path: str | Path | None = None,
    seed: int = 7,
) -> dict[str, Any]:
    samples, dataset_source = load_dataset(root)
    needed_coverage = needed_span_coverage(samples)
    corpus_docs, idf_source = discover_corpus_docs(root)
    idf_map = build_idf(corpus_docs + [sample.context for sample in samples])
    curve: list[dict[str, float]] = []
    rows_by_threshold: dict[float, list[dict[str, Any]]] = {}
    for candidate in THRESHOLDS:
        rows = _score_dataset(samples, idf_map, candidate)
        rows_by_threshold[candidate] = rows
        metrics = _metrics(rows)
        curve.append({"threshold": candidate, **metrics})
    frontier = _frontier_by_tier(curve, rows_by_threshold, seed=seed)
    best_02 = frontier["lt_0_02"]
    best_01 = frontier["lt_0_01"]
    best_05 = frontier["lt_0_05"]
    selected_rows = rows_by_threshold.get(best_02["threshold"], _score_dataset(samples, idf_map, threshold))
    if trace_path is not None:
        emit_trace(trace_path, selected_rows)
    minimum = best_02["token_reduction"] >= 0.30 and best_02["recall_loss"] < 0.02
    strong = 0.50 <= best_01["token_reduction"] <= 0.70 and best_01["recall_loss"] < 0.01
    return {
        "dataset_source": dataset_source,
        "dataset_size": len(samples),
        "needed_span_coverage": needed_coverage["coverage"],
        "needed_phrases_total": needed_coverage["total"],
        "needed_phrases_located": needed_coverage["located"],
        "idf_source": idf_source,
        "threshold_curve": curve,
        "best_recall_loss_lt_02": best_02,
        "best_recall_loss_lt_01": best_01,
        "best_recall_loss_lt_05": best_05,
        "frontier": frontier,
        "baselines": {
            key: {
                "random_drop": {
                    "token_reduction": value["token_reduction"],
                    "answer_span_recall": value["random_drop_recall"],
                    "recall_loss": 1.0 - value["random_drop_recall"],
                },
                "naive_stopword_drop": {
                    "token_reduction": value["token_reduction"],
                    "answer_span_recall": value["naive_stopword_recall"],
                    "recall_loss": 1.0 - value["naive_stopword_recall"],
                },
            }
            for key, value in frontier.items()
        },
        "policy_vs_random_recall_delta": best_02["policy_vs_random_recall_delta"],
        "policy_vs_naive_stopword_recall_delta": best_02["policy_vs_naive_stopword_recall_delta"],
        "minimum_bar": "PASS" if minimum else "FAIL",
        "strong_bar": "PASS" if strong else "FAIL",
        "trace_rows": selected_rows,
    }


def card(result: dict[str, Any]) -> str:
    best02 = result["best_recall_loss_lt_02"]
    best01 = result["best_recall_loss_lt_01"]
    best05 = result["best_recall_loss_lt_05"]
    frontier = result["frontier"]
    lines = [
        "# TokenRouteQA",
        "",
        f"Dataset: `{result['dataset_source']}` ({result['dataset_size']} samples)",
        "",
        f"Needed span coverage: `{result['needed_span_coverage']:.3f}` ({result['needed_phrases_located']}/{result['needed_phrases_total']})",
        "",
        f"IDF source: `{result['idf_source']}`",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| max_reduction_at_recall_loss_lt_0.02 | {best02['token_reduction']:.3f} |",
        f"| recall_loss_at_best_0.02 | {best02['recall_loss']:.3f} |",
        f"| max_reduction_at_recall_loss_lt_0.01 | {best01['token_reduction']:.3f} |",
        f"| recall_loss_at_best_0.01 | {best01['recall_loss']:.3f} |",
        f"| max_reduction_at_recall_loss_lt_0.05 | {best05['token_reduction']:.3f} |",
        f"| recall_loss_at_best_0.05 | {best05['recall_loss']:.3f} |",
        f"| policy_vs_random_recall_delta | {result['policy_vs_random_recall_delta']:.3f} |",
        f"| policy_vs_naive_stopword_recall_delta | {result['policy_vs_naive_stopword_recall_delta']:.3f} |",
        f"| minimum_bar | {result['minimum_bar']} |",
        f"| strong_bar | {result['strong_bar']} |",
        "",
        "## Frontier",
        "",
        "| Recall loss tier | Threshold | Reduction | Recall loss | Policy-vs-random recall delta | Policy-vs-IDF-stopword recall delta |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in ("lt_0_01", "lt_0_02", "lt_0_05"):
        row = frontier[key]
        lines.append(
            f"| {key.replace('lt_', '<').replace('_', '.')} | {row['threshold']:.2f} | {row['token_reduction']:.3f} | {row['recall_loss']:.3f} | {row['policy_vs_random_recall_delta']:.3f} | {row['policy_vs_naive_stopword_recall_delta']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Full Curve",
            "",
            "| Threshold | Reduction | Recall loss |",
            "| ---: | ---: | ---: |",
        ]
    )
    for row in result["threshold_curve"]:
        lines.append(f"| {row['threshold']:.2f} | {row['token_reduction']:.3f} | {row['recall_loss']:.3f} |")
    return "\n".join(lines)


def baseline_metrics(policy_rows: list[dict[str, Any]], matched_reduction: float, seed: int = 7) -> dict[str, dict[str, float]]:
    total = len(policy_rows)
    drop_n = round(total * matched_reduction)
    needed = [row for row in policy_rows if row["later_needed"]]
    keep_all = _baseline_result(policy_rows, set())
    rng = random.Random(seed)
    random_drop = _baseline_result(policy_rows, set(rng.sample(range(total), drop_n)))
    naive_order = sorted(
        range(total),
        key=lambda index: (
            float(policy_rows[index]["idf"]),
            0 if policy_rows[index]["static_class"] in {"function_word", "punctuation"} else 1,
            index,
        ),
    )
    naive_drop = set(naive_order[:drop_n])
    return {
        "keep_all": keep_all,
        "random_drop": random_drop,
        "naive_stopword_drop": _baseline_result(policy_rows, naive_drop),
    }


def tokenize_with_spans(text: str) -> list[tuple[str, int, int]]:
    return [(match.group(0), match.start(), match.end()) for match in re.finditer(r"https?://\S+|\[\d+\]|[A-Za-z]+(?:n't)?|\d+|[^\w\s]", text)]


def _score_dataset(samples: list[TokenQASample], idf_map: dict[str, float], threshold: float) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sample in samples:
        rows.extend(score_sample(sample, idf_map, threshold))
    return rows


def _metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    total = len(rows)
    cheap = len([row for row in rows if row["route_action"] == "cheap"])
    needed = [row for row in rows if row["later_needed"]]
    kept_needed = [row for row in needed if row["route_action"] == "keep"]
    recall = 1.0 if not needed else len(kept_needed) / len(needed)
    return {"token_reduction": cheap / total, "answer_span_recall": recall, "recall_loss": 1.0 - recall}


def _baseline_result(rows: list[dict[str, Any]], drop_indices: set[int]) -> dict[str, float]:
    needed = [index for index, row in enumerate(rows) if row["later_needed"]]
    kept = [index for index in needed if index not in drop_indices]
    recall = 1.0 if not needed else len(kept) / len(needed)
    return {"token_reduction": len(drop_indices) / len(rows), "answer_span_recall": recall, "recall_loss": 1.0 - recall}


def _best_under_loss(curve: list[dict[str, float]], max_loss: float) -> dict[str, float]:
    passing = [row for row in curve if row["recall_loss"] < max_loss]
    if not passing:
        return min(curve, key=lambda row: row["recall_loss"])
    return max(passing, key=lambda row: (row["token_reduction"], -row["recall_loss"]))


def _frontier_by_tier(
    curve: list[dict[str, float]],
    rows_by_threshold: dict[float, list[dict[str, Any]]],
    *,
    seed: int,
) -> dict[str, dict[str, float]]:
    frontier: dict[str, dict[str, float]] = {}
    for key, max_loss in (("lt_0_01", 0.01), ("lt_0_02", 0.02), ("lt_0_05", 0.05)):
        best = dict(_best_under_loss(curve, max_loss))
        rows = rows_by_threshold[best["threshold"]]
        baselines = baseline_metrics(rows, best["token_reduction"], seed=seed)
        policy_recall = 1.0 - best["recall_loss"]
        best.update(
            {
                "random_drop_recall": baselines["random_drop"]["answer_span_recall"],
                "naive_stopword_recall": baselines["naive_stopword_drop"]["answer_span_recall"],
                "policy_vs_random_recall_delta": policy_recall - baselines["random_drop"]["answer_span_recall"],
                "policy_vs_naive_stopword_recall_delta": policy_recall - baselines["naive_stopword_drop"]["answer_span_recall"],
            }
        )
        frontier[key] = best
    return frontier


def needed_token_indices(sample: TokenQASample) -> tuple[set[int], int, int]:
    tokens = tokenize_with_spans(sample.context)
    token_values = [_normalize_token(token) for token, _start, _end in tokens]
    needed: set[int] = set()
    phrases = [phrase for phrase in sample.needed_phrases if phrase.strip()]
    located = 0
    for phrase in phrases:
        phrase_tokens = [_normalize_token(token) for token, _start, _end in tokenize_with_spans(phrase) if re.search(r"\w", token)]
        phrase_tokens = [token for token in phrase_tokens if token]
        if not phrase_tokens:
            continue
        matched_indices = _locate_token_run(token_values, phrase_tokens)
        if not matched_indices and len(phrase_tokens) >= 3:
            matched_indices = _locate_longest_partial_run(token_values, phrase_tokens)
        if matched_indices:
            needed.update(matched_indices)
            located += 1
    return needed, located, len(phrases)


def needed_span_coverage(samples: list[TokenQASample]) -> dict[str, float | int]:
    located = 0
    total = 0
    for sample in samples:
        _needed, sample_located, sample_total = needed_token_indices(sample)
        located += sample_located
        total += sample_total
    return {"located": located, "total": total, "coverage": 0.0 if total == 0 else located / total}


def _load_real_gold(root: Path) -> list[TokenQASample]:
    segments = _read_segments(root / "data" / "v1" / "gold" / "v1_full_extraction_gold_v1.csv")
    segments.extend(_read_segments(root / "data" / "gold" / "gold_segments_filled.csv"))
    if not segments:
        return []
    qa_by_segment = _read_qa(root / "data" / "v1" / "gold" / "v1_qa_targets.csv")
    extra_qa = _read_qa(root / "data" / "gold" / "gold_qa_filled.csv")
    qa_by_segment.update({key: value for key, value in extra_qa.items() if key not in qa_by_segment})
    samples: list[TokenQASample] = []
    seen: set[str] = set()
    for row in segments:
        segment_id = row.get("segment_id", "").strip()
        text = row.get("text", "").strip()
        if not segment_id or not text or segment_id in seen:
            continue
        seen.add(segment_id)
        qa = qa_by_segment.get(segment_id, {})
        entities = _split_phrases(row.get("gold_entities", ""))
        answer = qa.get("gold_answer", "").strip()
        phrases = list(entities)
        if answer:
            phrases.append(answer)
        if not phrases:
            relevance = str(row.get("gold_answer_relevant", "")).strip().lower()
            if relevance == "yes":
                phrases.append(row.get("gold_role", "").strip())
        samples.append(
            TokenQASample(
                sample_id=segment_id,
                context=text,
                question=qa.get("query", "").strip(),
                answer=answer,
                evidence="; ".join(entities),
                needed_phrases=tuple(dict.fromkeys(phrase for phrase in phrases if phrase)),
            )
        )
    return samples


def _read_segments(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_qa(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    result: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            segment_field = row.get("gold_required_segment_ids", "")
            for segment_id in re.split(r"[|;]", segment_field):
                key = segment_id.strip()
                if key and key not in result:
                    result[key] = row
    return result


def _split_phrases(value: str) -> list[str]:
    return [part.strip() for part in re.split(r"[|;]", value or "") if part.strip()]


def _normalize_token(token: str) -> str:
    normalized = token.strip(string.punctuation).lower()
    if len(normalized) > 3 and normalized.endswith("s") and not normalized.endswith("ss"):
        normalized = normalized[:-1]
    return normalized


def _locate_token_run(token_values: list[str], phrase_tokens: list[str]) -> set[int]:
    found: set[int] = set()
    width = len(phrase_tokens)
    for start in range(0, len(token_values) - width + 1):
        if token_values[start:start + width] == phrase_tokens:
            found.update(range(start, start + width))
    return found


def _locate_longest_partial_run(token_values: list[str], phrase_tokens: list[str]) -> set[int]:
    for width in range(len(phrase_tokens) - 1, 1, -1):
        for phrase_start in range(0, len(phrase_tokens) - width + 1):
            found = _locate_token_run(token_values, phrase_tokens[phrase_start:phrase_start + width])
            if found:
                return found
    return set()


def _first_content_indices(tokens: list[tuple[str, int, int]]) -> set[int]:
    indices: set[int] = set()
    pending = True
    for index, (token, _start, _end) in enumerate(tokens):
        if re.fullmatch(r"[.!?]", token):
            pending = True
            continue
        if pending and re.search(r"\w", token):
            indices.add(index)
            pending = False
    return indices


def _idf_percentile(idf_map: dict[str, float], percentile: float) -> float:
    values = sorted(idf_map.values())
    if not values:
        return 1.0
    index = min(len(values) - 1, max(0, math.floor((len(values) - 1) * percentile)))
    return values[index]


def _fallback_dataset() -> list[TokenQASample]:
    return [
        TokenQASample("q1", "The island artist, in the old local note, did not sign the treaty in London [1].", "Who did not sign?", "island artist", "not", ("island artist", "not")),
        TokenQASample("q2", "OpenAI released the route memo in 2027, and the memo was in the file, but it was not final.", "What was not final?", "final", "not final", ("final", "not final")),
        TokenQASample("q3", "The bridge formula F(118), in a long note with the and of and to, connects to island evidence without a citation.", "Which formula connects to island evidence?", "F(118)", "F(118)", ("F(118)",)),
        TokenQASample("q4", "Return the JSON only; in the draft and the note, never include the debug token after the answer.", "What is the debug token?", "the debug token", "the debug token", ("the debug token",)),
        TokenQASample("q5", "London artist Mira kept the small code token def in the notebook and in the margin.", "Which code token was kept?", "def", "def", ("def",)),
        TokenQASample("q6", "The 2027 audit says the claim can stand in the report unless evidence is missing from the appendix.", "When can the claim fail?", "missing", "unless", ("missing", "unless")),
    ]


__all__ = ["TokenQASample", "baseline_metrics", "card", "load_dataset", "needed_span_coverage", "needed_token_indices", "run_benchmark", "score_sample", "tokenize_with_spans"]
