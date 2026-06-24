"""Token-importance routing prior for RouteMap."""

from __future__ import annotations

from .bench import TokenQASample, run_benchmark, score_sample
from .context import contextual_features, contextual_importance_score
from .policy import route_action, route_score
from .prior import build_idf, classify_token, discover_corpus_docs, token_prior_score
from .routers import classify_element, route_passage, route_passage_detail, run_comparison, score_for_mode
from .trace import emit_trace


__all__ = [
    "TokenQASample",
    "build_idf",
    "classify_element",
    "classify_token",
    "contextual_features",
    "contextual_importance_score",
    "discover_corpus_docs",
    "emit_trace",
    "route_action",
    "route_passage",
    "route_passage_detail",
    "route_score",
    "run_benchmark",
    "run_comparison",
    "score_for_mode",
    "score_sample",
    "token_prior_score",
]
