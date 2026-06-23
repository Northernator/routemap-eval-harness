"""Tests for the experimental routemap_elements lane (run with PYTHONPATH=src)."""

from __future__ import annotations

import random
from pathlib import Path

from routemap_elements.bench_elements import MODES, _score_sample, run_comparison
from routemap_elements.elements import best_codon_value, classify_element, codon_value
from routemap_token.bench import load_dataset
from routemap_token.prior import build_idf, discover_corpus_docs

ROOT = str(Path(__file__).resolve().parent)
KNOWN_ELEMENTS = {
    "NEGATION", "MODAL", "CONDITION", "EXCEPTION", "REQUIRE", "DEFINE", "CAUSE", "SUPPORT",
    "CONTRADICT", "MAPSTO", "NUMBER", "DATE", "THRESHOLD", "UNIT", "CITATION", "SOURCE",
    "EXAMPLE", "QUOTE", "ENTITY", "SYSTEM", "CONCEPT", "ACTION", "RISK", "LIMITATION",
    "PROBABILITY", "INSTRUCT", "CODE", "FORMULA", "SEQUENCE", "CONNECTOR", "FUNCTION",
    "BOUNDARY", "UNKNOWN",
}


def test_classify_element_known_and_deterministic() -> None:
    for tok in ["not", "must", "System", "2027", "[3]", "the", ".", "approve", "risk", "F(118)", "blarghx"]:
        el = classify_element(tok)
        assert el in KNOWN_ELEMENTS
        assert classify_element(tok) == el  # deterministic


def test_codon_value_bounded() -> None:
    assert 0.0 <= codon_value(("NEGATION", "MODAL", "ACTION")) <= 1.0
    # an operator bound to contentful tokens scores higher than pure filler
    assert codon_value(("NEGATION", "ACTION", "ENTITY")) > codon_value(("FUNCTION", "FUNCTION", "BOUNDARY"))


def test_no_leak_routes_independent_of_gold_answer() -> None:
    samples, _ = load_dataset(ROOT)
    docs, _ = discover_corpus_docs(ROOT)
    idf = build_idf(docs + [s.context for s in samples])
    rng = random.Random(7)
    for s in samples[:30]:
        for mode in MODES:
            a = [r["route_action"] for r in _score_sample(s, idf, 0.5, mode)]
            scrambled = s.__class__(sample_id=s.sample_id, context=s.context, question=s.question,
                                    answer="ZZZ " + str(rng.random()), evidence="qq", needed_phrases=("zzz", "qq"))
            b = [r["route_action"] for r in _score_sample(scrambled, idf, 0.5, mode)]
            assert a == b, f"route changed when gold answer scrambled (mode={mode})"


def test_determinism() -> None:
    r1 = run_comparison(root=ROOT, seed=7)
    r2 = run_comparison(root=ROOT, seed=7)
    for m in ("token", *MODES):
        for t in ("lt_0_01", "lt_0_02", "lt_0_05"):
            assert r1["modes"][m][t] == r2["modes"][m][t]


def test_element_beats_token_baseline_on_real_gold() -> None:
    res = run_comparison(root=ROOT, seed=7)
    if res["dataset"] != "v1_full_extraction_gold":
        return  # gold not present in this environment; skip the headline assertion
    tok = res["modes"]["token"]["lt_0_01"]
    el = res["modes"]["element"]["lt_0_01"]
    assert el["recall_loss"] < 0.02  # recall preserved
    assert el["token_reduction"] > tok["token_reduction"] + 0.03  # meaningfully more reduction
    # codon adds nothing on top of element
    cg = res["modes"]["codon_gate"]["lt_0_01"]["token_reduction"]
    assert cg <= el["token_reduction"] + 1e-9
