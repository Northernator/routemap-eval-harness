"""Versioned audit records for RouteMap validator decisions."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from typing import Any

from .verdicts import Verdict


AUDIT_SCHEMA_VERSION = "validator_audit_v1"


@dataclass(frozen=True)
class AuditRecord:
    record: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return dict(self.record)


def to_record(
    decision: Any,
    *,
    raw: str | None = None,
    extracted: str | None = None,
    spec: Any = None,
    model: str | None = None,
    timestamp: str | None = None,
    record_id: str | None = None,
) -> dict[str, Any]:
    existing = getattr(decision, "record", None) or {}
    raw_sha1 = existing.get("raw_sha1") if raw is None and existing else _sha1_text(raw)
    extracted_repr = existing.get("extracted_repr") if raw is None else extracted
    spec_hash = existing.get("spec_hash") if raw is None else _hash_json(spec)
    model_value = existing.get("model") if raw is None else model
    timestamp_value = timestamp or existing.get("timestamp") or _utc_now()
    checks = [dict(item) for item in getattr(decision, "checks", [])]
    base = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "record_id": "",
        "timestamp": timestamp_value,
        "task_type": getattr(decision, "task_type"),
        "object_id": getattr(decision, "object_id"),
        "model": model_value,
        "raw_sha1": raw_sha1,
        "extraction_ok": getattr(decision, "extraction_ok"),
        "extraction_note": getattr(decision, "extraction_note"),
        "extracted_repr": extracted_repr,
        "checker": getattr(decision, "checker"),
        "verdict": getattr(decision, "verdict"),
        "reason": getattr(decision, "reason"),
        "coverage_note": getattr(decision, "coverage_note"),
        "checks": checks,
        "spec_hash": spec_hash,
    }
    base["record_id"] = record_id or existing.get("record_id") or _record_id(base)
    validate_record(base)
    return base


def validate_record(record: dict[str, Any]) -> None:
    if not isinstance(record, dict):
        raise TypeError("audit record must be an object")
    required = {
        "schema_version",
        "record_id",
        "timestamp",
        "task_type",
        "object_id",
        "model",
        "raw_sha1",
        "extraction_ok",
        "extraction_note",
        "extracted_repr",
        "checker",
        "verdict",
        "reason",
        "coverage_note",
        "checks",
        "spec_hash",
    }
    missing = sorted(required - set(record))
    if missing:
        raise ValueError(f"missing audit fields: {', '.join(missing)}")
    _expect(record, "schema_version", str)
    if record["schema_version"] != AUDIT_SCHEMA_VERSION:
        raise ValueError("schema_version must be validator_audit_v1")
    _expect(record, "record_id", str)
    _expect(record, "timestamp", str)
    _validate_timestamp(record["timestamp"])
    _expect(record, "task_type", str)
    _expect_nullable(record, "object_id", str)
    _expect_nullable(record, "model", str)
    _expect(record, "raw_sha1", str)
    if not re.fullmatch(r"[0-9a-f]{40}", record["raw_sha1"]):
        raise ValueError("raw_sha1 must be a lowercase SHA-1 hex digest")
    _expect(record, "extraction_ok", bool)
    _expect(record, "extraction_note", str)
    _expect_nullable(record, "extracted_repr", str)
    _expect_nullable(record, "checker", str)
    _expect(record, "verdict", str)
    if record["verdict"] not in Verdict.ALL:
        raise ValueError(f"invalid verdict: {record['verdict']!r}")
    _expect(record, "reason", str)
    _expect_nullable(record, "coverage_note", str)
    _expect_nullable(record, "spec_hash", str)
    if record["spec_hash"] is not None and not re.fullmatch(r"[0-9a-f]{40}", record["spec_hash"]):
        raise ValueError("spec_hash must be null or a lowercase SHA-1 hex digest")
    if not isinstance(record["checks"], list):
        raise TypeError("checks must be an array")
    for index, check in enumerate(record["checks"]):
        if not isinstance(check, dict):
            raise TypeError(f"checks[{index}] must be an object")
        for key in ("checker", "verdict", "reason", "coverage_note"):
            if key not in check:
                raise ValueError(f"checks[{index}] missing {key}")
        _expect(check, "checker", str, prefix=f"checks[{index}].")
        _expect(check, "verdict", str, prefix=f"checks[{index}].")
        if check["verdict"] not in Verdict.ALL:
            raise ValueError(f"checks[{index}].verdict is invalid")
        _expect(check, "reason", str, prefix=f"checks[{index}].")
        _expect_nullable(check, "coverage_note", str, prefix=f"checks[{index}].")


class AuditLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        validate_record(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        return record

    def write_decision(self, decision: Any) -> dict[str, Any]:
        return self.append(to_record(decision))


def _expect(obj: dict[str, Any], key: str, typ: type, prefix: str = "") -> None:
    if not isinstance(obj[key], typ):
        raise TypeError(f"{prefix}{key} must be {typ.__name__}")


def _expect_nullable(obj: dict[str, Any], key: str, typ: type, prefix: str = "") -> None:
    if obj[key] is not None and not isinstance(obj[key], typ):
        raise TypeError(f"{prefix}{key} must be null or {typ.__name__}")


def _validate_timestamp(value: str) -> None:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601") from exc


def _sha1_text(value: str | None) -> str:
    return sha1(("" if value is None else str(value)).encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str | None:
    if value is None:
        return None
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha1(payload.encode("utf-8")).hexdigest()


def _record_id(record: dict[str, Any]) -> str:
    payload = dict(record)
    payload["record_id"] = ""
    payload["timestamp"] = ""
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return sha1(encoded.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


__all__ = ["AUDIT_SCHEMA_VERSION", "AuditLog", "AuditRecord", "to_record", "validate_record"]
