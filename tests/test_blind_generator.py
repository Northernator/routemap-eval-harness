from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from blind import generate_blind_v1  # noqa: E402


def test_blind_generator_preserves_frozen_outputs_without_process_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_marker = "private-api-key-must-not-be-persisted"
    output_dir = tmp_path / "blind-v1"
    monkeypatch.setenv("OPENAI_API_KEY", private_marker)
    monkeypatch.setattr(generate_blind_v1, "OUT", output_dir)

    generate_blind_v1.main()

    generated_manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    frozen_manifest = json.loads(
        (ROOT / "data" / "blind" / "v1" / "manifest.json").read_text(encoding="utf-8")
    )
    assert generated_manifest["sha256"] == frozen_manifest["sha256"]
    assert all(private_marker not in path.read_text(encoding="utf-8") for path in output_dir.iterdir())
