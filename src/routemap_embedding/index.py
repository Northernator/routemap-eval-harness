"""EmbeddingRouteIndex: fingerprint candidates plus full cosine rerank."""

from __future__ import annotations

from typing import Any

import numpy as np


class EmbeddingRouteIndex:
    def __init__(self, matrix: np.ndarray, ids: list[str], fingerprint: Any):
        if len(matrix) != len(ids):
            raise ValueError("matrix and ids length mismatch")
        self.matrix = matrix.astype(np.float32, copy=False)
        self.ids = list(ids)
        self.fingerprint = fingerprint
        if hasattr(self.fingerprint, "build"):
            self.fingerprint.build(self.matrix, self.ids)
        elif hasattr(self.fingerprint, "fit"):
            self.fingerprint.fit(self.matrix, self.ids)
        else:
            raise TypeError("fingerprint must expose build() or fit()")

    def full_search(self, query: np.ndarray, k: int = 10) -> list[str]:
        indices = self._topk_indices(query, k, np.arange(len(self.ids)))
        return [self.ids[index] for index in indices]

    def route_search(self, query: np.ndarray, k: int = 10, shortlist_mult: int = 8) -> list[str]:
        limit = min(len(self.ids), max(k, k * shortlist_mult))
        candidates = set(self.fingerprint.candidates(query, limit=limit))
        if not candidates:
            return []
        if len(candidates) > limit:
            candidate_array = np.asarray(sorted(candidates), dtype=np.int64)
            scores = self.matrix[candidate_array] @ query.astype(np.float32, copy=False)
            keep = np.argpartition(-scores, limit - 1)[:limit]
            candidate_array = candidate_array[keep]
        else:
            candidate_array = np.asarray(sorted(candidates), dtype=np.int64)
        indices = self._topk_indices(query, k, candidate_array)
        return [self.ids[index] for index in indices]

    def candidate_count(self, query: np.ndarray, shortlist_mult: int = 8, k: int = 10) -> int:
        limit = min(len(self.ids), max(k, k * shortlist_mult))
        return len(self.fingerprint.candidates(query, limit=limit))

    def fingerprint_nbytes(self) -> int:
        if hasattr(self.fingerprint, "codes_nbytes"):
            return int(self.fingerprint.codes_nbytes())
        total = 0
        planes = getattr(self.fingerprint, "planes", None)
        if planes is not None:
            total += int(planes.nbytes)
        buckets = getattr(self.fingerprint, "buckets", {})
        total += sum(len(values) for values in buckets.values()) * 4
        return total

    def _topk_indices(self, query: np.ndarray, k: int, candidates: np.ndarray) -> list[int]:
        if len(candidates) == 0:
            return []
        k = min(k, len(candidates))
        scores = self.matrix[candidates] @ query.astype(np.float32, copy=False)
        top = np.argpartition(-scores, k - 1)[:k]
        ordered = top[np.argsort(-scores[top], kind="mergesort")]
        return [int(candidates[index]) for index in ordered]


__all__ = ["EmbeddingRouteIndex"]
