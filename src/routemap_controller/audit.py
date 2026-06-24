"""Route decision audit schema and JSONL log."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any


AUDIT_SCHEMA_VERSION = "route_decision_v1"
TASK_TYPES = {"arithmetic", "json_schema", "tool_call", "python_code", "long_context_qa", "retrieval", "unknown"}
ACTIONS = {"verify", "cheap_path", "escalate"}
OUTCOMES = {"RULED_OUT_WRONG", "NOT_RULED_OUT", "UNCHECKABLE", "accept", "FULL_COMPUTE", "FULL_COMPUTE_WITH_VALIDATOR"}


def make_record(
    *,
    task_type: str,
    object_id: str,
    route_family: str,
    route_score: float | None,
    action: str,
    validator: str,
    outcome: str,
    budget: str,
    risk: str,
    compute_avoided: bool,
    reason: str,
    timestamp: str | None = None,
    route_id: str | None = None,
) -> dict[str, Any]:
    base = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "route_id": "",
        "timestamp": timestamp or _utc_now(),
        "task_type": task_type,
        "object_id": object_id,
        "route_family": route_family,
        "route_score": route_score,
        "action": action,
        "validator": validator,
        "outcome": outcome,
        "budget": budget,
        "risk": risk,
        "compute_avoided": compute_avoided,
        "reason": reason,
    }
    base["route_id"] = route_id or _record_id(base)
    validate_record(base)
    return base


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise TypeError("route decision record must be an object")
    required = {
        "schema_version",
        "route_id",
        "timestamp",
        "task_type",
        "object_id",
        "route_family",
        "route_score",
        "action",
        "validator",
        "outcome",
        "budget",
        "risk",
        "compute_avoided",
        "reason",
    }
    missing = sorted(required - set(record))
    if missing:
        raise ValueError(f"missing route decision fields: {', '.join(missing)}")
    _expect(record, "schema_version", str)
    if record["schema_version"] != AUDIT_SCHEMA_VERSION:
        raise ValueError("schema_version must be route_decision_v1")
    _expect(record, "route_id", str)
    if not re.fullmatch(r"[0-9a-f]{40}", record["route_id"]):
        raise ValueError("route_id must be a lowercase SHA-1 hex digest")
    _expect(record, "timestamp", str)
    _validate_timestamp(record["timestamp"])
    _expect(record, "task_type", str)
    if record["task_type"] not in TASK_TYPES:
        raise ValueError(f"invalid task_type: {record['task_type']!r}")
    _expect(record, "object_id", str)
    _expect(record, "route_family", str)
    if record["route_score"] is not None and not isinstance(record["route_score"], float):
        raise TypeError("route_score must be float or null")
    _expect(record, "action", str)
    if record["action"] not in ACTIONS:
        raise ValueError(f"invalid action: {record['action']!r}")
    _expect(record, "validator", str)
    if record["action"] in {"cheap_path", "verify"} and not record["validator"]:
        raise ValueError("cheap_path and verify actions require a validator")
    _expect(record, "outcome", str)
    if record["outcome"] not in OUTCOMES:
        raise ValueError(f"invalid outcome: {record['outcome']!r}")
    _expect(record, "budget", str)
    _expect(record, "risk", str)
    _expect(record, "compute_avoided", bool)
    _expect(record, "reason", str)


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        validate_record(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        return record


def _expect(record: dict[str, Any], key: str, typ: type) -> None:
    if not isinstance(record[key], typ):
        raise TypeError(f"{key} must be {typ.__name__}")


def _validate_timestamp(value: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601") from exc


def _record_id(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload["route_id"] = ""
    payload["timestamp"] = ""
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha1(encoded.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


__all__ = ["AUDIT_SCHEMA_VERSION", "AuditLog", "make_record", "validate_record"]
