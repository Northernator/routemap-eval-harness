"""Benchmark for approximate embedding fingerprint retrieval."""

from __future__ import annotations

import csv
import json
import statistics
import time
from pathlib import Path
from typing import Any

import numpy as np

from .fingerprints import ProductQuantizer, RandomProjectionLSH, SimHash
from .index import EmbeddingRouteIndex
from .vectors import build_vectors, discover_corpus, vectorize_queries


def run_benchmark(
    *,
    root: str | Path = ".",
    backend: str = "tfidf",
    synthetic_n: int = 20000,
    k: int = 10,
    seed: int = 7,
) -> dict[str, Any]:
    root_path = Path(root)
    docs = discover_corpus(root_path)
    matrix, ids, backend_used = build_vectors(docs, backend=backend)
    texts = [doc["text"] for doc in docs]
    qa_rows = _load_qa(root_path)
    queries = [row["query"] for row in qa_rows]
    query_matrix = vectorize_queries(queries, texts) if queries else np.zeros((0, matrix.shape[1]), dtype=np.float32)
    # Rebuild corpus vectors in the same TF-IDF space as queries for fair lexical evaluation.
    if queries and backend_used == "tfidf":
        combined = build_vectors([{"id": doc_id, "text": text} for doc_id, text in zip(ids, texts)] + [{"id": f"q::{i}", "text": q} for i, q in enumerate(queries)], backend="tfidf")[0]
        matrix = combined[:len(ids)]
        query_matrix = combined[len(ids):]

    real_gold = _real_gold_eval(matrix, ids, qa_rows, query_matrix, k=k, seed=seed)
    synthetic = _synthetic_eval(matrix, ids, k=k, n=synthetic_n, seed=seed)
    bars = _bars(synthetic["chosen"])
    return {
        "backend_used": backend_used,
        "corpus_size": len(ids),
        "dimension": int(matrix.shape[1]),
        "real_gold": real_gold,
        "synthetic": synthetic,
        "minimum_bar": "PASS" if bars["minimum"] else "FAIL",
        "strong_bar": "PASS" if bars["strong"] else "FAIL",
    }


def report(result: dict[str, Any]) -> str:
    lines = [
        "# EmbeddingRouteIndex Benchmark",
        "",
        f"Backend used: `{result['backend_used']}`",
        f"Corpus: {result['corpus_size']} vectors x {result['dimension']} dims",
        "",
        "## Real-Gold Recall",
        "",
        f"n_queries: {result['real_gold']['n_queries']}",
        "",
        "| Fingerprint | full_recall@10 | route_recall@10 | recall_loss |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in result["real_gold"]["rows"]:
        lines.append(f"| {row['fingerprint']} | {row['full_recall_at_10']:.3f} | {row['route_recall_at_10']:.3f} | {row['recall_loss']:.3f} |")
    lines.extend([
        "",
        "## Synthetic Recall vs Latency",
        "",
        f"N: {result['synthetic']['n_vectors']}",
        f"vector_bytes: {result['synthetic']['vector_bytes']}",
        "",
        "| Fingerprint | shortlist_mult | recall@10 | false_negative_rate | full_ms | route_ms | speedup | fingerprint_bytes |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    for row in result["synthetic"]["curve"]:
        lines.append(
            f"| {row['fingerprint']} | {row['shortlist_mult']} | {row['recall_at_10']:.3f} | {row['false_negative_rate']:.3f} | "
            f"{row['latency_full_ms']:.3f} | {row['latency_route_ms']:.3f} | {row['speedup']:.2f} | {row['fingerprint_bytes']} |"
        )
    lines.extend([
        "",
        "## Chosen Operating Points",
        "",
        "| Fingerprint | shortlist_mult | recall@10 | speedup | minimum_candidate | strong_candidate |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ])
    for name in ("SimHash", "LSH", "PQ"):
        row = result["synthetic"]["chosen"][name]
        minimum = row["recall_at_10"] > 0.95 and row["speedup"] >= 2.0
        strong = row["recall_at_10"] > 0.98 and row["speedup"] >= 5.0
        lines.append(
            f"| {name} | {row['shortlist_mult']} | {row['recall_at_10']:.3f} | {row['speedup']:.2f} | "
            f"{'yes' if minimum else 'no'} | {'yes' if strong else 'no'} |"
        )
    lines.extend([
        "",
        "## Bars",
        "",
        "| Bar | Result |",
        "| --- | --- |",
        f"| minimum_bar | {result['minimum_bar']} |",
        f"| strong_bar | {result['strong_bar']} |",
    ])
    return "\n".join(lines)


def _fingerprints(seed: int, dim: int) -> list[tuple[str, Any]]:
    n_subvectors = 4
    while dim % n_subvectors != 0 and n_subvectors > 1:
        n_subvectors -= 1
    return [
        ("SimHash", SimHash(n_bits=12, seed=seed)),
        ("LSH", RandomProjectionLSH(n_planes=24, n_bands=8, seed=seed)),
        ("PQ", ProductQuantizer(n_subvectors=n_subvectors, n_codes=16, seed=seed)),
    ]


def _real_gold_eval(
    matrix: np.ndarray,
    ids: list[str],
    qa_rows: list[dict[str, str]],
    query_matrix: np.ndarray,
    *,
    k: int,
    seed: int,
) -> dict[str, Any]:
    rows: list[dict[str, float | str]] = []
    if len(qa_rows) == 0:
        return {"n_queries": 0, "rows": rows}
    full_index = EmbeddingRouteIndex(matrix, ids, RandomProjectionLSH(seed=seed))
    full_hits = _gold_hits(full_index, qa_rows, query_matrix, k, route=False)
    for name, fp in _fingerprints(seed, matrix.shape[1]):
        index = EmbeddingRouteIndex(matrix, ids, fp)
        route_hits = _gold_hits(index, qa_rows, query_matrix, k, route=True)
        full_recall = full_hits / len(qa_rows)
        route_recall = route_hits / len(qa_rows)
        rows.append(
            {
                "fingerprint": name,
                "full_recall_at_10": full_recall,
                "route_recall_at_10": route_recall,
                "recall_loss": full_recall - route_recall,
            }
        )
    return {"n_queries": len(qa_rows), "rows": rows}


def _synthetic_eval(matrix: np.ndarray, ids: list[str], *, k: int, n: int, seed: int) -> dict[str, Any]:
    synthetic_matrix, synthetic_ids, query_indices = _make_synthetic(matrix, ids, n=n, seed=seed)
    query_vectors = synthetic_matrix[query_indices]
    curve: list[dict[str, Any]] = []
    for name, fp in _fingerprints(seed, synthetic_matrix.shape[1]):
        index = EmbeddingRouteIndex(synthetic_matrix, synthetic_ids, fp)
        full_refs = [index.full_search(query, k=k) for query in query_vectors]
        full_ms = _median_latency(lambda q: index.full_search(q, k=k), query_vectors)
        for shortlist_mult in (2, 4, 8, 16, 32):
            route_results = [index.route_search(query, k=k, shortlist_mult=shortlist_mult) for query in query_vectors]
            route_ms = _median_latency(lambda q: index.route_search(q, k=k, shortlist_mult=shortlist_mult), query_vectors)
            recall = _mean_recall(full_refs, route_results, k)
            curve.append(
                {
                    "fingerprint": name,
                    "shortlist_mult": shortlist_mult,
                    "recall_at_10": recall,
                    "false_negative_rate": 1.0 - recall,
                    "latency_full_ms": full_ms,
                    "latency_route_ms": route_ms,
                    "speedup": full_ms / route_ms if route_ms > 0 else float("inf"),
                    "fingerprint_bytes": index.fingerprint_nbytes(),
                }
            )
    chosen = _choose_operating_points(curve)
    return {
        "n_vectors": len(synthetic_ids),
        "n_queries": len(query_vectors),
        "vector_bytes": int(synthetic_matrix.nbytes),
        "curve": curve,
        "chosen": chosen,
    }


def _make_synthetic(matrix: np.ndarray, ids: list[str], *, n: int, seed: int) -> tuple[np.ndarray, list[str], list[int]]:
    generator = np.random.default_rng(seed)
    dim = matrix.shape[1]
    base = matrix.astype(np.float32, copy=False)
    rows = [base]
    out_ids = list(ids)
    query_indices: list[int] = []
    planted = min(48, len(base))
    for index in range(planted):
        noise = generator.normal(scale=0.015, size=dim).astype(np.float32)
        vec = base[index] + noise
        vec /= max(float(np.linalg.norm(vec)), 1e-9)
        query_indices.append(len(out_ids))
        rows.append(vec[None, :])
        out_ids.append(f"planted::{ids[index]}")
    remaining = max(0, n - len(out_ids))
    if remaining:
        random_vectors = generator.normal(size=(remaining, dim)).astype(np.float32)
        random_vectors /= np.maximum(np.linalg.norm(random_vectors, axis=1, keepdims=True), 1e-9)
        rows.append(random_vectors)
        out_ids.extend(f"distractor::{i}" for i in range(remaining))
    synthetic = np.vstack(rows).astype(np.float32, copy=False)
    return synthetic, out_ids, query_indices


def _load_qa(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in (root / "data" / "gold" / "gold_qa_filled.csv", root / "data" / "v1" / "gold" / "v1_qa_targets.csv"):
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                query = row.get("query", "").strip()
                gold = row.get("gold_required_segment_ids", "").strip()
                if query and gold:
                    rows.append({"query": query, "gold": gold})
        if rows:
            break
    return rows


def _gold_hits(index: EmbeddingRouteIndex, qa_rows: list[dict[str, str]], query_matrix: np.ndarray, k: int, *, route: bool) -> int:
    hits = 0
    for row, query in zip(qa_rows, query_matrix):
        gold = {part.strip() for part in row["gold"].replace(";", "|").split("|") if part.strip()}
        found = set(index.route_search(query, k=k, shortlist_mult=16) if route else index.full_search(query, k=k))
        if gold & found:
            hits += 1
    return hits


def _median_latency(fn: Any, queries: np.ndarray) -> float:
    timings: list[float] = []
    for query in queries:
        start = time.perf_counter()
        fn(query)
        timings.append((time.perf_counter() - start) * 1000.0)
    return float(statistics.median(timings)) if timings else 0.0


def _mean_recall(reference: list[list[str]], routed: list[list[str]], k: int) -> float:
    if not reference:
        return 0.0
    scores = []
    for left, right in zip(reference, routed):
        scores.append(len(set(left[:k]) & set(right[:k])) / k)
    return float(sum(scores) / len(scores))


def _choose_operating_points(curve: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    chosen: dict[str, dict[str, Any]] = {}
    for row in curve:
        name = row["fingerprint"]
        current = chosen.get(name)
        if current is None or (row["recall_at_10"], row["speedup"]) > (current["recall_at_10"], current["speedup"]):
            chosen[name] = row
    return chosen


def _bars(chosen: dict[str, dict[str, Any]]) -> dict[str, bool]:
    return {
        "minimum": any(row["recall_at_10"] > 0.95 and row["speedup"] >= 2.0 for row in chosen.values()),
        "strong": any(row["recall_at_10"] > 0.98 and row["speedup"] >= 5.0 for row in chosen.values()),
    }


def write_outputs(result: dict[str, Any], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "embedding_route_report.md").write_text(report(result), encoding="utf-8")
    (out / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


__all__ = ["report", "run_benchmark", "write_outputs"]
