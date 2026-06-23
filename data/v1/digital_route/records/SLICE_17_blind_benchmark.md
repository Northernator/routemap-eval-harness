# Slice 17 — Frozen external BLIND benchmark (data/blind/v1)

Date: 2026-06-23
Purpose: move from "internally verified" to "hard to dismiss" — a held-out suite the engines were never
tuned against. The reviewer's highest-value remaining gap.

## Discipline
- Generated **outside** the dev loop by `src/blind/generate_blind_v1.py`, seed **20260623** (distinct from
  the dev seed 7), fresh distribution (invented entities/terms, new schemas, new number ranges).
- Ground truth computed by **independent pure-Python code**, never the route engines (no self-grading).
- **Frozen**: `manifest.json` holds SHA-256 of every file; `src/blind/score_blind_v1.py` verifies the hashes
  and refuses to run if any changed.
- **Scored exactly once.** No tuning, no re-run-with-tweaks.

## Files (data/blind/v1/)
arithmetic_blind_500.jsonl (500) · schema_outputs_blind_200.jsonl (200) · extraction_blind_100.csv (100) ·
retrieval_blind_100.jsonl (100) + retrieval_corpus.jsonl (200 docs) · manifest.json · BLIND_RESULTS.{md,json}

## Result (single scored run)
| Lane | N | Result |
| --- | ---: | --- |
| Arithmetic (routemap_digital) | 500 | catch **1.000** of residue-inconsistent (170/170); FP **0.000** (0/253 correct); off-by-M blind spot uncaught (77, sound) |
| Structured output (routemap_validators) | 200 | catch **1.000** of violations (118/118); FP **0.000** (0/82 valid); uncheckable 0.000; markdown-wrapped handled |
| Retrieval (routemap_embedding) | 100 | full recall@10 **1.000**; fingerprint-route recall@10 **0.910** (honest ~9% routing cost) |
| Extraction (deterministic baseline) | 100 | entity recall **0.667** (offline capitalized-entity baseline; LLM extractor is ollama-gated) |

## Reading
On fresh data never tuned against, the two strongest lanes generalize cleanly: the arithmetic verifier and
the structured-output validator both hold **catch 1.000 / false-positive 0.000**, with the arithmetic blind
spot behaving exactly as characterized (off-by-combined-modulus errors correctly returned NOT_RULED_OUT). The
retrieval fingerprint shows its honest ~9% recall cost; the offline extraction baseline shows its honest
ceiling (0.667 — misses lowercase domain terms; the LLM path would do better but is ollama-gated). Nothing was
re-run or tuned after seeing these numbers.

This is the credibility step: the zero-false-positive soundness is now demonstrated on held-out data, not just
fit to dev data. Wired into `run_evidence.py` (step "blind: held-out suite") so CI re-verifies it every build.
