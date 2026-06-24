"""JSONL audit store and summarizer for canonical harness decisions."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = ROOT / "data" / "outputs" / "audit.jsonl"
DEFAULT_SCHEMA = ROOT / "schemas" / "harness_decision_v1.schema.json"


def append(decision: Any, path: str | Path = DEFAULT_AUDIT) -> dict[str, Any]:
    """Validate and append one canonical harness decision record."""
    record = _as_record(decision)
    validate_record(record)
    audit_path = Path(path)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True, sort_keys=True, default=str) + "\n")
    return record


def summarize(path: str | Path) -> dict[str, Any]:
    """Summarize a harness audit JSONL file and return metrics plus Markdown."""
    records = list(_read_jsonl(Path(path)))
    summary = summarize_records(records)
    summary["markdown"] = markdown_table(summary)
    return summary


def get_record(decision_id: str, path: str | Path = DEFAULT_AUDIT) -> dict[str, Any] | None:
    """Return one stored harness audit record by decision_id."""
    for record in _read_jsonl(Path(path)):
        if record.get("decision_id") == decision_id:
            return record
    return None


def tail(path: str | Path = DEFAULT_AUDIT, limit: int = 20) -> list[dict[str, Any]]:
    """Return the last N audit records, newest first."""
    safe_limit = max(0, int(limit))
    if safe_limit == 0:
        return []
    return list(reversed(list(_read_jsonl(Path(path)))[-safe_limit:]))


def summarize_records(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [dict(record) for record in records]
    summary = _summary_for_rows(rows)
    summary["by_model"] = {
        model: _summary_for_rows(model_rows)
        for model, model_rows in sorted(_group_by_model(rows).items())
    }
    return summary


def _summary_for_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    final_status = _counts(rows, "final_status")
    repaired = final_status.get("repaired", 0)
    escalated = final_status.get("escalated", 0)
    accepted = final_status.get("accepted", 0)
    repair_attempts = sum(1 for row in rows if int(row.get("repair_attempt", 0)) > 0)
    false_accepts = sum(1 for row in rows if _is_false_accept(row))
    latencies = sorted(float(row.get("latency_ms", 0.0)) for row in rows)
    return {
        "total": total,
        "counts": {
            "task_type": _counts(rows, "task_type"),
            "route_family": _counts(rows, "route_family"),
            "verdict": _counts(rows, "verdict"),
            "action": _counts(rows, "action"),
            "final_status": final_status,
        },
        "repair_success_rate": _rate(repaired, repair_attempts),
        "escalation_rate": _rate(escalated, total),
        "acceptance_rate": _rate(accepted, total),
        "false_accepts": false_accepts,
        "latency_ms": {
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
        },
    }


def _group_by_model(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_model_key(row), []).append(row)
    return grouped


def _model_key(row: Mapping[str, Any]) -> str:
    for key in ("model", "model_ref", "runtime", "provider"):
        value = row.get(key)
        if value:
            return str(value)
    return "unknown"


def markdown_table(summary: Mapping[str, Any]) -> str:
    rows: list[tuple[str, str, str]] = [
        ("total", "all", str(summary["total"])),
        ("repair_success_rate", "all", f"{float(summary['repair_success_rate']):.3f}"),
        ("escalation_rate", "all", f"{float(summary['escalation_rate']):.3f}"),
        ("false_accepts", "all", str(summary["false_accepts"])),
        ("latency_ms", "p50", f"{float(summary['latency_ms']['p50']):.3f}"),
        ("latency_ms", "p95", f"{float(summary['latency_ms']['p95']):.3f}"),
    ]
    counts = summary["counts"]
    for group in ("task_type", "route_family", "verdict", "action", "final_status"):
        for key, value in sorted(counts[group].items()):
            rows.append((group, key, str(value)))
    lines = ["| metric | value | count |", "| --- | --- | --- |"]
    lines.extend(f"| {metric} | {value} | {count} |" for metric, value, count in rows)
    return "\n".join(lines)


def validate_record(record: Mapping[str, Any]) -> None:
    """Validate a record against schemas/harness_decision_v1.schema.json."""
    schema = _schema()
    allowed = set(schema["properties"])
    extra = set(record) - allowed
    if extra:
        raise ValueError("unexpected harness decision fields: " + ", ".join(sorted(extra)))
    missing = [key for key in schema["required"] if key not in record]
    if missing:
        raise ValueError("missing harness decision fields: " + ", ".join(missing))

    for key, spec in schema["properties"].items():
        if key not in record:
            continue
        _validate_value(key, record[key], spec)
    if record.get("validator") == "" and (record.get("action") != "escalate" or record.get("task_type") != "unknown"):
        raise ValueError("empty validator is allowed only when action=escalate on unknown")


def write_jsonl_record(path: Path, record: Mapping[str, Any]) -> None:
    """Backward-compatible JSONL writer."""
    append(record, path)


def summarize_jsonl_records(records: Iterable[Mapping[str, Any]]) -> Mapping[str, Any]:
    """Backward-compatible record summarizer."""
    summary = summarize_records(records)
    summary["markdown"] = markdown_table(summary)
    return summary


def _as_record(decision: Any) -> dict[str, Any]:
    if hasattr(decision, "to_dict"):
        record = decision.to_dict()
    else:
        record = dict(decision)
    return {key: value for key, value in record.items() if value is not None}


def _schema() -> dict[str, Any]:
    return json.loads(DEFAULT_SCHEMA.read_text(encoding="utf-8"))


def _validate_value(key: str, value: Any, spec: Mapping[str, Any]) -> None:
    if "const" in spec and value != spec["const"]:
        raise ValueError(f"{key} must be {spec['const']!r}")
    if "enum" in spec and value not in spec["enum"]:
        raise ValueError(f"{key} must be one of {', '.join(map(str, spec['enum']))}")
    typ = spec.get("type")
    if typ and not _type_matches(value, str(typ)):
        raise TypeError(f"{key} must be {typ}")
    if "minLength" in spec and isinstance(value, str) and len(value) < int(spec["minLength"]):
        raise ValueError(f"{key} must not be empty")
    if "minimum" in spec and isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < float(spec["minimum"]):
            raise ValueError(f"{key} must be >= {spec['minimum']}")


def _type_matches(value: Any, typ: str) -> bool:
    if typ == "object":
        return isinstance(value, dict)
    if typ == "string":
        return isinstance(value, str)
    if typ == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if typ == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return True


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key, "")) for row in rows))


def _rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    index = round((len(values) - 1) * q)
    return values[index]


def _is_false_accept(record: Mapping[str, Any]) -> bool:
    validator_record = record.get("validator_record")
    return (
        isinstance(validator_record, Mapping)
        and bool(validator_record.get("known_wrong"))
        and record.get("final_status") == "accepted"
    )


__all__ = [
    "append",
    "get_record",
    "markdown_table",
    "summarize",
    "summarize_jsonl_records",
    "summarize_records",
    "tail",
    "validate_record",
    "write_jsonl_record",
]
