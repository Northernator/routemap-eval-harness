# Harness Audit Schema

`harness_decision_v1` is the canonical audit record emitted by `routemap_harness`.
It wraps existing lane audit records instead of replacing them.

## Canonical Shape

The top-level record is `schemas/harness_decision_v1.schema.json`.
Every emitted JSONL row must validate before it is written.

The lane-specific controller or validator audit record is embedded unchanged under:

```json
{
  "validator_record": {
    "schema_version": "route_decision_v1"
  }
}
```

or:

```json
{
  "validator_record": {
    "schema_version": "validator_audit_v1"
  }
}
```

## Crosswalk

| Existing field | Source schema | Harness field |
| --- | --- | --- |
| `route_id` | `route_decision_v1` | `validator_record.route_id` |
| `record_id` | `validator_audit_v1` | `validator_record.record_id` |
| `timestamp` | both | top-level `timestamp`; original preserved in `validator_record.timestamp` |
| `task_type` | both | top-level `task_type` |
| `route_family` | `route_decision_v1` | top-level `route_family`, normalized to harness enum |
| `action` | `route_decision_v1` | lane action preserved in `validator_record.action`; policy action stored in top-level `action` |
| `outcome` | `route_decision_v1` | top-level `verdict` when one-sided; full-compute outcomes map to `UNCHECKABLE` |
| `verdict` | `validator_audit_v1` | top-level `verdict` |
| `validator` / `checker` | both | top-level `validator`; original preserved in `validator_record` |
| `reason` | both | top-level `reason`; original preserved in `validator_record.reason` |
| `risk` / `budget` | `route_decision_v1` | preserved in `validator_record`; risk also informs `escalation_target` |
| `checks` | `validator_audit_v1` | `validator_record.checks` |

## Harness-Owned Fields

| Field | Meaning |
| --- | --- |
| `decision_id` | deterministic `{input_hash[:16]}-{repair_attempt}` |
| `input_hash` | SHA-256 of canonical input payload JSON |
| `repair_attempt` | zero for original decision, incremented for repair loop attempts |
| `action` | policy action: `accept`, `repair`, `retry`, `escalate`, `reject`, `full_compute` |
| `final_status` | policy result: `accepted`, `rejected`, `escalated`, `repaired`, `failed` |
| `latency_ms` | measured around controller `route_decide(...)` |
| `validator_record.escalation_target` | escalation policy target when applicable |

## Invariants

- `harness_decision_v1` is the only JSONL audit schema written by the harness.
- Existing lane records are embedded under `validator_record`.
- No accept/repair/prune decision may be emitted without a validator or explicit escalation target.
- `false_accepts` in gold summaries must remain `0`.
