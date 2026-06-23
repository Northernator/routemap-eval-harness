from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from routemap_token.bench import TokenQASample, card, load_dataset, needed_token_indices, run_benchmark, score_sample, tokenize_with_spans
from routemap_token.policy import route_action
from routemap_token.prior import build_idf, classify_token, token_prior_score
from routemap_token.trace import REQUIRED_TRACE_FIELDS, emit_trace


def test_classify_token() -> None:
    assert classify_token("the") == "function_word"
    assert classify_token("and") == "function_word"
    assert classify_token("island") == "content_word"
    assert classify_token("artist") == "content_word"
    assert classify_token("not") == "negation"
    assert classify_token("never") == "negation"
    assert classify_token("[1]") == "citation"
    assert classify_token("http://x") == "citation"
    assert classify_token("def") == "code_token"
    assert classify_token("==") == "code_token"
    assert classify_token("118") == "number"
    assert classify_token("2027") == "number"
    assert classify_token("OpenAI") == "named_entity"
    assert classify_token("London") == "named_entity"


def test_load_bearing_negation_never_cheap() -> None:
    assert route_action("not", 0.01, threshold=0.95, features={}) == "keep"


def test_idf_monotonicity() -> None:
    idf = build_idf(["the common token", "the common route", "the rarex"])
    assert idf["rarex"] > idf["the"]


def test_no_leak_route_decisions_ignore_gold_labels() -> None:
    idf = build_idf(["The island artist did not sign the treaty."])
    sample = TokenQASample("a", "The island artist did not sign the treaty.", "Who did not sign?", "island artist", "did not sign", ("island artist", "did not sign"))
    perturbed = TokenQASample("a", sample.context, sample.question, "arbitrary answer", "arbitrary evidence", ("treaty", "made up gold"))
    rows_a = score_sample(sample, idf, 0.5)
    rows_b = score_sample(perturbed, idf, 0.5)
    decisions_a = [(row["token"], row["route_score"], row["route_action"]) for row in rows_a]
    decisions_b = [(row["token"], row["route_score"], row["route_action"]) for row in rows_b]
    assert decisions_a == decisions_b


def test_real_gold_loads() -> None:
    samples, source = load_dataset(ROOT)
    assert source == "v1_full_extraction_gold"
    assert len(samples) >= 50


def test_token_boundary_needed_labeling() -> None:
    sample = TokenQASample("boundary", "The note says not now.", "", "", "", ("not",))
    needed, located, total = needed_token_indices(sample)
    tokens = [token for token, _start, _end in tokenize_with_spans(sample.context)]
    assert located == 1
    assert total == 1
    assert tokens.index("not") in needed
    assert tokens.index("note") not in needed


def test_needed_span_coverage_lifts_with_normalized_partial_runs() -> None:
    sample = TokenQASample("partial", "Secure AI systems guide audits.", "", "", "", ("NCSC secure AI guidance", "audits"))
    needed, located, total = needed_token_indices(sample)
    tokens = [token for token, _start, _end in tokenize_with_spans(sample.context)]
    assert located == 2
    assert total == 2
    assert tokens.index("Secure") in needed
    assert tokens.index("AI") in needed
    assert tokens.index("audits") in needed
    result = run_benchmark(root=ROOT, seed=7)
    assert result["needed_span_coverage"] >= 0.404


def test_explicit_clear_is_inference_only_and_preserves_distinctive_tokens() -> None:
    idf = build_idf([
        "Beta 2027 filler",
        "Beta 2027 filler",
        "Beta 2027 filler",
        "ordinary filler",
    ])
    sample = TokenQASample("clear", "Beta filler Beta 2027 value 2027 RareX RareX.", "Which Beta value?", "", "", ("value",))
    rows = score_sample(sample, idf, 0.95)
    by_token = [(row["token"], row) for row in rows]
    beta_rows = [row for token, row in by_token if token == "Beta"]
    number_rows = [row for token, row in by_token if token == "2027"]
    rare_rows = [row for token, row in by_token if token == "RareX"]
    assert not beta_rows[0]["context_features"]["explicit_clear"]
    assert beta_rows[0]["route_action"] == "keep"
    assert not beta_rows[1]["context_features"]["explicit_clear"]
    assert beta_rows[1]["route_action"] == "keep"
    assert not number_rows[0]["context_features"]["explicit_clear"]
    assert number_rows[1]["context_features"]["explicit_clear"]
    assert number_rows[1]["route_action"] == "cheap"
    assert not rare_rows[0]["context_features"]["explicit_clear"]
    assert not rare_rows[1]["context_features"]["explicit_clear"]
    assert all(row["route_action"] == "keep" for row in rare_rows)


def test_recall_preservation_and_baseline_deltas() -> None:
    result = run_benchmark(root=ROOT, seed=7)
    assert result["dataset_source"] == "v1_full_extraction_gold"
    for key in ("lt_0_01", "lt_0_02", "lt_0_05"):
        assert key in result["frontier"]
        assert result["frontier"][key]["policy_vs_random_recall_delta"] > 0
        assert result["frontier"][key]["policy_vs_naive_stopword_recall_delta"] > 0
    assert result["minimum_bar"] in {"PASS", "FAIL"}
    assert result["strong_bar"] in {"PASS", "FAIL"}


def test_deterministic_trace(tmp_path: Path) -> None:
    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    result_a = run_benchmark(root=ROOT, trace_path=path_a, seed=11)
    result_b = run_benchmark(root=ROOT, trace_path=path_b, seed=11)
    assert path_a.read_bytes() == path_b.read_bytes()
    assert result_a["threshold_curve"] == result_b["threshold_curve"]
    first = json.loads(path_a.read_text(encoding="utf-8").splitlines()[0])
    assert REQUIRED_TRACE_FIELDS <= set(first)
    assert card(result_a) == card(result_b)
