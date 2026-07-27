"""Access bundled RouteMap schema resources."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any


DECISION_SCHEMA_RESOURCE = "schemas/harness_decision_v1.schema.json"


def decision_schema_text() -> str:
    """Return the bundled canonical harness decision schema."""
    resource = files("routemap_harness").joinpath(DECISION_SCHEMA_RESOURCE)
    return resource.read_text(encoding="utf-8")


def load_decision_schema() -> dict[str, Any]:
    """Load the bundled canonical harness decision schema."""
    return json.loads(decision_schema_text())


__all__ = ["DECISION_SCHEMA_RESOURCE", "decision_schema_text", "load_decision_schema"]
