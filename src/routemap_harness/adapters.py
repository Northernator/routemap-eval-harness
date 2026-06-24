"""Model adapter contract scaffold."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class ModelFn(Protocol):
    """Callable model adapter contract for Prompt 9."""

    def __call__(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        ...
