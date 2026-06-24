"""FastAPI surface for routemap-harness."""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import audit_store
from .adapters import DEFAULT_MODEL_REF, EXPERIMENTAL_CLI_RUNTIMES
from .core import harness_check
from .policy import repair, repair_stub


app = FastAPI(title="RouteMap Harness API")


@app.get("/")
def control_page() -> FileResponse:
    return FileResponse(_control_page_path(), media_type="text/html")


@app.get("/models")
def models() -> list[dict[str, Any]]:
    return _model_statuses()


@app.post("/check")
def check(body: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "task_type": body.get("task"),
        "raw": body.get("output"),
        "model": body.get("model"),
        "schema": body.get("spec"),
    }
    decision = harness_check(payload, strict=bool(body.get("strict")))
    audit_store.append(decision, _audit_path())
    return decision.to_dict()


@app.post("/repair")
def repair_decision(body: dict[str, Any]) -> dict[str, Any]:
    _repair = repair
    return dict(repair_stub(str(body.get("decision_id", ""))))


@app.get("/audit")
def audit_tail(limit: int = 20) -> list[dict[str, Any]]:
    return audit_store.tail(_audit_path(), limit)


@app.get("/audit/{decision_id}")
def audit_record(decision_id: str) -> dict[str, Any]:
    record = audit_store.get_record(decision_id, _audit_path())
    if record is None:
        raise HTTPException(status_code=404, detail="decision not found")
    return record


def _audit_path() -> str:
    return str(getattr(app.state, "audit_path", audit_store.DEFAULT_AUDIT))


def _control_page_path() -> Path:
    return Path(__file__).resolve().parent / "web" / "control.html"


def _model_statuses() -> list[dict[str, Any]]:
    ollama_available = _ollama_available()
    openai_available = bool(os.environ.get("OPENAI_API_KEY"))
    anthropic_available = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return [
        {
            "model_ref": DEFAULT_MODEL_REF,
            "runtime": "ollama",
            "auth_mode": "local",
            "available": ollama_available,
            "note": "local Ollama daemon reachable" if ollama_available else "local Ollama daemon not reachable",
        },
        {
            "model_ref": os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
            "runtime": "openai",
            "auth_mode": "api_key",
            "available": openai_available,
            "note": "OPENAI_API_KEY set" if openai_available else "OPENAI_API_KEY not set",
        },
        {
            "model_ref": os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            "runtime": "anthropic",
            "auth_mode": "api_key",
            "available": anthropic_available,
            "note": "ANTHROPIC_API_KEY set" if anthropic_available else "ANTHROPIC_API_KEY not set",
        },
        *[
            {
                "model_ref": runtime,
                "runtime": runtime,
                "auth_mode": "cli",
                "available": False,
                "note": "experimental runtime disabled in local control page",
            }
            for runtime in sorted(EXPERIMENTAL_CLI_RUNTIMES)
        ],
    ]


def _ollama_available() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=0.25) as response:
            return 200 <= int(response.status) < 500
    except (OSError, urllib.error.URLError, TimeoutError):
        return False


__all__ = ["app"]
