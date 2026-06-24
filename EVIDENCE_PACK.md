# RouteMap Evidence Pack

Everything needed for a third party to reproduce the headline numbers cold. The goal is to move from
"the build reports it works" to "anyone can run it and get the same tables."

## 1. Repo state
- Repository: https://github.com/Northernator/routemap-eval-harness
- Reproduce against commit **`d3b773a`** ("Initial commit: RouteMap - route-and-validate control layer for LLMs").
  Full hash: `d3b773a74a40b0470f592afa506c61a1a6b4dd95`.
- Verify your checkout with `git rev-parse HEAD`. Run all commands from the repo root (`src/` and
  `run_evidence.py` are at the top level), with `src` on `PYTHONPATH`.

## 2. Environment
- Python 3.11 (verified on 3.10/3.11). `numpy` only for six of the seven packages.
- Matrix layer (`routemap_matrix`) only: `torch` + `transformers>=4.44` (+ `accelerate`). The GPU run needs
  Ampere-class hardware; the Maxwell GTX 980M result is a characterized negative (see `src/routemap_matrix/HANDOFF.md`).
- Run everything with `src` on the path: from the harness root, `set PYTHONPATH=src` (PowerShell: `$env:PYTHONPATH='src'`).

## 3. Install
```
# core (validators, digital, bench, token, embedding, controller) + offline benchmarks:
pip install -r requirements-dev.txt
# matrix layer only (optional):
pip install -r requirements-matrix.txt   # + a torch build for your GPU (Maxwell: torch 2.5.1+cu124)
```

## 4. One command to reproduce
```
cd routemap_eval_harness/routemap_eval_harness
python run_evidence.py
```
Runs the seven test suites and the offline benchmarks, then writes `EVIDENCE/RESULTS.md` with pass/fail and
captured log tails. Offline steps need only Python + numpy; the matrix self-check needs torch; the live-ollama
and GPU numbers are environment-gated (noted in the output).

## 5. Headline results (verified) and how each reproduces
| Lane | Verified headline | Reproduce |
| --- | --- | --- |
| Sound validators | Practical false-positive rate 0.000 across arithmetic/code/JSON on real wrapped output (N=30); JSON-schema: 60% of outputs violated their schema, all caught; repair 0.60 -> 0.33; zero pass-but-wrong | `rv_test_validator_package.py`; `python -m routemap_validators.run_regression`; scale numbers in `data/v1/digital_route/slice_05_scale/` + `slice_06_repair/` (ollama-gated) |
| Digital engine | 8/8 tests; pow/fib-via-cycle == Python exact over 3,000 random ~1e8 exponents; CRT round-trip exact below M, ambiguous above; off-by-M -> NOT_RULED_OUT (sound) | `rd_test_digital_engine.py`; `python -m routemap_digital check "7^1000000 mod 9"` |
| HugeArithmeticRouteBench | catch 1.000, false-reject 0.000, oracle-verifier agreement 1.000 (75/75), 0 silent misses, 0 false-correct; ground truth independent of the engine (0/73 mismatches) | `rb_test_bench.py`; `python -m routemap_bench run` |
| Token-importance routing | **default router = element** (~44% reduction @<1% loss; token baseline ~34% via `--router token`). Element validated on synthetic-blind + 2 real human-reviewed held-out sets at 0 recall loss with frozen weights (sha256 c7f0cf9e); no-leak | `rt_test_token.py`; `rt_test_elements.py`; `python -m routemap_token run --router all`; `python -m routemap_elements.blind_validate` |
| Embedding fingerprints | Recall/speed frontier on a 20k-vector synthetic index; no naive fingerprint clears recall@10>0.95 at >=2x (characterized negative, full curve checked) | `re_test_embedding.py`; `python -m routemap_embedding run` |
| Unified controller | 9/9 tests; route_decide dispatch correct per task type; no-silent-prune invariant holds; every decision a schema-valid `route_decision_v1` record; demo = 7 plans, 1 escalation | `rc_test_controller.py`; `python -m routemap_controller demo` |
| Harness core + gold | Canonical `harness_decision_v1` wrapper over the controller; frozen per-lane gold set verifies SHA-256 before scoring; zero false accepts and sound-lane false-positive rate 0.000; CLI/API/demo emit schema-valid decision + audit JSONL | `tests/test_harness_core.py`; `tests/test_harness_gold.py`; `python -m routemap_harness check --task json_schema --input examples/json_tool_call/harness_cli_payload.json --audit EVIDENCE/harness_cli_audit.jsonl`; `python scripts/run_demo_pack.py`; `python scripts/check_acceptance.py` |
| Local web UI | FastAPI serves an offline single-file Check/Chat UI with model availability, optional token-element input compression, chat-run audit, and exact arithmetic correction display | `tests/test_web.py`; `PYTHONPATH=src uvicorn routemap_harness.api:app` |
| Matrix / KV routing | route/validate core 9/9 (CPU); GPU peak-VRAM/quality is hardware-gated (research-only) | `rm_test_matrix.py`; `python -m routemap_matrix selfcheck`; GPU run per `src/routemap_matrix/HANDOFF.md` |
| Blind held-out suite | on fresh data never tuned against: arithmetic + structured-output catch 1.000 / FP 0.000; retrieval route recall@10 0.910; extraction 0.667 (baseline) | `python src/blind/score_blind_v1.py` (verifies SHA-256, scores once); `data/blind/v1/BLIND_RESULTS.md` |

## 6. Datasets and frozen seeds
- Benchmark seed: **7** (all generators; deterministic — same seed gives byte-identical task files).
- Synthetic: HugeArithmeticRouteBench tasks, TokenRouteQA constructed fallback, embedding distractors, needle-in-haystack — all seeded.
- Real gold: `data/v1/gold/v1_full_extraction_gold_v1.csv` (99 segments), `data/gold/*.csv`, `data/v1/gold/v1_qa_targets.csv`.
- Harness acceptance gold: `data/harness_gold/cases.jsonl`, locked by `data/harness_gold/SHA256SUMS`, one known-correct and one known-wrong fixture per lane.
- Harness demos: `examples/json_tool_call/`, `examples/arithmetic/`, `examples/extraction/`, `examples/long_context/`; `scripts/run_demo_pack.py` summarizes these into `EVIDENCE/HARNESS_RESULTS.md`.
- Cached model corpora (offline, no model needed to re-score): `data/v1/digital_route/slice_05_scale/corpus.jsonl`, `slice_02_*`, `slice_06_repair/`.

## 7. Audit schemas
- `configs/validator_audit_schema_v1.json` — `validator_audit_v1` (validator decisions).
- `src/routemap_controller/audit.py` — `route_decision_v1` (controller decisions; maps to the architecture's §7.1 core schema).
- `schemas/harness_decision_v1.schema.json` — canonical harness audit record embedding lane records under `validator_record`; crosswalk in `docs/AUDIT_SCHEMA.md`.

## 8. No-claim list (locked)
No lossless recovery from any fingerprint (information floor); no digital-root maths on float attention weights;
no universal speedup (residue verify is slower than recompute at ordinary sizes); the checkers are one-sided —
they establish wrongness, never correctness; no novel core algorithms (residues/AST/schema/IDF/LSH are standard) —
the contribution is integration, the audit schema, and the zero-false-positive / no-self-grading discipline.
Full version: `ROADMAP_BASELINE.md` and the report's "What is not claimed" section.

## 9. Per-slice records and the report
- `data/v1/digital_route/records/PHASE3_INDEX.md` + `SLICE_01..16_*.md` — dated record of every slice with verified numbers.
- `RouteMap_Intelligence_Architecture_Report.docx` (repo root / workspace) — the synthesized build & verification report.
