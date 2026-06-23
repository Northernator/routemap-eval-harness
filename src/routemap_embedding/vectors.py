"""Vector builders for embedding fingerprint retrieval."""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np


TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z]+)?")


def discover_corpus(root: str | Path = ".") -> list[dict[str, str]]:
    base = Path(root)
    docs: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in (
        base / "data" / "v1" / "gold" / "v1_full_extraction_gold_v1.csv",
        base / "data" / "gold" / "gold_segments_filled.csv",
    ):
        for row in _read_csv(path):
            segment_id = row.get("segment_id", "").strip()
            text = row.get("text", "").strip()
            if segment_id and text and segment_id not in seen:
                docs.append({"id": segment_id, "text": text, "source": str(path)})
                seen.add(segment_id)
    documents = base / "data" / "v1" / "documents"
    if documents.exists():
        for path in sorted(documents.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
            doc_id = f"doc::{path.name}"
            if text and doc_id not in seen:
                docs.append({"id": doc_id, "text": text, "source": str(path)})
                seen.add(doc_id)
    return docs


def build_vectors(
    docs: list[str] | list[dict[str, Any]] | list[tuple[str, str]],
    *,
    backend: str = "tfidf",
) -> tuple[np.ndarray, list[str], str]:
    ids, texts = _coerce_docs(docs)
    requested = backend
    if backend == "minilm":
        matrix = _try_minilm(texts)
        if matrix is not None:
            return _l2_normalize(matrix.astype(np.float32, copy=False)), ids, "minilm"
        backend = "tfidf"
    if backend != "tfidf":
        raise ValueError(f"unsupported backend: {requested}")
    return _tfidf_vectors(texts), ids, "tfidf"


def vectorize_queries(queries: list[str], corpus_docs: list[str]) -> np.ndarray:
    combined = list(corpus_docs) + list(queries)
    matrix = _tfidf_vectors(combined)
    return matrix[len(corpus_docs):]


def _coerce_docs(docs: list[str] | list[dict[str, Any]] | list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    ids: list[str] = []
    texts: list[str] = []
    for index, item in enumerate(docs):
        if isinstance(item, dict):
            doc_id = str(item.get("id") or item.get("segment_id") or index)
            text = str(item.get("text") or "")
        elif isinstance(item, tuple):
            doc_id = str(item[0])
            text = str(item[1])
        else:
            doc_id = str(index)
            text = str(item)
        ids.append(doc_id)
        texts.append(text)
    return ids, texts


def _tfidf_vectors(texts: list[str]) -> np.ndarray:
    tokenized = [_tokens(text) for text in texts]
    vocab = sorted({token for doc in tokenized for token in doc})
    if not vocab:
        return np.zeros((len(texts), 1), dtype=np.float32)
    vocab_index = {token: index for index, token in enumerate(vocab)}
    doc_count = len(texts)
    df: Counter[str] = Counter()
    for doc in tokenized:
        df.update(set(doc))
    idf = np.array([math.log((1 + doc_count) / (1 + df[token])) + 1.0 for token in vocab], dtype=np.float32)
    matrix = np.zeros((len(texts), len(vocab)), dtype=np.float32)
    for row_index, doc in enumerate(tokenized):
        counts = Counter(doc)
        total = float(sum(counts.values()) or 1)
        for token, count in counts.items():
            matrix[row_index, vocab_index[token]] = (count / total) * idf[vocab_index[token]]
    return _l2_normalize(matrix)


def _tokens(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def _l2_normalize(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    return (matrix / norms).astype(np.float32, copy=False)


def _try_minilm(texts: list[str]) -> np.ndarray | None:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return None
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return np.asarray(model.encode(texts, normalize_embeddings=True), dtype=np.float32)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


__all__ = ["build_vectors", "discover_corpus", "vectorize_queries"]
