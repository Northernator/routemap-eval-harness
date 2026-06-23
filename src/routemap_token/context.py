"""Contextual token-importance features.

Gold answer and evidence labels are intentionally absent from these APIs.
Inference-time signals are limited to question overlap, entity flag,
negation/modal markers, position, citation boundaries, and neighbors.
"""

from __future__ import annotations

import string

from .prior import classify_token


def contextual_features(
    token: str,
    *,
    question_tokens: set[str],
    position_info: dict[str, int | bool],
    neighbors: tuple[str | None, str | None],
    idf: float | None = None,
    low_idf_cutoff: float | None = None,
    occurrence_index: int = 0,
) -> dict[str, bool]:
    lower = _normalize_for_overlap(token)
    left, right = neighbors
    neighbor_classes = {classify_token(item) for item in (left, right) if item is not None}
    token_class = classify_token(token)
    low_idf = idf is not None and low_idf_cutoff is not None and idf <= low_idf_cutoff
    repeated_non_first = occurrence_index > 0
    sentence_initial = bool(position_info.get("sentence_initial")) or bool(position_info.get("after_newline")) or bool(position_info.get("first_content_token"))
    query_overlap = lower in question_tokens
    protected_context = (
        token_class in {"citation", "negation", "code_token", "instruction"}
        or "negation" in neighbor_classes
        or "citation" in neighbor_classes
        or sentence_initial
        or str(token) in {"\"", "'"}
        or left in {"\"", "'"}
        or right in {"\"", "'"}
    )
    return {
        "query_overlap": query_overlap,
        "entity_flag": token_class == "named_entity",
        "negation_modal": token_class == "negation" or "negation" in neighbor_classes,
        "table_header_or_sentence_initial": sentence_initial,
        "citation_boundary": token_class == "citation" or "citation" in neighbor_classes,
        "quote_boundary": str(token) in {"\"", "'"} or left in {"\"", "'"} or right in {"\"", "'"},
        "first_content_token": bool(position_info.get("first_content_token")),
        "low_idf": bool(low_idf),
        "repeated_non_first": repeated_non_first,
        "low_information": bool(low_idf and repeated_non_first),
        "explicit_clear": bool(
            token_class in {"named_entity", "number", "formula"}
            and low_idf
            and repeated_non_first
            and not query_overlap
            and not protected_context
        ),
    }


def contextual_importance_score(static_score: float, features: dict[str, bool]) -> float:
    score = static_score
    if features.get("query_overlap"):
        score += 0.34
    if features.get("entity_flag"):
        score += 0.16
    if features.get("negation_modal"):
        score += 0.32
    if features.get("table_header_or_sentence_initial"):
        score += 0.12
    if features.get("citation_boundary"):
        score += 0.16
    if features.get("quote_boundary"):
        score += 0.10
    if features.get("low_information"):
        score -= 0.18
    return max(0.0, min(1.0, score))


def _normalize_for_overlap(token: str) -> str:
    normalized = str(token).strip(string.punctuation).lower()
    if len(normalized) > 3 and normalized.endswith("s") and not normalized.endswith("ss"):
        normalized = normalized[:-1]
    return normalized


__all__ = ["contextual_features", "contextual_importance_score"]
