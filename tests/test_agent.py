from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from routemap_agent import run_agent


def test_agent_blocks_unsafe_tool_call(tmp_path: Path) -> None:
    executed = {"called": False}
    outputs = iter(
        [
            "Use a file reader.",
            '{"name":"read_file","arguments":{"path":"../secret.txt"}}',
            '{"name":"read_file","arguments":{"path":"../secret.txt"}}',
        ]
    )

    def model_fn(prompt: str) -> str:
        return next(outputs)

    def add(a: int, b: int) -> dict[str, int]:
        executed["called"] = True
        return {"sum": a + b}

    result = run_agent(
        "Read a secret file",
        {"add": {"fn": add, "schema": _add_schema(), "output_schema": _sum_schema()}},
        model_fn,
        audit_path=tmp_path / "audit.jsonl",
    )

    assert executed["called"] is False
    assert result["final"] == "escalated: tool call blocked"
    assert result["audit_ids"]
    assert result["steps"][0]["tool_firewall"]["verdict"] == "RULED_OUT_WRONG"


def test_agent_happy_path(tmp_path: Path) -> None:
    outputs = iter(
        [
            "Use add once.",
            '{"name":"add","arguments":{"a":2,"b":3}}',
            "The answer is 5.",
        ]
    )

    def model_fn(prompt: str) -> str:
        return next(outputs)

    def add(a: int, b: int) -> dict[str, int]:
        return {"sum": a + b}

    result = run_agent(
        "Compute 2 + 3",
        {"add": {"fn": add, "schema": _add_schema(), "output_schema": _sum_schema()}},
        model_fn,
        audit_path=tmp_path / "audit.jsonl",
    )

    assert result["final"] == "The answer is 5."
    assert len(result["audit_ids"]) == 2
    step = result["steps"][0]
    assert step["tool_output"] == {"sum": 5}
    assert step["tool_firewall"]["verdict"] == "NOT_RULED_OUT"
    assert step["output_check"]["verdict"] == "NOT_RULED_OUT"


def _add_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["a", "b"],
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
    }


def _sum_schema() -> dict[str, object]:
    return {
        "type": "object",
        "required": ["sum"],
        "properties": {"sum": {"type": "integer"}},
    }
