"""Similarity-preserving fingerprints for approximate routing."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


@dataclass
class SimHash:
    n_bits: int = 16
    seed: int = 7
    planes: np.ndarray | None = None
    buckets: dict[int, list[int]] = field(default_factory=dict)
    ids: list[str] = field(default_factory=list)

    def fit(self, matrix: np.ndarray, ids: list[str] | None = None) -> "SimHash":
        generator = _rng(self.seed)
        self.planes = generator.normal(size=(matrix.shape[1], self.n_bits)).astype(np.float32)
        if ids is not None:
            self.build(matrix, ids)
        return self

    def build(self, matrix: np.ndarray, ids: list[str]) -> None:
        if self.planes is None:
            self.fit(matrix)
        self.ids = list(ids)
        buckets: dict[int, list[int]] = defaultdict(list)
        for index, vec in enumerate(matrix):
            buckets[self.encode(vec)].append(index)
        self.buckets = dict(buckets)

    def encode(self, vec: np.ndarray) -> int:
        if self.planes is None:
            raise ValueError("SimHash must be fit before encode")
        bits = np.dot(vec.astype(np.float32, copy=False), self.planes) >= 0
        signature = 0
        for bit_index, bit in enumerate(bits):
            if bool(bit):
                signature |= 1 << bit_index
        return signature

    def bucket(self, sig: int) -> int:
        return int(sig)

    def candidates(self, query: np.ndarray, limit: int | None = None) -> set[int]:
        sig = self.encode(query)
        result = set(self.buckets.get(self.bucket(sig), []))
        if result or limit is None:
            return result
        return set()


@dataclass
class RandomProjectionLSH:
    n_planes: int = 24
    n_bands: int = 6
    seed: int = 7
    planes: np.ndarray | None = None
    buckets: dict[tuple[int, int], list[int]] = field(default_factory=dict)
    ids: list[str] = field(default_factory=list)

    def fit(self, matrix: np.ndarray, ids: list[str] | None = None) -> "RandomProjectionLSH":
        if self.n_planes % self.n_bands != 0:
            raise ValueError("n_planes must be divisible by n_bands")
        generator = _rng(self.seed)
        self.planes = generator.normal(size=(matrix.shape[1], self.n_planes)).astype(np.float32)
        if ids is not None:
            self.build(matrix, ids)
        return self

    def build(self, matrix: np.ndarray, ids: list[str]) -> None:
        if self.planes is None:
            self.fit(matrix)
        self.ids = list(ids)
        buckets: dict[tuple[int, int], list[int]] = defaultdict(list)
        for index, vec in enumerate(matrix):
            for bucket in self.bucket(self.encode(vec)):
                buckets[bucket].append(index)
        self.buckets = dict(buckets)

    def encode(self, vec: np.ndarray) -> tuple[int, ...]:
        if self.planes is None:
            raise ValueError("RandomProjectionLSH must be fit before encode")
        return tuple(int(value) for value in (np.dot(vec.astype(np.float32, copy=False), self.planes) >= 0))

    def bucket(self, sig: tuple[int, ...]) -> tuple[tuple[int, int], ...]:
        rows_per_band = self.n_planes // self.n_bands
        buckets: list[tuple[int, int]] = []
        for band in range(self.n_bands):
            value = 0
            start = band * rows_per_band
            for offset, bit in enumerate(sig[start:start + rows_per_band]):
                if bit:
                    value |= 1 << offset
            buckets.append((band, value))
        return tuple(buckets)

    def candidates(self, query: np.ndarray, limit: int | None = None) -> set[int]:
        result: set[int] = set()
        for bucket in self.bucket(self.encode(query)):
            result.update(self.buckets.get(bucket, []))
        return result


@dataclass
class ProductQuantizer:
    n_subvectors: int = 4
    n_codes: int = 16
    seed: int = 7
    n_iter: int = 8
    codebooks: list[np.ndarray] = field(default_factory=list)
    codes: np.ndarray | None = None
    ids: list[str] = field(default_factory=list)

    def fit(self, matrix: np.ndarray, ids: list[str] | None = None) -> "ProductQuantizer":
        if matrix.shape[1] % self.n_subvectors != 0:
            raise ValueError("matrix width must be divisible by n_subvectors")
        generator = _rng(self.seed)
        self.codebooks = []
        self.ids = list(ids or [])
        width = matrix.shape[1] // self.n_subvectors
        for sub in range(self.n_subvectors):
            block = matrix[:, sub * width:(sub + 1) * width].astype(np.float32, copy=False)
            k = min(self.n_codes, len(block))
            seeds = generator.choice(len(block), size=k, replace=False)
            centers = block[seeds].copy()
            for _ in range(self.n_iter):
                distances = ((block[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
                labels = distances.argmin(axis=1)
                for code in range(k):
                    members = block[labels == code]
                    if len(members):
                        centers[code] = members.mean(axis=0)
            if k < self.n_codes:
                pad = np.zeros((self.n_codes - k, width), dtype=np.float32)
                centers = np.vstack([centers, pad])
            self.codebooks.append(centers.astype(np.float32, copy=False))
        self.codes = np.asarray([self.encode(vec) for vec in matrix], dtype=np.int16)
        return self

    def build(self, matrix: np.ndarray, ids: list[str]) -> None:
        self.fit(matrix, ids)

    def encode(self, vec: np.ndarray) -> tuple[int, ...]:
        if not self.codebooks:
            raise ValueError("ProductQuantizer must be fit before encode")
        width = len(vec) // self.n_subvectors
        result: list[int] = []
        for sub, centers in enumerate(self.codebooks):
            block = vec[sub * width:(sub + 1) * width].astype(np.float32, copy=False)
            distances = ((centers - block[None, :]) ** 2).sum(axis=1)
            result.append(int(distances.argmin()))
        return tuple(result)

    def approximate_distances(self, query: np.ndarray) -> np.ndarray:
        if self.codes is None:
            raise ValueError("ProductQuantizer must be fit before approximate_distances")
        q_code = self.encode(query)
        width = len(query) // self.n_subvectors
        tables: list[np.ndarray] = []
        for sub, centers in enumerate(self.codebooks):
            block = query[sub * width:(sub + 1) * width].astype(np.float32, copy=False)
            tables.append(((centers - block[None, :]) ** 2).sum(axis=1))
        distances = np.zeros(len(self.codes), dtype=np.float32)
        for sub, table in enumerate(tables):
            distances += table[self.codes[:, sub]]
        exact_matches = np.all(self.codes == np.asarray(q_code, dtype=np.int16), axis=1)
        distances[exact_matches] *= 0.5
        return distances

    def candidates(self, query: np.ndarray, limit: int | None = None) -> set[int]:
        distances = self.approximate_distances(query)
        n = len(distances) if limit is None else min(int(limit), len(distances))
        if n <= 0:
            return set()
        indices = np.argpartition(distances, n - 1)[:n]
        return set(int(index) for index in indices)

    def codes_nbytes(self) -> int:
        total = 0
        for book in self.codebooks:
            total += int(book.nbytes)
        if self.codes is not None:
            total += int(self.codes.nbytes)
        return total


def hamming_distance(left: int | Iterable[int], right: int | Iterable[int]) -> int:
    if isinstance(left, int) and isinstance(right, int):
        return int((left ^ right).bit_count())
    return sum(1 for a, b in zip(left, right) if a != b)


__all__ = ["ProductQuantizer", "RandomProjectionLSH", "SimHash", "hamming_distance"]
