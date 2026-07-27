# RouteMap — External Audit Checklist

A step-by-step path for an outside developer or researcher to reproduce the headline results cold.
Everything except the GPU matrix run and the live-`ollama` validator numbers reproduces offline with
Python + numpy.

## 0. Get the code
```
git clone https://github.com/Northernator/routemap-eval-harness.git
cd routemap-eval-harness
git switch --detach <release-tag-or-full-commit>
git rev-parse HEAD
git status --short
```
Use the tag or full commit named by the result being audited. Record the resolved full hash, and continue
only from a clean checkout. For current unreleased work, omit `git switch` and label the result unreleased.

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
python -m pytest -q
python scripts/check_acceptance.py
```
Expected: the full discovered suite and every acceptance check pass. Preserve complete output, including
skip reasons; do not treat an omitted or skipped lane as passed.

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
| Token routing | `python -m routemap_token run` | default element router: about 0.44 reduction at <1% recall loss on the named dataset; inspect current output for exact values |
| Embedding | `python -m routemap_embedding run` | recall/speed frontier; minimum_bar FAIL / strong_bar FAIL (characterized negative) |
| Controller | `python -m routemap_controller demo --out EVIDENCE/controller_demo` | 7 plans, 7 schema-valid audit rows, 1 escalation |
| Matrix core | `rm_test_matrix.py` | 9/9 (route/validate core; numpy) |
| **Blind (held-out)** | `python src/blind/score_blind_v1.py` | frozen-hash verified; arithmetic + structured-output catch 1.000 / FP 0.000 on fresh data; retrieval route recall@10 0.910; see `data/blind/v1/BLIND_RESULTS.md` |

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

## 7. Frozen blind benchmark (never tuned against)
A held-out suite is in `data/blind/v1/` (seed 20260623, independent ground truth, SHA-256 locked, scored once).
`python src/blind/score_blind_v1.py` verifies the hashes then scores. Results: `data/blind/v1/BLIND_RESULTS.md`.

## 8. Remaining honest gaps
- Cross-model coverage: the validator numbers were developed against a single local model; multi-model runs are pending.
- A human-annotated gold set for the semantic/extraction lane (the synthetic-gold leakage caveat from Phase 2 still applies; the blind extraction lane uses a deterministic baseline, LLM path ollama-gated).
- `NOT_RULED_OUT` is one-sided: it records that implemented checks found no hard failure, not that an output is correct.
- Dataset-level zero false accepts does not establish a universal zero-failure rate.
- Cached outputs reproduce scoring logic, not current behavior of a changing model or provider.
- Generated evidence under `EVIDENCE/` is ignored and must be paired with commit/environment metadata before publication.

## 9. Audit record to retain

Record the full commit hash, clean-status result, Python version, operating system, dependency versions,
commands run, skipped steps and reasons, generated report hashes, and any model/provider/hardware identifiers.
Use [`docs/PUBLIC_RELEASE_CHECKLIST.md`](docs/PUBLIC_RELEASE_CHECKLIST.md) for a maintainer release audit.
