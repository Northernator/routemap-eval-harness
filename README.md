# RouteMap — a route-and-validate control layer for LLM reliability

RouteMap applies one control loop at several layers of an LLM system: **fingerprint** an output cheaply,
**route** to the subset that matters, **compute** only that subset, **validate** the shortcut, and
**escalate** when it looks unsafe. The individual techniques are known; the contribution is their
integration, a locked audit schema, and a zero-false-positive / no-self-grading discipline.

> RouteMap began as a semantic route-extraction evaluation harness (Phases 1–2, see *Origins* below). It grew
> into a verified route-and-validate stack of seven standalone packages (slices 01–16).

## Quick start
```powershell
git clone https://github.com/Northernator/routemap-eval-harness
cd routemap-eval-harness                           # repo root = package root (src/, run_evidence.py live here)
pip install -r requirements-dev.txt                # python + numpy + pytest
$env:PYTHONPATH='src'                              # bash/macOS: export PYTHONPATH=src
python run_evidence.py                             # runs the suites + offline benchmarks -> EVIDENCE/RESULTS.md
```

## The seven packages
| Package | What it does | Verified headline |
| --- | --- | --- |
| `routemap_validators` | routed sound checkers (arithmetic/code/JSON), one-sided verdicts, `UNCHECKABLE` fail-safe, locked `validator_audit_v1` schema | practical false-positive rate 0.000 on real wrapped output (N=30); JSON-schema repair 0.60 -> 0.33 |
| `routemap_digital` | residue/CRT/cycle engine + one-sided verifier + `routemap` CLI | catches real model arithmetic errors at zero false positives; blind spot characterized |
| `routemap_bench` | model-agnostic HugeArithmeticRouteBench | oracle-verifier agreement 1.000; ground truth generated independently of the engine |
| `routemap_token` | token-importance routing with `router_mode` (default **element** ~0.44; **token** prior baseline ~0.34; codon-gate), leak-safe | default validated on a synthetic blind set + 2 real human-reviewed held-out sets at 0 recall loss, frozen weights |
| `routemap_embedding` | SimHash / LSH / PQ route-and-rerank index | recall/speed frontier mapped (characterized negative) |
| `routemap_controller` | `route_decide()` composing the lanes, guarded cheap path, schema-locked `route_decision_v1` audit | 9/9 tests; no silent pruning |
| `routemap_matrix` | KV-cache importance-routing prototype | route/validate core verified (CPU); GPU result hardware-gated (research-only) |

## Scorecard
| Lane | Useful today? | Scientific result | Product value |
| --- | --- | --- | --- |
| Sound validators | Yes | Strong positive | High |
| Digital verifier | Yes (narrow) | Strong positive | Medium-high (arithmetic-heavy) |
| Token routing | Maybe | Bounded positive | Medium |
| Embedding fingerprints | Not yet | Characterized negative | Low until tuned ANN |
| Unified controller | Yes | Strong architecture result | High |
| Matrix / KV routing | Not yet | Hardware-gated negative | Research only |

## Reproduce
- One command: `python run_evidence.py` -> writes `EVIDENCE/RESULTS.md`.
- Harness demo pack: `python scripts/run_demo_pack.py` -> writes `EVIDENCE/HARNESS_RESULTS.md` with caught failures, repairs, escalations, audit completeness, and latency p50/p95.
- Harness model matrix: `python scripts/run_model_matrix.py` -> writes `EVIDENCE/MODEL_MATRIX.md`; Ollama is local, API adapters run only when their env vars are set, and every output is checked by the same harness.
- Acceptance gate: `python scripts/check_acceptance.py` -> enforces zero false accepts, sound-lane FP 0.000, schema-valid JSONL, default element wording, and no correctness-certification claims.
- Full manifest (commit, env, seeds, datasets, audit schemas): [`EVIDENCE_PACK.md`](EVIDENCE_PACK.md).
- External-auditor checklist: [`EXTERNAL_AUDIT_CHECKLIST.md`](EXTERNAL_AUDIT_CHECKLIST.md).
- Per-slice record of every result: `data/v1/digital_route/records/PHASE3_INDEX.md` + `SLICE_01..16_*.md`.
- GPU (matrix) handoff: [`src/routemap_matrix/HANDOFF.md`](src/routemap_matrix/HANDOFF.md).

## Claims and no-claims
**Claimed (verified):** a routed library of sound checkers holds 0.000 practical false positives on real
wrapped model output across arithmetic/code/JSON; structured-output verification is genuinely useful (60% of
a small model's JSON violated its schema, all caught, repair halves the errors); the arithmetic verifier
catches 100% of real model arithmetic errors at zero false positives with a precisely characterized,
shrinkable blind spot; the default element router drops about 44% of tokens (the token-prior baseline drops about a third) at
near-zero answer-token loss on real gold — validated on a synthetic blind set and two real human-reviewed
held-out sets with frozen weights — and beats an IDF-stopword baseline by 0.62 in recall.

**Not claimed:** no lossless recovery from a fingerprint (information floor); no digital-root maths on float
attention weights; no universal speedup (residue verification is slower than recompute at ordinary sizes);
the checkers are one-sided (they establish wrongness, never certify correctness); no novel core algorithms —
the value is integration, the audit schema, and the discipline. Three lanes are reported as **characterized
negatives**: the token-routing ceiling, the embedding recall/speed split, and the matrix hardware wall.

## Status
Seven phases built; four verified positives plus three characterized negatives. Internal correctness is
verified (every slice re-run and re-derived against source), and a **frozen held-out blind benchmark**
(`data/blind/v1/`, scored once, never tuned against) shows the arithmetic and structured-output lanes holding
catch 1.000 / false-positive 0.000 on fresh data. Remaining: cross-model coverage and the hardware-gated GPU
attention measurement.

---

## Origins — the evaluation harness (Phases 1–2)
RouteMap began as a semantic route-extraction benchmark: map each passage into typed route fields
(`document_scope + entity + role + relation + operative_status`) and test whether a typed route index enables
sparse retrieval — `query -> route extraction -> small candidate set -> answer` — at preserved quality.

Offline demo (no API; deps `pandas` + `numpy`):
```
python src/run_local_demo.py        # or: make demo
```
This builds a gold-sample CSV from `data/documents/`, runs the keyword and RouteMap baselines and an offline
route-extractor stub, and scores the outputs under `data/outputs/`. Batch evaluation: `src/run_batch_eval.py`.

Key findings from this phase: an LLM role classifier beats deterministic baselines at every taxonomy level
(in-domain 0.825 / out-of-domain 0.556); an extractive entity field with a domain-general fallback transfers
where a fixed ontology collapses; and a lexical leakage probe showed synthetic gold cannot certify
generalization — human gold is the gate. See `RouteMap_Phase2_Benchmark_Report.docx` and `data/v1/gold/`.
