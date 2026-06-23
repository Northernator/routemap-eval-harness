# Phase 7 Slice 15 - Unified Route Controller

Date: 2026-06-23

## Purpose

Build `routemap_controller`, a unified auditable control loop over the existing RouteMap architecture. The contribution is orchestration and audit, not new routing math: classify the task, select the existing route family, attach a validator, and escalate when no safe guarded cheap path exists.

Every cheap decision is guarded or escalated. There is no silent prune.

## Files Added

- `src/routemap_controller/__init__.py`
- `src/routemap_controller/__main__.py`
- `src/routemap_controller/README.md`
- `src/routemap_controller/audit.py`
- `src/routemap_controller/classify.py`
- `src/routemap_controller/controller.py`
- `src/routemap_controller/demo.py`
- `src/routemap_controller/run_controller_demo.py`
- `rc_test_controller.py`

## Packages Composed

| Task type | Route family | Wrapped package/API | Validator |
| --- | --- | --- | --- |
| arithmetic | digital_residue | `routemap_digital.parse_expression`, `routemap_digital.verify` | residue |
| json_schema | sound_checker | `routemap_validators.check_output` | sound checker |
| python_code | sound_checker | `routemap_validators.check_output` | sound checker |
| long_context_qa | token_importance | `routemap_token` prior/context/policy | answer_span_recall_guard |
| retrieval | embedding_fingerprint | `routemap_embedding.EmbeddingRouteIndex.route_search` | rerank_guard |
| unknown/high-risk/full-budget | full_compute | controller escalation | full_compute_validator when applicable |

## ActionPlan Contract

`route_decide(input, task=None, *, budget="balanced", risk="low") -> ActionPlan`

Frozen fields: `task_type`, `route_family`, `action`, `engine`, `validator`, `outcome`, `compute_avoided`, `reason`, `trace`, `record`.

Invariant: `action in {"cheap_path", "verify"}` requires a non-empty `validator`.

## Audit Schema

Schema version: `route_decision_v1`

Required fields: `schema_version`, `route_id`, `timestamp`, `task_type`, `object_id`, `route_family`, `route_score`, `action`, `validator`, `outcome`, `budget`, `risk`, `compute_avoided`, `reason`.

`validate_record()` is hand-rolled and allows unknown optional keys for forward compatibility. `AuditLog.append()` writes JSONL.

## Demo Suite

Outputs:

- `data/v1/digital_route/slice_15_controller/demo_action_plans.md`
- `data/v1/digital_route/slice_15_controller/route_decisions.jsonl`

| Task | task_type | route_family | action | validator | outcome | compute_avoided |
| --- | --- | --- | --- | --- | --- | --- |
| wrong_arithmetic | arithmetic | digital_residue | verify | residue | RULED_OUT_WRONG | false |
| correct_arithmetic | arithmetic | digital_residue | verify | residue | NOT_RULED_OUT | false |
| bad_json | json_schema | sound_checker | verify | json_schema_constraints_v1 | RULED_OUT_WRONG | false |
| valid_code | python_code | sound_checker | verify | python_code_parse_v1 | NOT_RULED_OUT | false |
| passage_question | long_context_qa | token_importance | cheap_path | answer_span_recall_guard | accept | true |
| retrieval_query | retrieval | embedding_fingerprint | cheap_path | rerank_guard | accept | true |
| unknown_high_risk | unknown | full_compute | escalate | full_compute_validator | FULL_COMPUTE_WITH_VALIDATOR | false |

Audit log line count: 7.

## Example Trace

Arithmetic verify:

```text
classify: expression plus claimed_answer -> arithmetic
route: parse_expression('2 + 3') -> {'family': 'bigsum', 'values': [2, 3]}
validator: routemap_digital.verify with moduli=default
decision: action=verify outcome=RULED_OUT_WRONG; no cheap prune, guarded verification only
```

Escalation:

```text
classify: unknown
route: no guarded cheap path selected
decision: action=escalate outcome=FULL_COMPUTE_WITH_VALIDATOR; reason=risk=high forces FULL_COMPUTE_WITH_VALIDATOR
```

## Honest Framing

This slice unifies control and audit. It does not claim new verifier strength, new embedding math, or new token-routing guarantees. The controller delegates to existing route families, records the decision, and makes validator attachment explicit. Unknown, high-risk, full-budget, or unguarded paths escalate.

## Verification

```text
python -B -m pytest rc_test_controller.py -q
9 passed

PYTHONPATH=src python -B -m routemap_controller demo --out data/v1/digital_route/slice_15_controller
7 action plans
7 route_decisions.jsonl rows
```
