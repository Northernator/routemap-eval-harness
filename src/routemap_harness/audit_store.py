"""JSONL audit store scaffold."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping


def write_jsonl_record(path: Path, record: Mapping[str, Any]) -> None:
    """Write one audit record to a JSONL store."""
    raise NotImplementedError("Prompt 6 will implement JSONL writing")


def summarize_jsonl_records(records: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Summarize audit records."""
    raise NotImplementedError("Prompt 6 will implement audit summarization")
