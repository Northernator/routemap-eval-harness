"""JSONL run store for replaying model I/O outside the decision schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNS = ROOT / "data" / "outputs" / "runs.jsonl"


def append_run(record: Mapping[str, Any], path: str | Path = DEFAULT_RUNS) -> dict[str, Any]:
    """Append one free-form run replay record keyed by decision_id."""
    row = dict(record)
    if not row.get("decision_id"):
        raise ValueError("run record requires decision_id")
    run_path = Path(path)
    run_path.parent.mkdir(parents=True, exist_ok=True)
    with run_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, default=str) + "\n")
    return row


def get_run(decision_id: str, path: str | Path = DEFAULT_RUNS) -> dict[str, Any] | None:
    """Return the latest stored run record for a decision_id."""
    match = None
    for record in _read_jsonl(Path(path)):
        if record.get("decision_id") == decision_id:
            match = record
    return match


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


__all__ = ["DEFAULT_RUNS", "append_run", "get_run"]
