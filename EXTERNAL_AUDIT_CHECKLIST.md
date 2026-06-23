# RouteMap — External Audit Checklist

A step-by-step path for an outside developer or researcher to reproduce the headline results cold.
Everything except the GPU matrix run and the live-`ollama` validator numbers reproduces offline with
Python + numpy.

## 0. Get the code
```
git clone https://github.com/Northernator/routemap-eval-harness
cd routemap-eval-harness
git rev-parse HEAD     # expect d3b773a74a40b0470f592afa506c61a1a6b4dd95
```

## 1. Environment
- Python 3.11 (3.10 also works).
```
pip install -r requirements-dev.txt     # numpy + pytest (+ pandas/matplotlib for the Phase 1-2 harness)
```
- Matrix layer only (optional, GPU): `pip install -r requirements-matrix.txt` plus a torch build for your
  GPU — see `src/routemap_matrix/HANDOFF.md`.

## 2. Run the test suites (expect all PASS)
```
# set src on the path first:  PowerShell: $env:PYTHONPATH='src'   bash: export PYTHONPATH=src
python -m pytest rv_test_validator_package.py rd_test_digital_engine.py rb_test_bench.py rt_test_token.py re_test_embedding.py rc_test_controller.py rm_test_matrix.py -q
```
Expected: seven suites pass (validators, digital, bench, token, embedding, controller, matrix-core).

## 3. Run the evidence runner (one command)
```
python run_evidence.py
```
Writes `EVIDENCE/RESULTS.md` with pass/fail and captured log tails for the seven suites plus the five offline
benchmarks/demos. The matrix self-check is skipped unless `torch` is installed.

## 4. Expected headline artifacts and numbers
| Lane | Reproduce | Expect |
| --- | --- | --- |
| Validators | `python -m routemap_validators.run_regression` | status PASS; arith/json extracted rule-out 1.000 / 0.600; FP 0.000 |
| Digital engine | `rd_test_digital_engine.py`; `python -m routemap_digital check "7^1000000 mod 9"` | 8/8 tests; prints `7` |
| Arithmetic bench | `python -m routemap_bench run` | catch 1.000, false-reject 0.000, oracle_verifier_agreement 1.000 |
| Token routing | `python -m routemap_token run` | dataset v1_full_extraction_gold (99); ~0.34 reduction at <1% recall loss; min PASS / strong FAIL |
| Embedding | `python -m routemap_embedding run` | recall/speed frontier; minimum_bar FAIL / strong_bar FAIL (characterized negative) |
| Controller | `python -m routemap_controller demo --out EVIDENCE/controller_demo` | 7 plans, 7 schema-valid audit rows, 1 escalation |
| Matrix core | `rm_test_matrix.py` | 9/9 (route/validate core; numpy) |

## 5. Known environment-gated (not in the offline run)
- **Matrix GPU result** (peak VRAM / long-context): needs an Ampere-class GPU. See `src/routemap_matrix/HANDOFF.md`.
  On the development GPU (GTX 980M, Maxwell) this is a characterized hardware-wall negative, not a win.
- **Validator N=30 live numbers**: need a local `ollama` model; the cached-corpus regression in step 4 reproduces
  the FP 0.000 / JSON 0.600 figures offline.

## 6. Audit schemas, records, claims
- Audit schemas: `configs/validator_audit_schema_v1.json` (`validator_audit_v1`); `src/routemap_controller/audit.py` (`route_decision_v1`).
- Dated record of every result: `data/v1/digital_route/records/PHASE3_INDEX.md` + `SLICE_01..16_*.md`.
- Frozen seed: `7` (deterministic — same seed gives byte-identical task files).
- No-claim list: `EVIDENCE_PACK.md` section 8 and the report's "What is not claimed".

## 7. Not yet present (honest gaps)
- A frozen external blind benchmark (`data/blind/`) the system was never tuned against — the next credibility step.
- Cross-model coverage: the validator numbers were developed against a single local model; multi-model runs are pending.
