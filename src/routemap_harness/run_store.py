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


def export_failures(audit_path: str | Path, runs_path: str | Path) -> list[dict[str, Any]]:
    """Join audit and run logs into training rows for failed/repaired outcomes."""
    runs = {
        str(record.get("decision_id")): record
        for record in _read_jsonl(Path(runs_path))
        if record.get("decision_id")
    }
    rows: list[dict[str, Any]] = []
    for decision in _read_jsonl(Path(audit_path)):
        if not _is_failure(decision):
            continue
        run = runs.get(str(decision.get("decision_id")))
        if run is None:
            continue
        rows.append(_failure_row(decision, run))
    return rows


def _is_failure(decision: Mapping[str, Any]) -> bool:
    return (
        decision.get("final_status") in {"rejected", "escalated", "repaired"}
        or decision.get("verdict") == "RULED_OUT_WRONG"
    )


def _failure_row(decision: Mapping[str, Any], run: Mapping[str, Any]) -> dict[str, Any]:
    model_output = run.get("model_output")
    final_output = run.get("final_output")
    return {
        "prompt": run.get("prompt"),
        "model_output": model_output,
        "failure_type": f"{decision.get('task_type')}:{_failure_detail(decision)}",
        "validator_reason": decision.get("reason"),
        "repair_prompt": _repair_prompt(run),
        "corrected_output": final_output if final_output != model_output else None,
        "final_status": decision.get("final_status"),
    }


def _failure_detail(decision: Mapping[str, Any]) -> str:
    record = decision.get("validator_record")
    checks = record.get("checks") if isinstance(record, Mapping) else None
    if isinstance(checks, list):
        for check in checks:
            if isinstance(check, Mapping) and check.get("verdict") == "RULED_OUT_WRONG":
                return str(check.get("checker") or decision.get("verdict"))
    return str(decision.get("verdict"))


def _repair_prompt(run: Mapping[str, Any]) -> Any:
    attempts = run.get("repair_attempts")
    if not isinstance(attempts, list):
        return None
    for attempt in attempts:
        if not isinstance(attempt, Mapping):
            continue
        record = attempt.get("validator_record")
        if isinstance(record, Mapping) and record.get("repair_prompt"):
            return record.get("repair_prompt")
    return None


def _read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


__all__ = ["DEFAULT_RUNS", "append_run", "export_failures", "get_run"]
