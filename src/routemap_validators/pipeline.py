"""Integrated extract-then-check validator pipeline."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from dr_checker_framework_v1 import default_router
from dr_output_extraction_v1 import extract_code, extract_integer, extract_json

from .audit import to_record, validate_record
from .verdicts import Verdict


if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)


@dataclass(frozen=True)
class Decision:
    verdict: str
    reason: str
    checker: str | None
    coverage_note: str | None
    extraction_ok: bool
    extraction_note: str
    task_type: str
    object_id: str | None
    checks: list[dict[str, Any]]
    record: dict[str, Any] = field(default_factory=dict)


def check_output(
    raw: str,
    task_type: str,
    spec: Any = None,
    *,
    object_id: str | None = None,
    model: str | None = None,
) -> Decision:
    if task_type == "arithmetic":
        extracted, ok, note = extract_integer(raw)
        if not ok:
            return _unchecked(raw, task_type, spec, object_id, model, note, "integer extraction failed")
        expr_spec, moduli = _arithmetic_spec(spec)
        if expr_spec is None:
            return _unchecked(raw, task_type, spec, object_id, model, note, "arithmetic spec missing")
        claim: dict[str, Any] = {
            "type": "arithmetic",
            "expr_spec": expr_spec,
            "claimed_answer": int(extracted),
        }
        if moduli is not None:
            claim["moduli"] = moduli
        return _route(raw, task_type, spec, object_id, model, extracted, note, claim)
    if task_type == "python_code":
        extracted, ok, note = extract_code(raw)
        if not ok:
            return _unchecked(raw, task_type, spec, object_id, model, note, "code extraction failed")
        return _route(raw, task_type, spec, object_id, model, extracted, note, {"type": "python_code", "source": extracted})
    if task_type == "json_schema":
        extracted, ok, note = extract_json(raw)
        if not ok:
            return _unchecked(raw, task_type, spec, object_id, model, note, "json extraction failed")
        if spec is None:
            return _unchecked(raw, task_type, spec, object_id, model, note, "json schema spec missing")
        return _route(
            raw,
            task_type,
            spec,
            object_id,
            model,
            extracted,
            note,
            {"type": "json_schema", "schema": spec, "output": extracted},
        )
    raise ValueError(f"unsupported task_type: {task_type!r}")


def _route(
    raw: str,
    task_type: str,
    spec: Any,
    object_id: str | None,
    model: str | None,
    extracted: str,
    note: str,
    claim: dict[str, Any],
) -> Decision:
    result = default_router().check(claim)
    checks = [dict(item) for item in result["checks"]]
    selected = _selected_check(checks)
    return _decision(
        raw=raw,
        task_type=task_type,
        spec=spec,
        object_id=object_id,
        model=model,
        extracted=extracted,
        verdict=result["verdict"],
        reason=result["reason"],
        checker=selected.get("checker") if selected else None,
        coverage_note=selected.get("coverage_note") if selected else None,
        extraction_ok=True,
        extraction_note=note,
        checks=checks,
    )


def _unchecked(
    raw: str,
    task_type: str,
    spec: Any,
    object_id: str | None,
    model: str | None,
    extraction_note: str,
    reason: str,
) -> Decision:
    return _decision(
        raw=raw,
        task_type=task_type,
        spec=spec,
        object_id=object_id,
        model=model,
        extracted=None,
        verdict=Verdict.UNCHECKABLE,
        reason=reason,
        checker=None,
        coverage_note=None,
        extraction_ok=False,
        extraction_note=extraction_note,
        checks=[],
    )


def _decision(
    *,
    raw: str,
    task_type: str,
    spec: Any,
    object_id: str | None,
    model: str | None,
    extracted: str | None,
    verdict: str,
    reason: str,
    checker: str | None,
    coverage_note: str | None,
    extraction_ok: bool,
    extraction_note: str,
    checks: list[dict[str, Any]],
) -> Decision:
    decision = Decision(
        verdict=verdict,
        reason=reason,
        checker=checker,
        coverage_note=coverage_note,
        extraction_ok=extraction_ok,
        extraction_note=extraction_note,
        task_type=task_type,
        object_id=object_id,
        checks=checks,
    )
    record = to_record(decision, raw=raw, extracted=extracted, spec=spec, model=model)
    validate_record(record)
    object.__setattr__(decision, "record", record)
    return decision


def _selected_check(checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for check in checks:
        if check["verdict"] == Verdict.RULED_OUT_WRONG:
            return check
    return checks[0] if checks else None


def _arithmetic_spec(spec: Any) -> tuple[Any | None, Any | None]:
    if isinstance(spec, dict) and "expr_spec" in spec:
        return spec.get("expr_spec"), spec.get("moduli")
    return spec, None


__all__ = ["Decision", "check_output"]
