# RouteMap Validators

`routemap_validators` is the named core validator package for the Digital RouteMap checker layer. It wraps the existing Phase 3 modules; it does not copy checker math or change checker behavior.

## Public API

```python
from routemap_validators import (
    AUDIT_SCHEMA_VERSION,
    AuditLog,
    CoverageReport,
    Verdict,
    check_output,
    default_router,
    to_record,
    validate_record,
)
```

`check_output(raw, task_type, spec=None, object_id=None, model=None)` extracts the checkable payload before routing it to the existing checker framework.

Supported task types:

| task_type | Extraction | Existing checker |
| --- | --- | --- |
| `arithmetic` | `extract_integer` | `ArithmeticChecker` / `dr_verifier_v1.verify` |
| `python_code` | `extract_code` | `PythonCodeChecker` |
| `json_schema` | `extract_json` | `JsonSchemaChecker` |

Extraction or generation failure returns `UNCHECKABLE`. It never returns `RULED_OUT_WRONG`.

## Verdict Contract

`Verdict` exposes the canonical three-verdict set:

| Verdict | Meaning |
| --- | --- |
| `RULED_OUT_WRONG` | A sound checker found a concrete violation. |
| `NOT_RULED_OUT` | No applicable checker ruled out the output; correctness is not proven. |
| `UNCHECKABLE` | Extraction, generation, or required validator input failed before a sound check could run. |

`Verdict.ALL` is the frozen set of all three strings.

## Audit Schema

Locked schema path: `configs/validator_audit_schema_v1.json`

Schema version: `validator_audit_v1`

Required audit fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `schema_version` | const string | `validator_audit_v1` |
| `record_id` | string | Stable record identifier. |
| `timestamp` | ISO-8601 string | Emission time. |
| `task_type` | string | Validator task type. |
| `object_id` | string/null | Optional source object id. |
| `model` | string/null | Optional model name. |
| `raw_sha1` | string | SHA-1 of raw model output. |
| `extraction_ok` | boolean | Whether extraction produced checkable content. |
| `extraction_note` | string | Extraction boundary note. |
| `extracted_repr` | string/null | Normalized extracted content. |
| `checker` | string/null | Checker selected for the decision. |
| `verdict` | enum | One of the three canonical verdicts. |
| `reason` | string | Decision reason. |
| `coverage_note` | string/null | Checker coverage text. |
| `checks` | array | Per-checker verdict rows. |
| `spec_hash` | string/null | SHA-1 of canonical JSON spec. |

Unknown optional keys are ignored by `validate_record()`. Reserved future controller fields are `route_family`, `route_score`, and `action`; the package does not emit them now.

## Phase 7 Mapping

Per Intelligence Architecture section 7.1 core schema:

| Audit field | Phase 7 field |
| --- | --- |
| `checker` | `validator` |
| `verdict` | `outcome` |
| `object_id` | `object_id` |
| `task_type` | `task_type` |

## Regression

Offline runner:

```powershell
$env:PYTHONPATH='src'
python -m routemap_validators.run_regression
```

It re-scores the cached Slice 5 corpus and checks cached Slice 2 hardening results. It does not call Ollama or regenerate corpora.
