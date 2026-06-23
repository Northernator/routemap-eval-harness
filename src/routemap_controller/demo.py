"""Demo suite for the unified route controller."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .audit import AuditLog
from .controller import ActionPlan, route_decide


def demo_inputs() -> list[tuple[str, Any, dict[str, str]]]:
    schema = {
        "type": "object",
        "required": ["id", "score", "status", "tags"],
        "properties": {
            "id": {"type": "string"},
            "score": {"type": "integer", "minimum": 0, "maximum": 100},
            "status": {"enum": ["pass", "fail"]},
            "tags": {"type": "array", "minItems": 1},
        },
        "additionalProperties": False,
    }
    return [
        ("wrong_arithmetic", {"expr": "2 + 3", "claimed_answer": 6}, {}),
        ("correct_arithmetic", {"expr": "2 + 3", "claimed_answer": 5}, {}),
        ("bad_json", {"raw": '{"id":"x","score":104,"status":"maybe","tags":[]}', "schema": schema}, {"task": "json_schema"}),
        ("valid_code", {"raw": "```python\nx = 1 + 1\nprint(x)\n```"}, {"task": "python_code"}),
        ("passage_question", {"passage": "The route memo says AI risk is reviewed before deployment. A background note is cheap filler.", "question": "What is reviewed before deployment?"}, {}),
        ("retrieval_query", {"query": "modular arithmetic route", "documents": [("a", "Token routes trim low information passages."), ("b", "Digital residue checks arithmetic claims."), ("c", "Embedding routes shortlist candidate passages.")]}, {}),
        ("unknown_high_risk", {"task_type": "unknown", "payload": "please do something unusual with no route signature"}, {"risk": "high"}),
    ]


def run_demo(out_dir: str | Path = "data/v1/digital_route/slice_15_controller") -> list[tuple[str, ActionPlan]]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "route_decisions.jsonl"
    if log_path.exists():
        log_path.unlink()
    log = AuditLog(log_path)
    plans: list[tuple[str, ActionPlan]] = []
    for name, payload, kwargs in demo_inputs():
        task = kwargs.get("task")
        risk = kwargs.get("risk", "low")
        plan = route_decide(payload, task=task, risk=risk)
        log.append(plan.record)
        plans.append((name, plan))
    (out / "demo_action_plans.md").write_text(action_plan_table(plans), encoding="utf-8")
    return plans


def action_plan_table(plans: list[tuple[str, ActionPlan]]) -> str:
    lines = [
        "# Unified Route Controller Demo",
        "",
        "| Task | task_type | route_family | action | validator | outcome | compute_avoided |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, plan in plans:
        lines.append(
            f"| {name} | {plan.task_type} | {plan.route_family} | {plan.action} | {plan.validator or '-'} | {plan.outcome} | {str(plan.compute_avoided).lower()} |"
        )
    lines.append("")
    lines.append("## Traces")
    for name, plan in plans:
        lines.extend(["", f"### {name}", "", "```text", plan.trace, "```"])
    return "\n".join(lines)


__all__ = ["action_plan_table", "demo_inputs", "run_demo"]
