"""Risk-aware token routing policy."""

from __future__ import annotations

from .prior import classify_token


RISK_KEEP_CLASSES = {"negation", "number", "formula", "code_token", "citation", "named_entity", "instruction"}
ALWAYS_KEEP_CLASSES = {"negation", "code_token", "citation", "instruction"}
CLEARABLE_KEEP_CLASSES = {"number", "formula", "named_entity"}


def route_score(static_score: float, contextual_score: float) -> float:
    return max(0.0, min(1.0, (0.35 * static_score) + (0.65 * contextual_score)))


def route_action(token: str, score: float, *, threshold: float, features: dict[str, bool] | None = None) -> str:
    cls = classify_token(token)
    signals = features or {}
    if cls in ALWAYS_KEEP_CLASSES:
        return "keep"
    if cls in CLEARABLE_KEEP_CLASSES and not _explicit_clear(signals):
        return "keep"
    if cls in {"function_word", "punctuation"}:
        if signals.get("query_overlap") or signals.get("negation_modal") or signals.get("citation_boundary") or signals.get("quote_boundary"):
            return "keep"
        return "cheap" if score < threshold else "keep"
    return "cheap" if score < threshold else "keep"


def _explicit_clear(features: dict[str, bool]) -> bool:
    return bool(features.get("explicit_clear"))


__all__ = ["route_action", "route_score"]
