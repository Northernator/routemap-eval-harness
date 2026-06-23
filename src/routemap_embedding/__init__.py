"""Approximate embedding fingerprint retrieval for RouteMap."""

from __future__ import annotations

from .bench import run_benchmark, report
from .fingerprints import ProductQuantizer, RandomProjectionLSH, SimHash
from .index import EmbeddingRouteIndex
from .vectors import build_vectors, discover_corpus

__all__ = [
    "EmbeddingRouteIndex",
    "ProductQuantizer",
    "RandomProjectionLSH",
    "SimHash",
    "build_vectors",
    "discover_corpus",
    "report",
    "run_benchmark",
]
