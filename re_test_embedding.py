from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from routemap_embedding.bench import run_benchmark
from routemap_embedding.fingerprints import ProductQuantizer, RandomProjectionLSH, SimHash
from routemap_embedding.index import EmbeddingRouteIndex
from routemap_embedding.vectors import build_vectors


def _unit_random(n: int, d: int, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)
    matrix = rng.normal(size=(n, d)).astype(np.float32)
    matrix /= np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-9)
    return matrix


def _mean_recall(reference: list[list[str]], routed: list[list[str]], k: int) -> float:
    return sum(len(set(left[:k]) & set(right[:k])) / k for left, right in zip(reference, routed)) / len(reference)


def test_default_backend_is_tfidf_without_optional_deps() -> None:
    matrix, ids, backend = build_vectors(["alpha beta beta", "gamma delta"], backend="tfidf")
    assert backend == "tfidf"
    assert ids == ["0", "1"]
    assert matrix.dtype == np.float32
    assert np.allclose(np.linalg.norm(matrix, axis=1), 1.0)


def test_determinism_same_seed_same_fingerprints_codes_and_results() -> None:
    matrix = _unit_random(128, 32, seed=1)
    ids = [f"id{i}" for i in range(len(matrix))]
    query = matrix[0]
    left_lsh = RandomProjectionLSH(n_planes=24, n_bands=6, seed=9)
    right_lsh = RandomProjectionLSH(n_planes=24, n_bands=6, seed=9)
    left = EmbeddingRouteIndex(matrix, ids, left_lsh)
    right = EmbeddingRouteIndex(matrix, ids, right_lsh)
    assert left_lsh.encode(query) == right_lsh.encode(query)
    assert left.route_search(query, k=10, shortlist_mult=8) == right.route_search(query, k=10, shortlist_mult=8)
    left_pq = ProductQuantizer(n_subvectors=4, n_codes=8, seed=3).fit(matrix, ids)
    right_pq = ProductQuantizer(n_subvectors=4, n_codes=8, seed=3).fit(matrix, ids)
    assert np.array_equal(left_pq.codes, right_pq.codes)


def test_planted_neighbors_route_search_retrieves_near_duplicates() -> None:
    base = _unit_random(64, 48, seed=2)
    rng = np.random.default_rng(22)
    planted = base[:20] + rng.normal(scale=0.003, size=(20, 48)).astype(np.float32)
    planted /= np.maximum(np.linalg.norm(planted, axis=1, keepdims=True), 1e-9)
    matrix = np.vstack([base, planted]).astype(np.float32)
    ids = [f"base{i}" for i in range(len(base))] + [f"planted{i}" for i in range(len(planted))]
    index = EmbeddingRouteIndex(matrix, ids, RandomProjectionLSH(n_planes=32, n_bands=8, seed=4))
    hits = 0
    for i in range(20):
        routed = index.route_search(base[i], k=10, shortlist_mult=16)
        if f"planted{i}" in routed:
            hits += 1
    assert hits / 20 >= 0.85


def test_recall_vs_full_and_false_negative_complement() -> None:
    result = run_benchmark(root=ROOT, synthetic_n=1500, seed=5)
    rows = [row for row in result["synthetic"]["curve"] if row["fingerprint"] == "PQ"]
    recalls = [row["recall_at_10"] for row in rows]
    assert rows
    for row in rows:
        assert 0.0 <= row["recall_at_10"] <= 1.0
        assert abs(row["false_negative_rate"] - (1.0 - row["recall_at_10"])) < 1e-9
    assert recalls[-1] >= recalls[0]


def test_route_search_shortlists_candidates_at_scale() -> None:
    matrix = _unit_random(8000, 128, seed=6)
    ids = [f"id{i}" for i in range(len(matrix))]
    index = EmbeddingRouteIndex(matrix, ids, ProductQuantizer(n_subvectors=8, n_codes=16, seed=6))
    queries = matrix[:24]
    for query in queries:
        assert len(index.route_search(query, k=10, shortlist_mult=8)) == 10
        assert index.candidate_count(query, k=10, shortlist_mult=8) == 80
    assert 80 < len(matrix)


def test_distinct_vectors_can_collide_in_a_bucket() -> None:
    matrix = _unit_random(8, 16, seed=8)
    simhash = SimHash(n_bits=1, seed=8).fit(matrix)
    buckets: dict[int, list[int]] = {}
    for index, vec in enumerate(matrix):
        buckets.setdefault(simhash.bucket(simhash.encode(vec)), []).append(index)
    collision = next(values for values in buckets.values() if len(values) >= 2)
    assert collision[0] != collision[1]
    assert not np.allclose(matrix[collision[0]], matrix[collision[1]])


def test_benchmark_reports_honest_bars_and_real_gold() -> None:
    result = run_benchmark(root=ROOT, synthetic_n=1200, seed=7)
    assert result["backend_used"] == "tfidf"
    assert result["real_gold"]["n_queries"] > 0
    assert result["minimum_bar"] in {"PASS", "FAIL"}
    assert result["strong_bar"] in {"PASS", "FAIL"}
    assert {"SimHash", "LSH", "PQ"} == {row["fingerprint"] for row in result["real_gold"]["rows"]}
