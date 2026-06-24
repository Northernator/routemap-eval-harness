"""Grounded QA checker for source-supported answers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from routemap_token.elements import classify_element

from .audit import to_record, validate_record
from .pipeline import Decision
from .verdicts import Verdict


CHECKER = "grounding_guard"
CONTENT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of",
    "on", "or", "that", "the", "this", "to", "with",
}


@dataclass(frozen=True)
class _Check:
    name: str
    verdict: str
    reason: str

    def to_record(self) -> dict[str, Any]:
        return {
            "checker": self.name,
            "verdict": self.verdict,
            "reason": self.reason,
            "coverage_note": None,
        }


def check_grounding(
    answer: Any,
    source: Any,
    *,
    require_citation: bool = True,
    object_id: str | None = None,
    model: str | None = None,
) -> Decision:
    """Check that answer entities, numbers, dates, and citations are grounded in source text."""
    answer_text = str(answer or "")
    source_text, source_keys = _source_text_and_keys(source)
    source_lower = source_text.lower()
    checks: list[_Check] = []

    tokens = _tokens(answer_text)
    checkable = _checkable_tokens(tokens)
    entities = sorted({tok for tok, element in checkable if element == "ENTITY"}, key=str.lower)
    quantities = sorted({tok for tok, element in checkable if element in {"NUMBER", "DATE"}}, key=str.lower)

    if not checkable:
        checks.append(_fail("checkable_claims", "no checkable entities, numbers, or dates in answer", Verdict.UNCHECKABLE))
        return _make_decision(answer_text, source, object_id, model, Verdict.UNCHECKABLE, "no checkable entities, numbers, or dates in answer", checks)

    missing_entities = [token for token in entities if token.lower() not in source_lower]
    if missing_entities:
        checks.append(_fail("entity_support", "missing entities: " + ", ".join(missing_entities)))
    else:
        checks.append(_pass("entity_support", "all answer entities appear in source"))

    missing_quantities = [token for token in quantities if token.lower() not in source_lower]
    if missing_quantities:
        checks.append(_fail("quantity_support", "missing numbers/dates: " + ", ".join(missing_quantities)))
    else:
        checks.append(_pass("quantity_support", "all answer numbers/dates appear in source"))

    if require_citation:
        if _has_citation(answer_text, source_keys):
            checks.append(_pass("citation", "answer includes citation marker"))
        else:
            checks.append(_fail("citation", "missing citation marker"))

    overlap = _content_tokens(answer_text) & _content_tokens(source_text)
    if overlap:
        checks.append(_pass("evidence_overlap", "shared content tokens: " + ", ".join(sorted(overlap)[:5])))
    else:
        checks.append(_fail("evidence_overlap", "no non-trivial evidence overlap"))

    failures = [check for check in checks if check.verdict == Verdict.RULED_OUT_WRONG]
    if failures:
        reason = "; ".join(check.reason for check in failures)
        return _make_decision(answer_text, source, object_id, model, Verdict.RULED_OUT_WRONG, reason, checks)
    checks.append(_pass(CHECKER, "answer is grounded in source"))
    return _make_decision(answer_text, source, object_id, model, Verdict.NOT_RULED_OUT, "answer is grounded in source", checks)


def _source_text_and_keys(source: Any) -> tuple[str, set[str]]:
    if isinstance(source, dict):
        text_parts: list[str] = []
        keys: set[str] = set()
        for key, value in source.items():
            keys.add(str(key))
            text_parts.append(str(value))
        return "\n".join(text_parts), keys
    if isinstance(source, list):
        text_parts = []
        keys = set()
        for index, item in enumerate(source, start=1):
            if isinstance(item, dict):
                key = str(item.get("id", index))
                keys.add(key)
                text_parts.append(str(item.get("text", item)))
            else:
                keys.add(str(index))
                text_parts.append(str(item))
        return "\n".join(text_parts), keys
    return str(source or ""), set()


def _tokens(text: str) -> list[str]:
    return re.findall(r"\[[0-9A-Za-z_.:-]+\]|[A-Za-z][A-Za-z0-9_-]*|\d{4}-\d{2}-\d{2}|\d+(?:\.\d+)?", text)


def _checkable_tokens(tokens: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for token in tokens:
        if token.startswith("[") and token.endswith("]"):
            continue
        element = classify_element(token)
        if element in {"ENTITY", "NUMBER", "DATE"}:
            out.append((token, element))
    return out


def _has_citation(answer: str, source_keys: set[str]) -> bool:
    if re.search(r"\[[0-9A-Za-z_.:-]+\]", answer):
        return True
    lower = answer.lower()
    return any(key and key.lower() in lower for key in source_keys)


def _content_tokens(text: str) -> set[str]:
    return {
        token.lower()
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]*|\d+(?:\.\d+)?", text)
        if len(token) > 2 and token.lower() not in CONTENT_STOPWORDS
    }


def _make_decision(
    answer: str,
    source: Any,
    object_id: str | None,
    model: str | None,
    verdict: str,
    reason: str,
    checks: list[_Check],
) -> Decision:
    decision = Decision(
        verdict=verdict,
        reason=reason,
        checker=CHECKER,
        coverage_note=None,
        extraction_ok=True,
        extraction_note="answer/source provided",
        task_type="grounded_qa",
        object_id=object_id,
        checks=[check.to_record() for check in checks],
    )
    record = to_record(
        decision,
        raw=answer,
        extracted=answer,
        spec={"source": source},
        model=model,
    )
    validate_record(record)
    object.__setattr__(decision, "record", record)
    return decision


def _fail(name: str, reason: str, verdict: str = Verdict.RULED_OUT_WRONG) -> _Check:
    return _Check(name, verdict, reason)


def _pass(name: str, reason: str) -> _Check:
    return _Check(name, Verdict.NOT_RULED_OUT, reason)


__all__ = ["check_grounding"]
