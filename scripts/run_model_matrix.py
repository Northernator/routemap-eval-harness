#!/usr/bin/env python3
"""Run fixed prompts through configured model adapters and validate with the harness."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from routemap_harness import harness_check
from routemap_harness.adapters import ModelAdapterError, ModelAdapterUnavailable, model_fn


OUT = ROOT / "EVIDENCE"

PROMPTS = [
    {
        "name": "json_schema",
        "prompt": "Return ONLY JSON: id string, score 0..100, status pass/fail, tags nonempty array.",
        "payload": {
            "task_type": "json_schema",
            "schema": {
                "type": "object",
                "required": ["id", "score", "status", "tags"],
                "properties": {
                    "id": {"type": "string"},
                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                    "status": {"enum": ["pass", "fail"]},
                    "tags": {"type": "array", "minItems": 1},
                },
            },
        },
    },
    {
        "name": "arithmetic",
        "prompt": "Return ONLY the integer answer to 2 + 3.",
        "payload": {"task_type": "arithmetic", "expr": "2 + 3"},
    },
    {
        "name": "python_code",
        "prompt": "Return ONLY Python code defining add(a, b) as addition.",
        "payload": {"task_type": "python_code"},
    },
]


def main() -> int:
    OUT.mkdir(exist_ok=True)
    runtimes = [("ollama", "local", os.environ.get("ROUTEMAP_OLLAMA_MODEL", "llama3.1"))]
    if os.environ.get("OPENAI_API_KEY"):
        runtimes.append(("openai", "api_key", os.environ.get("ROUTEMAP_OPENAI_MODEL", "gpt-4.1-mini")))
    elif os.environ.get("ANTHROPIC_API_KEY"):
        runtimes.append(("anthropic", "api_key", os.environ.get("ROUTEMAP_ANTHROPIC_MODEL", "claude-3-5-haiku-latest")))

    rows: list[dict[str, Any]] = []
    for runtime, auth_mode, model_ref in runtimes:
        for spec in PROMPTS:
            try:
                output = model_fn(spec["prompt"], model_ref=model_ref, runtime=runtime, auth_mode=auth_mode, strict_model=True)
                payload = dict(spec["payload"])
                if spec["name"] == "arithmetic":
                    payload["claimed_answer"] = _first_int(str(output))
                elif spec["name"] == "python_code":
                    payload["code"] = str(output)
                    payload["raw"] = str(output)
                else:
                    payload["raw"] = str(output)
                decision = harness_check(payload)
                rows.append(
                    {
                        "runtime": runtime,
                        "model_ref": model_ref,
                        "prompt": spec["name"],
                        "status": "validated",
                        "verdict": decision.verdict,
                        "final_status": decision.final_status,
                    }
                )
            except (ModelAdapterError, ModelAdapterUnavailable, OSError) as exc:
                rows.append(
                    {
                        "runtime": runtime,
                        "model_ref": model_ref,
                        "prompt": spec["name"],
                        "status": "skipped",
                        "verdict": "",
                        "final_status": str(exc),
                    }
                )
    lines = [
        "# Harness Model Matrix",
        "",
        "| Runtime | Model | Prompt | Status | Verdict | Final status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(
        f"| {row['runtime']} | {row['model_ref']} | {row['prompt']} | {row['status']} | {row['verdict']} | {row['final_status']} |"
        for row in rows
    )
    (OUT / "MODEL_MATRIX.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT / 'MODEL_MATRIX.md'}")
    return 0


def _first_int(text: str) -> int:
    import re

    match = re.search(r"[+-]?\d+", text)
    return 0 if match is None else int(match.group(0))


if __name__ == "__main__":
    raise SystemExit(main())
