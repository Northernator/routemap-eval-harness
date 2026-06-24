"""Core harness decision API scaffold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Decision:
    """Placeholder decision object for Prompt 1."""

    payload: Mapping[str, Any]


def harness_check(payload: Mapping[str, Any]) -> Decision:
    """Evaluate a payload and return a harness decision."""
    raise NotImplementedError("Prompt 1 will implement harness_check")
