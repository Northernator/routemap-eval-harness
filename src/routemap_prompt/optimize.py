"""Deterministic prompt structuring from inference-time prompt tokens only."""

from __future__ import annotations

import re
from typing import Any

from routemap_token.elements import classify_element


PRESERVE_ELEMENTS = {"ENTITY", "NUMBER", "DATE", "NEGATION", "CITATION"}
CONSTRAINT_ELEMENTS = {"NEGATION", "THRESHOLD", "RISK"}
INSTRUCT_ELEMENTS = {"INSTRUCT"}
FORMAT_HINTS = {
    "json": "valid JSON",
    "csv": "CSV",
    "table": "a table",
    "list": "a concise list",
    "bullet": "a concise list",
}
TOKEN_RE = re.compile(r"https?://\S+|\[\d+\]|[A-Za-z]+(?:n't)?|[+-]?\d+(?:\.\d+)?|[<>]=?|%|\S")


def optimize_prompt(prompt: str, *, task_hint: str | None = None) -> dict[str, Any]:
    """Rewrite a prompt into a structured, checkable form without external context."""
    tokens = _tokens(prompt)
    classified = [(token, classify_element(token)) for token in tokens]
    instruct = _collect(classified, INSTRUCT_ELEMENTS)
    preserved = _collect(classified, PRESERVE_ELEMENTS)
    constraints = _collect(classified, CONSTRAINT_ELEMENTS)
    task = ", ".join(instruct) or str(task_hint or "").strip() or "answer"
    preserve_text = ", ".join(preserved) if preserved else "none detected"
    constraint_text = ", ".join(constraints) if constraints else "none detected"
    structured = "\n".join(
        [
            f"Task: {task}.",
            f"Preserve exactly: {preserve_text}.",
            f"Constraints: {constraint_text}.",
            f"Return: {_format_hint(tokens)}.",
        ]
    )
    return {
        "structured": structured,
        "preserved": preserved,
        "note": "structured from prompt-local element tags",
    }


def _tokens(prompt: str) -> list[str]:
    return TOKEN_RE.findall(str(prompt))


def _collect(classified: list[tuple[str, str]], elements: set[str]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for token, element in classified:
        if element not in elements:
            continue
        if token in seen:
            continue
        seen.add(token)
        values.append(token)
    return values


def _format_hint(tokens: list[str]) -> str:
    lowered = {token.lower().strip(".,;:!?\"'()[]") for token in tokens}
    for key, hint in FORMAT_HINTS.items():
        if key in lowered:
            return hint
    return "a direct, checkable answer"


__all__ = ["optimize_prompt"]
