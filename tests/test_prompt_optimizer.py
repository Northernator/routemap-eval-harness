from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_prompt import optimize_prompt


def test_optimize_prompt_preserves_prompt_literals() -> None:
    prompt = "Please summarize Acme report 42 from 2026 and do not omit [7]."

    first = optimize_prompt(prompt, task_hint="summary")
    second = optimize_prompt(prompt, task_hint="summary")

    assert first == second
    structured = first["structured"]
    assert structured.startswith("Task:")
    assert "Preserve exactly:" in structured
    assert "Acme" in structured
    assert "42" in structured
    assert "2026" in structured
    assert "not" in structured
    assert "[7]" in structured
    assert {"Acme", "42", "2026", "not", "[7]"} <= set(first["preserved"])
    assert "gold" not in structured.lower()
