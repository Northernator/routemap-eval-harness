# RouteMap Blind Benchmark v1 — Results

Frozen held-out suite generated outside the development loop (seed 20260623, distinct from the dev seed 7),
ground truth computed by independent pure-Python code, SHA-256 locked, and **scored exactly once**. The route
engines were built and tuned only on dev data; this set was never tuned against.

## Results
| Lane | N | Result |
| --- | ---: | --- |
| Arithmetic (`routemap_digital`) | 500 | catch **1.000** of residue-inconsistent errors; false-positive **0.000**; off-by-M blind spot uncaught (sound). 170 catchable errors all caught, 0/253 correct wrongly ruled out, 77 off-by-M correctly returned NOT_RULED_OUT. |
| Structured output (`routemap_validators`) | 200 | catch **1.000** of schema violations; false-positive **0.000**; uncheckable 0.000. 118 violations all caught, 0/82 valid wrongly ruled out, incl. markdown-wrapped outputs extracted cleanly. |
| Retrieval (`routemap_embedding`) | 100 | full recall@10 **1.000**; fingerprint-route recall@10 **0.910**. Brute force finds the gold doc every time; LSH routing loses ~9% recall — the characterized fingerprint tradeoff. |
| Extraction (deterministic baseline) | 100 | entity recall **0.667**. Offline capitalized-entity baseline catches the named entities, misses lowercase domain terms; the LLM extractor is ollama-gated. |

## What this shows
On fresh data never tuned against, the two strongest lanes generalize cleanly: the arithmetic verifier
catches 100% of catchable errors at zero false positives with its blind spot behaving exactly as
characterized, and the structured-output validator catches 100% of schema violations at zero false positives
including markdown-wrapped outputs. The retrieval fingerprint shows its honest ~9% recall cost and the offline
extraction baseline its honest ceiling. No lane was re-run or tuned after seeing these numbers.

## Reproduce
```
# from the repo root, with src on PYTHONPATH:
python src/blind/score_blind_v1.py        # verifies the frozen SHA-256 manifest, then scores once
python src/blind/generate_blind_v1.py     # regenerate the frozen set (byte-identical from the seed)
```
