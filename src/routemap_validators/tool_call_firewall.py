"""Tool-call firewall checker for non-executing validation."""

from __future__ import annotations

import json
import math
import ntpath
import posixpath
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Mapping

from dr_checker_schema_v1 import validate_value

from .audit import to_record, validate_record
from .pipeline import Decision
from .verdicts import Verdict


CHECKER = "tool_call_firewall"


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


def check_tool_call(
    call: Any,
    *,
    schema: Mapping[str, Any] | None = None,
    allowed_tools: list[str] | tuple[str, ...] | set[str] | None = None,
    object_id: str | None = None,
    model: str | None = None,
) -> Decision:
    """Validate a proposed tool call without executing it."""
    raw_text = _raw_text(call)
    normalized, normalize_error = _normalize_call(call)
    if normalize_error is not None:
        return _make_decision(raw_text, object_id, model, schema, None, normalize_error)
    assert normalized is not None

    tool_name = str(normalized["name"])
    arguments = normalized["arguments"]
    checks: list[_Check] = []

    allowed = {str(item) for item in (allowed_tools or []) if str(item)}
    if allowed and tool_name not in allowed:
        checks.append(_fail("allowed_tool", f"disallowed tool: {tool_name}"))
        return _make_decision(raw_text, object_id, model, schema, normalized, checks[0], checks)
    checks.append(_pass("allowed_tool", "tool allowed"))

    if schema is not None:
        schema_errors = validate_value(arguments, schema, "$.arguments")
        if schema_errors:
            checks.append(_fail("schema", f"schema violation: {schema_errors[0]}"))
            return _make_decision(raw_text, object_id, model, schema, normalized, checks[-1], checks)
        checks.append(_pass("schema", "arguments match schema"))

    safety_error = _safety_error(arguments, schema or {})
    if safety_error is not None:
        checks.append(_fail("safety", safety_error))
        return _make_decision(raw_text, object_id, model, schema, normalized, checks[-1], checks)
    checks.append(_pass("safety", "arguments pass safety checks"))

    checks.append(_pass(CHECKER, "tool call is executable"))
    return _make_decision(raw_text, object_id, model, schema, normalized, None, checks)


def _normalize_call(call: Any) -> tuple[dict[str, Any] | None, _Check | None]:
    try:
        data = json.loads(call) if isinstance(call, str) else call
    except json.JSONDecodeError as exc:
        return None, _fail("call_json", f"tool call JSON invalid: {exc.msg}")
    if isinstance(data, Mapping) and "tool_call" in data:
        data = data["tool_call"]
    if not isinstance(data, Mapping):
        return None, _fail("call_shape", "tool call must be a JSON object")
    name = data.get("name", data.get("tool"))
    if not isinstance(name, str) or not name:
        return None, _fail("tool_name", "tool name missing")
    if "arguments" in data:
        raw_args = data["arguments"]
    elif "args" in data:
        raw_args = data["args"]
    else:
        return None, _fail("arguments_json", "arguments missing")
    try:
        arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    except json.JSONDecodeError as exc:
        return None, _fail("arguments_json", f"arguments JSON invalid: {exc.msg}")
    if not isinstance(arguments, dict):
        return None, _fail("arguments_json", "arguments must parse as JSON object")
    return {"name": name, "arguments": arguments}, None


def _safety_error(arguments: Mapping[str, Any], schema: Mapping[str, Any]) -> str | None:
    return _walk(arguments, schema, "$")


def _walk(value: Any, schema: Mapping[str, Any], path: str) -> str | None:
    if isinstance(value, str):
        if _unsafe_path(value):
            return f"unsafe path at {path}: {value}"
        if _date_field(schema) and not _valid_iso_date(value):
            return f"invalid ISO date at {path}: {value}"
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return f"impossible number at {path}: NaN/Infinity"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum") if isinstance(schema, Mapping) else None
        if minimum == 0 and value < 0:
            return f"negative number at {path} violates minimum 0"
    if isinstance(value, Mapping):
        properties = schema.get("properties", {}) if isinstance(schema, Mapping) else {}
        for key, item in value.items():
            child_schema = properties.get(key, {}) if isinstance(properties, Mapping) else {}
            error = _walk(item, child_schema if isinstance(child_schema, Mapping) else {}, f"{path}.{key}")
            if error:
                return error
    if isinstance(value, list):
        item_schema = schema.get("items", {}) if isinstance(schema, Mapping) else {}
        for index, item in enumerate(value):
            error = _walk(item, item_schema if isinstance(item_schema, Mapping) else {}, f"{path}[{index}]")
            if error:
                return error
    return None


def _unsafe_path(value: str) -> bool:
    lowered = value.lower()
    system_prefixes = ("/etc/", "/bin/", "/usr/", "/var/", "/root/", "c:\\windows", "c:\\users")
    return (
        ".." in value.replace("\\", "/").split("/")
        or posixpath.isabs(value)
        or ntpath.isabs(value)
        or any(lowered.startswith(prefix) for prefix in system_prefixes)
    )


def _date_field(schema: Mapping[str, Any]) -> bool:
    return schema.get("format") in {"date", "date-time"} or schema.get("type") == "date"


def _valid_iso_date(value: str) -> bool:
    try:
        if "T" in value:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _make_decision(
    raw: str,
    object_id: str | None,
    model: str | None,
    schema: Mapping[str, Any] | None,
    normalized: Mapping[str, Any] | None,
    failure: _Check | None,
    checks: list[_Check] | None = None,
) -> Decision:
    all_checks = list(checks or ([] if failure is None else [failure]))
    verdict = Verdict.NOT_RULED_OUT if failure is None else Verdict.RULED_OUT_WRONG
    reason = "tool call is executable" if failure is None else failure.reason
    decision = Decision(
        verdict=verdict,
        reason=reason,
        checker=CHECKER if failure is None else failure.name,
        coverage_note=None,
        extraction_ok=normalized is not None,
        extraction_note="tool call normalized" if normalized is not None else "tool call extraction failed",
        task_type="tool_call",
        object_id=object_id,
        checks=[item.to_record() for item in all_checks],
    )
    record = to_record(
        decision,
        raw=raw,
        extracted=json.dumps(normalized, ensure_ascii=True, sort_keys=True) if normalized is not None else None,
        spec=schema,
        model=model,
    )
    validate_record(record)
    object.__setattr__(decision, "record", record)
    return decision


def _fail(name: str, reason: str) -> _Check:
    return _Check(name, Verdict.RULED_OUT_WRONG, reason)


def _pass(name: str, reason: str) -> _Check:
    return _Check(name, Verdict.NOT_RULED_OUT, reason)


def _raw_text(call: Any) -> str:
    return call if isinstance(call, str) else json.dumps(call, ensure_ascii=True, sort_keys=True, default=str)


__all__ = ["check_tool_call"]
