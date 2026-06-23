from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import routemap_bench
import routemap_digital
import routemap_embedding
import routemap_token
import routemap_validators
from routemap_controller.audit import AuditLog, validate_record
from routemap_controller.classify import classify
from routemap_controller.controller import ActionPlan, route_decide


SCHEMA = {
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


def test_classify_maps_examples() -> None:
    assert classify({"expr": "2 + 3", "claimed_answer": 5}).task_type == "arithmetic"
    assert classify({"raw": '{"score":104}', "schema": SCHEMA}).task_type == "json_schema"
    assert classify({"raw": "```python\nprint(1)\n```"}).task_type == "python_code"
    assert classify({"passage": "The route memo says AI risk is reviewed.", "question": "What is reviewed?"}).task_type == "long_context_qa"
    assert classify({"query": "modular arithmetic", "documents": ["Digital residues verify claims."]}).task_type == "retrieval"
    assert classify("This input is deliberately verbose and lacks a question mark or structured route signature for known handlers.").task_type == "unknown"
    assert classify("anything", task_hint="retrieval").task_type == "retrieval"


def test_dispatch_arithmetic_wrong_and_correct() -> None:
    wrong = route_decide({"expr": "2 + 3", "claimed_answer": 6})
    correct = route_decide({"expr": "2 + 3", "claimed_answer": 5})
    assert wrong.action == "verify"
    assert wrong.outcome == routemap_digital.RULED_OUT_WRONG
    assert correct.outcome == routemap_digital.NOT_RULED_OUT
    _assert_guarded_and_valid(wrong)
    _assert_guarded_and_valid(correct)


def test_dispatch_json_schema_violation() -> None:
    plan = route_decide({"raw": '{"id":"x","score":104,"status":"maybe","tags":[]}', "schema": SCHEMA}, task="json_schema")
    assert plan.action == "verify"
    assert plan.outcome == routemap_validators.Verdict.RULED_OUT_WRONG
    assert plan.validator
    _assert_guarded_and_valid(plan)


def test_long_context_and_retrieval_cheap_paths_are_guarded() -> None:
    qa = route_decide(
        {
            "passage": "The route memo says AI risk is reviewed before deployment. A background note is cheap filler.",
            "question": "What is reviewed before deployment?",
        }
    )
    assert qa.action == "cheap_path"
    assert qa.validator == "answer_span_recall_guard"
    assert qa.record["kept_tokens"]
    retrieval = route_decide(
        {
            "query": "digital residue arithmetic",
            "documents": [
                ("a", "Token routes trim low information passages."),
                ("b", "Digital residue checks arithmetic claims."),
                ("c", "Embedding routes shortlist candidates."),
            ],
        }
    )
    assert retrieval.action == "cheap_path"
    assert retrieval.validator == "rerank_guard"
    assert retrieval.record["shortlist"]
    _assert_guarded_and_valid(qa)
    _assert_guarded_and_valid(retrieval)


def test_escalation_unknown_and_high_risk() -> None:
    unknown = route_decide("This input is deliberately verbose and lacks a question mark or structured route signature for known handlers.")
    high = route_decide({"query": "digital residue", "documents": ["Digital residue checks arithmetic claims."]}, risk="high")
    assert unknown.action == "escalate"
    assert unknown.outcome == "FULL_COMPUTE"
    assert high.action == "escalate"
    assert high.outcome == "FULL_COMPUTE_WITH_VALIDATOR"
    validate_record(unknown.record)
    validate_record(high.record)


def test_invariant_no_unguarded_verify_or_cheap_action() -> None:
    plans = [
        route_decide({"expr": "2 + 3", "claimed_answer": 6}),
        route_decide({"raw": '{"id":"x","score":104,"status":"maybe","tags":[]}', "schema": SCHEMA}, task="json_schema"),
        route_decide({"passage": "Route tokens keep the answer.", "question": "What keeps the answer?"}),
        route_decide({"query": "route token", "documents": ["Route tokens keep answers.", "Digital residues verify answers."]}),
    ]
    for plan in plans:
        assert plan.trace.strip()
        validate_record(plan.record)
        if plan.action in {"cheap_path", "verify"}:
            assert plan.validator


def test_determinism_excluding_timestamp_and_route_id() -> None:
    payload = {"expr": "2 + 3", "claimed_answer": 6}
    left = route_decide(payload)
    right = route_decide(payload)
    assert (left.action, left.outcome) == (right.action, right.outcome)
    assert _stable_record(left.record) == _stable_record(right.record)


def test_audit_log_append_jsonl(tmp_path: Path) -> None:
    plan = route_decide({"expr": "2 + 3", "claimed_answer": 6})
    path = tmp_path / "audit.jsonl"
    AuditLog(path).append(plan.record)
    row = json.loads(path.read_text(encoding="utf-8").strip())
    validate_record(row)
    assert row["schema_version"] == "route_decision_v1"


def test_all_wrapped_packages_import_and_are_reachable() -> None:
    assert routemap_validators.check_output
    assert routemap_digital.verify
    assert routemap_token.route_action
    assert routemap_embedding.EmbeddingRouteIndex
    assert hasattr(routemap_bench, "__all__") or routemap_bench is not None
    assert route_decide({"expr": "2 + 3", "claimed_answer": 5}).engine == "routemap_digital.verify"
    assert route_decide({"raw": '{"id":"x","score":104,"status":"maybe","tags":[]}', "schema": SCHEMA}, task="json_schema").engine == "routemap_validators.check_output"
    assert route_decide({"passage": "Route tokens keep the answer.", "question": "What keeps the answer?"}).engine == "routemap_token"
    assert route_decide({"query": "route token", "documents": ["Route tokens keep answers.", "Digital residues verify answers."]}).engine == "routemap_embedding.EmbeddingRouteIndex"


def _assert_guarded_and_valid(plan: ActionPlan) -> None:
    assert plan.trace.strip()
    validate_record(plan.record)
    if plan.action in {"cheap_path", "verify"}:
        assert plan.validator


def _stable_record(record: dict[str, object]) -> dict[str, object]:
    stable = dict(record)
    stable.pop("timestamp", None)
    stable.pop("route_id", None)
    return stable
