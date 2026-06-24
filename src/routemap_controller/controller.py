"""Unified RouteMap route decision policy loop."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha1
from typing import Any

import numpy as np

import routemap_digital
import routemap_embedding
import routemap_token
import routemap_validators

from .audit import make_record, validate_record
from .classify import classify


@dataclass(frozen=True)
class ActionPlan:
    task_type: str
    route_family: str
    action: str
    engine: str
    validator: str
    outcome: str
    compute_avoided: bool
    reason: str
    trace: str
    record: dict[str, Any]


def route_decide(input: Any, task: str | None = None, *, budget: str = "balanced", risk: str = "low", router_mode: str | None = None) -> ActionPlan:
    env = classify(input, task)
    if risk == "high":
        return _escalate(env.task_type, input, budget, risk, "risk=high forces FULL_COMPUTE_WITH_VALIDATOR", validator="full_compute_validator", outcome="FULL_COMPUTE_WITH_VALIDATOR")
    if budget == "full":
        return _escalate(env.task_type, input, budget, risk, "budget=full prefers full compute", validator="full_compute_validator", outcome="FULL_COMPUTE_WITH_VALIDATOR")
    if env.task_type == "arithmetic":
        return _arithmetic(input, env.reason, budget, risk)
    if env.task_type in {"json_schema", "python_code"}:
        return _sound_checker(input, env.task_type, env.reason, budget, risk)
    if env.task_type == "tool_call":
        return _tool_call(input, env.reason, budget, risk)
    if env.task_type == "long_context_qa":
        return _long_context_qa(input, env.reason, budget, risk, router_mode)
    if env.task_type == "retrieval":
        return _retrieval(input, env.reason, budget, risk)
    return _escalate("unknown", input, budget, risk, "unknown task has no safe guarded cheap path", validator="", outcome="FULL_COMPUTE")


def _arithmetic(input: Any, signal: str, budget: str, risk: str) -> ActionPlan:
    data = input if isinstance(input, dict) else {"expr": str(input), "claimed_answer": 0}
    expr = str(data.get("expr", ""))
    claimed = int(data.get("claimed_answer", 0))
    expr_spec, modulus = routemap_digital.parse_expression(expr)
    moduli = [modulus] if modulus is not None else data.get("moduli")
    result = routemap_digital.verify(expr_spec, claimed, moduli)
    outcome = str(result["verdict"])
    route_family = "digital_residue"
    reason = f"residue verifier returned {outcome}"
    trace = "\n".join(
        [
            f"classify: {signal} -> arithmetic",
            f"route: parse_expression({expr!r}) -> {expr_spec}",
            f"validator: routemap_digital.verify with moduli={moduli or 'default'}",
            f"decision: action=verify outcome={outcome}; no cheap prune, guarded verification only",
        ]
    )
    return _plan("arithmetic", route_family, "verify", "routemap_digital.verify", "residue", outcome, False, reason, trace, input, budget, risk, route_score=None)


def _sound_checker(input: Any, task_type: str, signal: str, budget: str, risk: str) -> ActionPlan:
    data = input if isinstance(input, dict) else {"raw": str(input)}
    raw = str(data.get("raw") or data.get("code") or input)
    spec = data.get("schema") if task_type == "json_schema" else data.get("spec")
    decision = routemap_validators.check_output(raw, task_type, spec=spec, object_id=_object_id(input), model="routemap_controller")
    outcome = str(decision.verdict)
    trace = "\n".join(
        [
            f"classify: {signal} -> {task_type}",
            f"route: sound-checker validator package",
            f"validator: {decision.checker or 'sound_checker'}",
            f"decision: action=verify outcome={outcome}; checker reason={decision.reason}",
        ]
    )
    return _plan(task_type, "sound_checker", "verify", "routemap_validators.check_output", decision.checker or "sound_checker", outcome, False, decision.reason, trace, input, budget, risk, route_score=None)


def _tool_call(input: Any, signal: str, budget: str, risk: str) -> ActionPlan:
    data = input if isinstance(input, dict) else {"raw": str(input)}
    raw = data.get("raw", data.get("tool_call", input))
    spec = {
        "schema": data.get("schema") or data.get("spec"),
        "allowed_tools": data.get("allowed_tools"),
    }
    decision = routemap_validators.check_output(raw, "tool_call", spec=spec, object_id=_object_id(input), model="routemap_controller")
    outcome = str(decision.verdict)
    trace = "\n".join(
        [
            f"classify: {signal} -> tool_call",
            "route: sound-checker tool-call firewall",
            f"validator: {decision.checker or 'tool_call_firewall'}",
            f"decision: action=verify outcome={outcome}; checker reason={decision.reason}",
        ]
    )
    return _plan("tool_call", "sound_checker", "verify", "routemap_validators.check_output", decision.checker or "tool_call_firewall", outcome, False, decision.reason, trace, input, budget, risk, route_score=None)


def _long_context_qa(input: Any, signal: str, budget: str, risk: str, router_mode: str | None = None) -> ActionPlan:
    data = input if isinstance(input, dict) else {"passage": str(input), "question": ""}
    passage = str(data.get("passage", ""))
    question = str(data.get("question", ""))
    # Use routemap_token's default router (currently 'element'); allow an override.
    kwargs = {"router_mode": router_mode} if router_mode else {}
    rows = routemap_token.route_passage(passage, question, **kwargs)
    keep = [row["token"] for row in rows if row["route_action"] == "keep"]
    cheap = [row["token"] for row in rows if row["route_action"] == "cheap"]
    if not keep:
        return _escalate("long_context_qa", input, budget, risk, "token route produced empty keep set", validator="answer_span_recall_guard", outcome="FULL_COMPUTE_WITH_VALIDATOR")
    reduction = len(cheap) / max(1, len(rows))
    mode_label = router_mode or "element"
    reason = f"{mode_label} route keeps {len(keep)} tokens and routes {reduction:.3f} cheap"
    trace = "\n".join(
        [
            f"classify: {signal} -> long_context_qa",
            f"route: routemap_token.route_passage (router_mode={mode_label})",
            "validator: answer_span_recall_guard",
            f"decision: action=cheap_path kept={len(keep)} cheap={len(cheap)} reduction={reduction:.3f}",
        ]
    )
    record_extra = {"kept_tokens": keep, "cheap_tokens": cheap}
    return _plan("long_context_qa", "token_importance", "cheap_path", "routemap_token", "answer_span_recall_guard", "accept", True, reason, trace, input, budget, risk, route_score=float(1.0 - reduction), extra=record_extra)


def _retrieval(input: Any, signal: str, budget: str, risk: str) -> ActionPlan:
    data = input if isinstance(input, dict) else {"query": str(input)}
    query = str(data.get("query", input))
    documents = data.get("documents") or data.get("corpus") or _default_documents()
    docs = [{"id": str(doc_id), "text": str(text)} for doc_id, text in _coerce_documents(documents)]
    matrix, ids, backend = routemap_embedding.build_vectors(docs + [{"id": "__query__", "text": query}], backend="tfidf")
    doc_matrix = matrix[:-1]
    query_vec = matrix[-1]
    fingerprint = routemap_embedding.RandomProjectionLSH(n_planes=12, n_bands=4, seed=7)
    index = routemap_embedding.EmbeddingRouteIndex(doc_matrix, ids[:-1] if ids[-1] == "__query__" else [doc["id"] for doc in docs], fingerprint)
    shortlist = index.route_search(query_vec, k=min(3, len(docs)), shortlist_mult=8)
    if not shortlist:
        return _escalate("retrieval", input, budget, risk, "fingerprint route returned empty shortlist", validator="rerank_guard", outcome="FULL_COMPUTE_WITH_VALIDATOR")
    reason = f"embedding route returned {len(shortlist)} reranked candidates with {backend} vectors"
    trace = "\n".join(
        [
            f"classify: {signal} -> retrieval",
            "route: routemap_embedding RandomProjectionLSH candidates",
            "validator: rerank_guard full cosine reranks the shortlist",
            f"decision: action=cheap_path shortlist={shortlist}",
        ]
    )
    return _plan("retrieval", "embedding_fingerprint", "cheap_path", "routemap_embedding.EmbeddingRouteIndex", "rerank_guard", "accept", True, reason, trace, input, budget, risk, route_score=float(len(shortlist) / max(1, len(docs))), extra={"shortlist": shortlist})


def _escalate(task_type: str, input: Any, budget: str, risk: str, reason: str, *, validator: str, outcome: str) -> ActionPlan:
    trace = "\n".join(
        [
            f"classify: {task_type}",
            "route: no guarded cheap path selected",
            f"decision: action=escalate outcome={outcome}; reason={reason}",
        ]
    )
    return _plan(task_type, "full_compute", "escalate", "controller", validator, outcome, False, reason, trace, input, budget, risk, route_score=None)


def _plan(
    task_type: str,
    route_family: str,
    action: str,
    engine: str,
    validator: str,
    outcome: str,
    compute_avoided: bool,
    reason: str,
    trace: str,
    input: Any,
    budget: str,
    risk: str,
    *,
    route_score: float | None,
    extra: dict[str, Any] | None = None,
) -> ActionPlan:
    record = make_record(
        task_type=task_type,
        object_id=_object_id(input),
        route_family=route_family,
        route_score=route_score,
        action=action,
        validator=validator,
        outcome=outcome,
        budget=budget,
        risk=risk,
        compute_avoided=compute_avoided,
        reason=reason,
    )
    if extra:
        record.update(extra)
    validate_record(record)
    return ActionPlan(task_type, route_family, action, engine, validator, outcome, compute_avoided, reason, trace, record)


def _object_id(input: Any) -> str:
    encoded = json.dumps(input, ensure_ascii=True, sort_keys=True, default=str)
    return sha1(encoded.encode("utf-8")).hexdigest()


def _tokenize(text: str) -> list[str]:
    import re

    return re.findall(r"https?://\S+|\[\d+\]|[A-Za-z]+(?:n't)?|\d+|[^\w\s]", text)


def _coerce_documents(documents: Any) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for index, item in enumerate(documents):
        if isinstance(item, dict):
            result.append((str(item.get("id", index)), str(item.get("text", ""))))
        elif isinstance(item, tuple):
            result.append((str(item[0]), str(item[1])))
        else:
            result.append((str(index), str(item)))
    return result


def _default_documents() -> list[tuple[str, str]]:
    return [
        ("route-token", "Token routing keeps answer-bearing spans and cheapens low information tokens."),
        ("route-digital", "Digital residue routes verify arithmetic claims with modular fingerprints."),
        ("route-embedding", "Embedding fingerprints retrieve a shortlist before full cosine reranking."),
    ]


__all__ = ["ActionPlan", "route_decide"]
