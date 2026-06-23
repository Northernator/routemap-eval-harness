"""Static token class and IDF prior for token routing."""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path


FUNCTION_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "them",
    "to",
    "was",
    "were",
    "with",
}
NEGATION_MODAL = {"not", "never", "no", "without", "unless", "cannot", "n't", "may", "might", "must", "should", "can"}
CODE_TOKENS = {"def", "import", "return", "class", "==", "!=", "{", "}", ";", "=>", "->", "(", ")"}
INSTRUCTION_LEADS = {"return", "write", "compute", "summarize", "choose", "list", "explain", "show", "compare"}
CLASS_WEIGHTS = {
    "function_word": 0.12,
    "content_word": 0.62,
    "named_entity": 0.82,
    "number": 0.78,
    "formula": 0.82,
    "code_token": 0.88,
    "negation": 0.95,
    "citation": 0.72,
    "instruction": 0.70,
    "punctuation": 0.05,
    "unknown": 0.45,
}
FALLBACK_DOCS = [
    "the and of to a in route answer token not island artist London OpenAI evidence citation",
    "the token route keeps not never numbers 118 2027 formula code def return context question",
    "artist island bridge content word answer span evidence span cheap keep reduction recall",
]


def classify_token(token: str) -> str:
    value = str(token)
    lower = value.lower()
    if lower in CODE_TOKENS or value in CODE_TOKENS:
        return "code_token"
    if re.fullmatch(r"\W+", value):
        return "punctuation"
    if lower in NEGATION_MODAL:
        return "negation"
    if re.fullmatch(r"\[\d+\]|https?://\S+|\"|'", value):
        return "citation"
    if re.fullmatch(r"[+-]?\d+(?:\.\d+)?", value):
        return "number"
    if re.search(r"[\^=/*_<>]|[A-Za-z]+\(\d*\)", value):
        return "formula"
    if lower in INSTRUCTION_LEADS:
        return "instruction"
    if value[:1].isupper() and re.search(r"[A-Za-z]", value):
        return "named_entity"
    if lower in FUNCTION_WORDS:
        return "function_word"
    if re.search(r"[A-Za-z]", value):
        return "content_word"
    return "unknown"


def build_idf(corpus_docs: list[str]) -> dict[str, float]:
    docs = corpus_docs or FALLBACK_DOCS
    doc_count = len(docs)
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(_tokens(doc)))
    return {
        token: math.log((1 + doc_count) / (1 + count)) + 1.0
        for token, count in sorted(df.items())
    }


def discover_corpus_docs(root: str | Path = ".") -> tuple[list[str], str]:
    base = Path(root)
    candidates = [
        base / "data" / "documents",
        base / "data" / "v1" / "documents",
        base / "data" / "v1" / "corpus",
    ]
    docs: list[str] = []
    for directory in candidates:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*"))[:80]:
            if path.suffix.lower() not in {".txt", ".md", ".csv", ".jsonl"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if text.strip():
                docs.append(text[:20000])
        if docs:
            return docs, str(directory)
    return list(FALLBACK_DOCS), "fallback_frequency_list"


def token_prior_score(token: str, idf_map: dict[str, float]) -> float:
    static = CLASS_WEIGHTS[classify_token(token)]
    idf = idf_map.get(str(token).lower(), max(idf_map.values(), default=2.0))
    normalized_idf = min(1.0, max(0.0, (idf - 1.0) / 2.0))
    return _clamp((0.65 * static) + (0.35 * normalized_idf))


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"https?://\S+|\[\d+\]|[A-Za-z]+(?:n't)?|\d+|[^\w\s]", text)]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


__all__ = ["classify_token", "build_idf", "discover_corpus_docs", "token_prior_score"]
