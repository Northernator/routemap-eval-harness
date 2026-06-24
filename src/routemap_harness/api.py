"""FastAPI surface for routemap-harness."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from . import audit_store
from .core import harness_check
from .policy import repair, repair_stub


app = FastAPI(title="RouteMap Harness API")


@app.post("/check")
def check(body: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "task_type": body.get("task"),
        "raw": body.get("output"),
        "model": body.get("model"),
        "schema": body.get("spec"),
    }
    decision = harness_check(payload)
    audit_store.append(decision, _audit_path())
    return decision.to_dict()


@app.post("/repair")
def repair_decision(body: dict[str, Any]) -> dict[str, Any]:
    _repair = repair
    return dict(repair_stub(str(body.get("decision_id", ""))))


@app.get("/audit/{decision_id}")
def audit_record(decision_id: str) -> dict[str, Any]:
    record = audit_store.get_record(decision_id, _audit_path())
    if record is None:
        raise HTTPException(status_code=404, detail="decision not found")
    return record


def _audit_path() -> str:
    return str(getattr(app.state, "audit_path", audit_store.DEFAULT_AUDIT))


__all__ = ["app"]
