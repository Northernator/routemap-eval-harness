"""Compare token vs element vs codon routing on the SAME TokenRouteQA benchmark.

Everything except the per-token routing signal is reused verbatim from
routemap_token (tokenizer, gold loading, needed-span labels, the recall/reduction
frontier, the random + IDF-stopword baselines). So any frontier difference is the
routing signal alone, measured no-leak on the identical 99 gold segments.

Modes:
  token        : routemap_token.run_benchmark (existing per-token class prior) -- baseline
  element      : per-token functional ELEMENT classes (richer tagset)
  codon_gate   : element scoring, but negation/number/entity kept only when the
                 3-token codon is load-bearing or it overlaps the question
                 (the faithful "context-gate the force-keep" hypothesis)
  codon_boost  : element scoring + a codon-value score boost (over-protect variant)
"""

from __future__ import annotations

import re
from typing import Any

from routemap_token.bench import (
    THRESHOLDS,
    _frontier_by_tier,
    _metrics,
    _normalize_token,
    load_dataset,
    needed_span_coverage,
    needed_token_indices,
    run_benchmark,
    tokenize_with_spans,
)
from routemap_token.prior import build_idf, discover_corpus_docs

from .elements import ELEMENT_WEIGHT, best_codon_value, classify_element

HARD_KEEP = {"CODE", "CITATION", "INSTRUCT", "QUOTE"}
GATED_KEEP = {"NEGATION", "MODAL", "NUMBER", "DATE", "THRESHOLD", "FORMULA",
              "ENTITY", "REQUIRE", "DEFINE", "CONDITION", "RISK", "CONTRADICT", "SYSTEM"}
ELEMENT_ALWAYS = {"NEGATION", "CODE", "CITATION", "INSTRUCT", "RISK"}
ELEMENT_CLEARABLE = {"NUMBER", "DATE", "THRESHOLD", "FORMULA", "ENTITY", "MODAL",
                     "REQUIRE", "DEFINE", "CONDITION"}
WEAK_ELEMENTS = {"FUNCTION", "BOUNDARY", "CONNECTOR", "SEQUENCE", "EXCEPTION"}
CODON_LOADBEARING_FLOOR = 0.60  # set a priori, not tuned on this test set
MODES = ("element", "codon_gate", "codon_boost")


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _score_sample(sample, idf_map: dict[str, float], threshold: float, mode: str) -> list[dict[str, Any]]:
    tokens = tokenize_with_spans(sample.context)
    element_seq = [classify_element(tok) for tok, _s, _e in tokens]
    question_tokens = {_normalize_token(t) for t, _s, _e in tokenize_with_spans(sample.question) if re.search(r"\w", t)}
    needed_indices, _loc, _tot = needed_token_indices(sample)
    max_idf = max(idf_map.values(), default=2.0)
    rows: list[dict[str, Any]] = []
    for i, (token, _s, _e) in enumerate(tokens):
        el = element_seq[i]
        norm = _normalize_token(token)
        idf = idf_map.get(norm, max_idf)
        idf_norm = _clamp((idf - 1.0) / 2.0)
        qov = norm in question_tokens
        base = ELEMENT_WEIGHT.get(el, 0.45)
        cv = best_codon_value(element_seq, i)
        if mode == "codon_boost":
            score = _clamp(0.45 * base + 0.20 * idf_norm + (0.28 if qov else 0.0) + 0.25 * cv)
        else:  # element + codon_gate share the same per-token score
            score = _clamp(0.55 * base + 0.25 * idf_norm + (0.30 if qov else 0.0))
        action = _action(el, score, threshold, qov, cv, mode)
        rows.append({
            "sample_id": sample.sample_id, "token": token, "static_class": el,
            "idf": idf, "route_action": action, "later_needed": i in needed_indices,
        })
    return rows


def _action(el: str, score: float, threshold: float, qov: bool, cv: float, mode: str) -> str:
    below = score < threshold
    if mode == "element":
        if el in ELEMENT_ALWAYS or el in ELEMENT_CLEARABLE:
            return "keep"
        if el in WEAK_ELEMENTS:
            return "keep" if qov else ("cheap" if below else "keep")
        return "cheap" if below else "keep"
    # codon_gate / codon_boost: context-gate the protected classes
    if el in HARD_KEEP:
        return "keep"
    if el in GATED_KEEP:
        if qov or cv >= CODON_LOADBEARING_FLOOR:
            return "keep"
        return "cheap" if below else "keep"
    if el in WEAK_ELEMENTS:
        return "keep" if qov else ("cheap" if below else "keep")
    return "cheap" if below else "keep"


def _frontier_for_mode(samples, idf_map, mode: str, seed: int):
    curve, rows_by_threshold = [], {}
    for cand in THRESHOLDS:
        rows = [r for s in samples for r in _score_sample(s, idf_map, cand, mode)]
        rows_by_threshold[cand] = rows
        curve.append({"threshold": cand, **_metrics(rows)})
    return _frontier_by_tier(curve, rows_by_threshold, seed=seed), rows_by_threshold


def run_comparison(root: str = ".", seed: int = 7) -> dict:
    samples, source = load_dataset(root)
    corpus_docs, _idf_src = discover_corpus_docs(root)
    idf_map = build_idf(corpus_docs + [s.context for s in samples])

    baseline = run_benchmark(root=root, seed=seed)
    out = {"dataset": source, "n": len(samples),
           "needed_coverage": needed_span_coverage(samples)["coverage"],
           "modes": {"token": {k: baseline["frontier"][k] for k in ("lt_0_01", "lt_0_02", "lt_0_05")}}}
    for mode in MODES:
        frontier, rows_by_threshold = _frontier_for_mode(samples, idf_map, mode, seed)
        out["modes"][mode] = {k: frontier[k] for k in ("lt_0_01", "lt_0_02", "lt_0_05")}
        if mode == "element":
            out["_element_rows_at_best01"] = rows_by_threshold[frontier["lt_0_01"]["threshold"]]
    out["_baseline_rows"] = baseline["trace_rows"]
    return out


__all__ = ["run_comparison", "classify_element", "MODES"]
