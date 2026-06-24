"""Minimal bounded agent loop over firewalled in-process tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping

from routemap_harness import audit_store
from routemap_harness.core import HarnessDecision, harness_check
from routemap_validators.verdicts import NOT_RULED_OUT, RULED_OUT_WRONG


ToolFn = Callable[..., Any]


def run_agent(
    goal: str,
    tools: Mapping[str, Any],
    model_fn: Callable[[str], Any],
    *,
    max_steps: int = 1,
    audit_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run at most one firewalled tool step and return a trace."""
    step_limit = max(0, min(int(max_steps), 1))
    steps: list[dict[str, Any]] = []
    audit_ids: list[str] = []
    if step_limit == 0:
        return {"steps": steps, "final": "escalated: max_steps exhausted", "audit_ids": audit_ids}

    plan = _model_text(model_fn(_plan_prompt(goal)))
    raw_call = _model_text(model_fn(_tool_prompt(goal, plan, tools)))
    step: dict[str, Any] = {"step": 1, "plan": plan, "tool_call": raw_call}
    call_decision = _check_tool_call(raw_call, tools)
    audit_ids.append(_append(call_decision, audit_path))
    step["tool_firewall"] = call_decision.to_dict()

    if call_decision.verdict == RULED_OUT_WRONG:
        repaired_call = _model_text(model_fn(_repair_prompt(goal, raw_call, call_decision)))
        step["repair_tool_call"] = repaired_call
        repaired_decision = _check_tool_call(repaired_call, tools)
        audit_ids.append(_append(repaired_decision, audit_path))
        step["repair_firewall"] = repaired_decision.to_dict()
        if repaired_decision.verdict != NOT_RULED_OUT:
            step["final_status"] = "escalated"
            steps.append(step)
            return {"steps": steps, "final": "escalated: tool call blocked", "audit_ids": audit_ids}
        raw_call = repaired_call
        call_decision = repaired_decision
    elif call_decision.verdict != NOT_RULED_OUT:
        step["final_status"] = "escalated"
        steps.append(step)
        return {"steps": steps, "final": "escalated: tool call uncheckable", "audit_ids": audit_ids}

    parsed = _parse_call(raw_call)
    descriptor = _tool_descriptor(tools[parsed["name"]])
    output = _execute_tool(descriptor["fn"], parsed["arguments"])
    step["tool_output"] = output
    output_decision = _check_output(output, descriptor)
    audit_ids.append(_append(output_decision, audit_path))
    step["output_check"] = output_decision.to_dict()
    if output_decision.verdict != NOT_RULED_OUT:
        step["final_status"] = "escalated"
        steps.append(step)
        return {"steps": steps, "final": "escalated: tool output blocked", "audit_ids": audit_ids}

    final = _model_text(model_fn(_final_prompt(goal, plan, raw_call, output)))
    step["final_status"] = "completed"
    steps.append(step)
    return {"steps": steps, "final": final, "audit_ids": audit_ids}


def _check_tool_call(raw_call: str, tools: Mapping[str, Any]) -> HarnessDecision:
    name = _safe_tool_name(raw_call)
    descriptor = _tool_descriptor(tools.get(name)) if name in tools else {}
    spec = {"allowed_tools": sorted(tools), "schema": descriptor.get("schema") or {"type": "object"}}
    return harness_check({"task_type": "tool_call", "raw": raw_call, "allowed_tools": spec["allowed_tools"], "schema": spec["schema"]})


def _check_output(output: Any, descriptor: Mapping[str, Any]) -> HarnessDecision:
    if descriptor.get("source") is not None:
        return harness_check(
            {
                "task_type": "grounded_qa",
                "raw": str(output),
                "answer": str(output),
                "source": descriptor["source"],
            }
        )
    schema = descriptor.get("output_schema") or _schema_for_output(output)
    return harness_check({"task_type": "json_schema", "raw": json.dumps(output, ensure_ascii=True), "schema": schema})


def _append(decision: HarnessDecision, audit_path: str | Path | None) -> str:
    audit_store.append(decision, audit_path or audit_store.DEFAULT_AUDIT)
    return decision.decision_id


def _parse_call(raw_call: str) -> dict[str, Any]:
    data = json.loads(raw_call)
    if isinstance(data, Mapping) and "tool_call" in data:
        data = data["tool_call"]
    if not isinstance(data, Mapping):
        raise ValueError("tool call must be an object")
    raw_args = data.get("arguments", data.get("args"))
    arguments = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    if not isinstance(arguments, dict):
        raise ValueError("tool call arguments must be an object")
    return {"name": str(data.get("name", data.get("tool"))), "arguments": arguments}


def _safe_tool_name(raw_call: str) -> str:
    try:
        return _parse_call(raw_call)["name"]
    except (json.JSONDecodeError, TypeError, ValueError):
        return ""


def _tool_descriptor(tool: Any) -> dict[str, Any]:
    if isinstance(tool, Mapping):
        fn = tool.get("fn")
        if not callable(fn):
            return {}
        return {
            "fn": fn,
            "schema": tool.get("schema"),
            "output_schema": tool.get("output_schema"),
            "source": tool.get("source"),
        }
    if callable(tool):
        return {"fn": tool, "schema": {"type": "object"}, "output_schema": None, "source": None}
    return {}


def _execute_tool(fn: ToolFn, arguments: Mapping[str, Any]) -> Any:
    try:
        return fn(**dict(arguments))
    except TypeError:
        return fn(dict(arguments))


def _schema_for_output(output: Any) -> dict[str, Any]:
    if isinstance(output, bool):
        return {"type": "boolean"}
    if isinstance(output, int):
        return {"type": "integer"}
    if isinstance(output, float):
        return {"type": "number"}
    if isinstance(output, list):
        return {"type": "array"}
    if isinstance(output, dict):
        return {"type": "object"}
    return {"type": "string"}


def _model_text(value: Any) -> str:
    return str(value)


def _plan_prompt(goal: str) -> str:
    return f"Plan one bounded tool step for this goal:\n{goal}"


def _tool_prompt(goal: str, plan: str, tools: Mapping[str, Any]) -> str:
    return (
        "Return exactly one JSON tool call with name and arguments. "
        f"Allowed tools: {', '.join(sorted(tools))}.\nGoal: {goal}\nPlan: {plan}"
    )


def _repair_prompt(goal: str, raw_call: str, decision: HarnessDecision) -> str:
    return (
        "Repair this blocked tool call as one allowed JSON tool call. "
        f"Goal: {goal}\nBlocked call: {raw_call}\nReason: {decision.reason}"
    )


def _final_prompt(goal: str, plan: str, raw_call: str, output: Any) -> str:
    return f"Give final answer.\nGoal: {goal}\nPlan: {plan}\nTool call: {raw_call}\nTool output: {output}"


__all__ = ["run_agent"]
