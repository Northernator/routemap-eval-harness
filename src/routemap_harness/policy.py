"""Repair and escalation policy scaffold."""

from __future__ import annotations

from typing import Any, Mapping


def choose_policy(decision: Mapping[str, Any]) -> Mapping[str, Any]:
    """Select repair or escalation policy for a decision."""
    raise NotImplementedError("Prompts 4 and 5 will implement policy handling")


def repair_stub(decision_id: str) -> Mapping[str, Any]:
    """Placeholder repair response for Prompt 4."""
    return {
        "status": "stub",
        "decision_id": decision_id,
        "message": "repair is not wired until Prompt 4",
    }


def summarize_stub(audit: str) -> Mapping[str, Any]:
    """Placeholder audit summary response for Prompt 6."""
    return {
        "status": "stub",
        "audit": audit,
        "message": "summarize is not wired until Prompt 6",
    }
