from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_harness_schema_loads_as_valid_json() -> None:
    schema_path = ROOT / "schemas" / "harness_decision_v1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["properties"]["schema_version"]["const"] == "harness_decision_v1"


def test_routemap_harness_package_imports() -> None:
    import routemap_harness

    assert routemap_harness.__all__ == ["HarnessDecision", "harness_check"]
