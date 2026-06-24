"""Task envelope classifier for the unified controller."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


TASK_TYPES = {"arithmetic", "json_schema", "tool_call", "python_code", "long_context_qa", "retrieval", "unknown"}


@dataclass(frozen=True)
class TaskEnvelope:
    task_type: str
    risk: str
    verifier_needed: bool
    reason: str


def classify(input: Any, task_hint: str | None = None) -> TaskEnvelope:
    if task_hint:
        task_type = task_hint if task_hint in TASK_TYPES else "unknown"
        return TaskEnvelope(task_type, "low", task_type in {"arithmetic", "json_schema", "tool_call", "python_code"}, "task hint override")
    if isinstance(input, dict):
        if input.get("task_type") in TASK_TYPES:
            task_type = str(input["task_type"])
            return TaskEnvelope(task_type, str(input.get("risk", "low")), task_type in {"arithmetic", "json_schema", "tool_call", "python_code"}, "explicit task_type")
        if "tool_call" in input:
            return TaskEnvelope("tool_call", "low", True, "tool_call field")
        if ("name" in input or "tool" in input) and ("arguments" in input or "args" in input):
            return TaskEnvelope("tool_call", "low", True, "tool name plus arguments")
        if "expr" in input and "claimed_answer" in input:
            return TaskEnvelope("arithmetic", "low", True, "expression plus claimed_answer")
        if "raw" in input and "schema" in input:
            return TaskEnvelope("json_schema", "low", True, "raw output plus schema")
        if "code" in input or "```" in str(input.get("raw", "")):
            return TaskEnvelope("python_code", "low", True, "code field or fenced code")
        if "passage" in input and "question" in input:
            return TaskEnvelope("long_context_qa", "low", True, "passage plus question")
        if "query" in input and ("documents" in input or "corpus" in input):
            return TaskEnvelope("retrieval", "low", True, "query plus retrieval corpus")
    text = str(input).strip()
    if re.search(r"\bmod\s+\d+\b", text, flags=re.IGNORECASE) or re.search(r"\d+\s*(?:\*\*|\^|\+|\*|!)", text):
        return TaskEnvelope("arithmetic", "low", True, "arithmetic expression shape")
    if "```" in text:
        return TaskEnvelope("python_code", "low", True, "fenced code")
    if text.startswith("{") and "schema" in text.lower():
        return TaskEnvelope("json_schema", "low", True, "JSON/schema text shape")
    if "?" in text and len(text.split()) > 8:
        return TaskEnvelope("long_context_qa", "low", True, "question-like long context")
    if text and len(text.split()) <= 12:
        return TaskEnvelope("retrieval", "low", True, "bare query string")
    return TaskEnvelope("unknown", "high", False, "no known route signature")


__all__ = ["TaskEnvelope", "classify"]
