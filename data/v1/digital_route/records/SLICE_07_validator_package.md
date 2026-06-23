# Phase 3 Slice 7 - Validator Package

Date: 2026-06-23

## Purpose

Promote the Phase 3 validator layer into a named importable package without changing checker math, extraction rules, or routing behavior.

## Files created

- `src/routemap_validators/__init__.py`
- `src/routemap_validators/verdicts.py`
- `src/routemap_validators/checkers.py`
- `src/routemap_validators/extraction.py`
- `src/routemap_validators/pipeline.py`
- `src/routemap_validators/audit.py`
- `src/routemap_validators/run_regression.py`
- `src/routemap_validators/README.md`
- `configs/validator_audit_schema_v1.json`
- `rv_test_validator_package.py`
- `data/v1/digital_route/slice_07_validator_package/example_audit.jsonl`
- `data/v1/digital_route/records/SLICE_07_validator_package.md`

## Commands run

- `$env:PYTHONPATH='src'; python -m py_compile src/routemap_validators/__init__.py src/routemap_validators/verdicts.py src/routemap_validators/checkers.py src/routemap_validators/extraction.py src/routemap_validators/pipeline.py src/routemap_validators/audit.py src/routemap_validators/run_regression.py`
- `$env:PYTHONPATH='src'; python -m pytest rv_test_validator_package.py -q`
- `$env:PYTHONPATH='src'; python -m routemap_validators.run_regression`
- `git diff --check -- src/routemap_validators configs/validator_audit_schema_v1.json rv_test_validator_package.py data/v1/digital_route/records/SLICE_07_validator_package.md data/v1/digital_route/slice_07_validator_package`

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

`check_output(raw, task_type, spec=None, object_id=None, model=None)` lifts the existing Slice 4/5 integrated behavior into the package:

| task_type | Extraction boundary | Existing checker |
| --- | --- | --- |
| `arithmetic` | `extract_integer` | `ArithmeticChecker` |
| `python_code` | `extract_code` | `PythonCodeChecker` |
| `json_schema` | `extract_json` | `JsonSchemaChecker` |

Extraction failure is `UNCHECKABLE`, never `RULED_OUT_WRONG`.

## Locked Audit Schema

Schema path: `configs/validator_audit_schema_v1.json`

Schema version: `validator_audit_v1`

| Field | Required | Type | Notes |
| --- | --- | --- | --- |
| `schema_version` | yes | const string | `validator_audit_v1` |
| `record_id` | yes | string | Stable audit id |
| `timestamp` | yes | ISO-8601 string | Emission time |
| `task_type` | yes | string | Validator task type |
| `object_id` | yes | string/null | Source object id |
| `model` | yes | string/null | Model name |
| `raw_sha1` | yes | string | SHA-1 of raw output |
| `extraction_ok` | yes | bool | Extraction success |
| `extraction_note` | yes | string | Extraction note |
| `extracted_repr` | yes | string/null | Normalized extracted payload |
| `checker` | yes | string/null | Selected checker |
| `verdict` | yes | enum | `RULED_OUT_WRONG`, `NOT_RULED_OUT`, `UNCHECKABLE` |
| `reason` | yes | string | Decision reason |
| `coverage_note` | yes | string/null | Checker coverage note |
| `checks` | yes | array | `{checker, verdict, reason, coverage_note}` rows |
| `spec_hash` | yes | string/null | SHA-1 of canonical spec JSON |

Unknown optional keys are ignored. Reserved future controller fields are `route_family`, `route_score`, and `action`; they are documented but not emitted.

## Phase 7 Field Mapping

| Validator audit field | Intelligence Architecture section 7.1 field |
| --- | --- |
| `checker` | `validator` |
| `verdict` | `outcome` |
| `object_id` | `object_id` |
| `task_type` | `task_type` |

## Regression Results

Expected and actual values are from cached offline corpora only.

| Domain | Expected rule-out | Actual rule-out | Expected UNCHECKABLE | Actual UNCHECKABLE | Expected FP | Actual FP | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| arithmetic | 1.000 | 1.000 | 0.133 | 0.133 | 0.000 | 0.000 | PASS |
| python_code | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | PASS |
| json_schema | 0.600 | 0.600 | 0.000 | 0.000 | 0.000 | 0.000 | PASS |

Additional acceptance checks:

| Check | Result |
| --- | --- |
| Slice 2 standard arithmetic catch rate | 1.000 |
| Slice 2 false-positive rate | 0.000 |
| Exact combined-modulus arithmetic error | `NOT_RULED_OUT` |
| `pass_but_wrong` where arithmetic truth is known | 0 |
| Existing `dr_*` and `evaluate_*` modules import | PASS |
| Decision audit records validate | PASS |

## Index Note

`PHASE3_INDEX.md` was intentionally left unchanged to preserve the new-files-only constraint for this packaging step. Suggested index row:

`- 2026-06-23 - Slice 07: validator package and locked audit schema; Slice 5 regression exact, hardening FP 0.000.`
