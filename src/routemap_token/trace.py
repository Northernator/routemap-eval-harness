"""Trace writer for token-importance routing audits."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TRACE_FIELDS = {
    "token",
    "static_class",
    "idf",
    "context_features",
    "route_score",
    "route_action",
    "later_needed",
}


def emit_trace(path: str | Path, rows: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            missing = REQUIRED_TRACE_FIELDS - set(row)
            if missing:
                raise ValueError(f"missing trace fields: {sorted(missing)}")
            handle.write(json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n")


__all__ = ["REQUIRED_TRACE_FIELDS", "emit_trace"]
