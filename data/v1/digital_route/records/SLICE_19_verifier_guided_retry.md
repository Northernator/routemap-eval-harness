# Slice 19 — Verifier-guided retry + escalation (controller loop)

Date: 2026-06-23
Purpose: turn the residue verifier from a passive monitor into an active loop. On
RULED_OUT_WRONG, re-prompt the model with terse, specific feedback (which moduli
failed), retry up to 2×, then escalate to deterministic compute. Measure whether
feedback repairs the model, how often we escalate, the call cost, and the safety
property — zero false accepts.

Code: `routemap_trachtenberg_test_pack/routemap_trachtenberg/run_retry.py` (pluggable
model_fn; ollama llama3.1). Same residue verifier as the rest of the project.

## Setup
- Model: ollama **llama3.1**, temp 0; N=100, seed 7, 3–4 digit × 3–4 digit; max_retries 2.
- Loop: freeform → verify → if ruled out, feedback-retry (≤2) → else escalate to exact a*b.
- Independently re-scored from the cache; **every** model-accepted answer re-verified
  residue-consistent AND actually correct (audit).

## Result (single run, N=100)
| Metric | Value |
| --- | --- |
| base freeform accuracy (attempt 0) | 24/100 = **24%** |
| fixed by verifier-guided retry | **+9** (8 at retry 1, 1 at retry 2) |
| model answers accepted (verified) | 33/100 |
| escalated to deterministic compute | 67/100 = 67% |
| FINAL pipeline accuracy | 100/100 = **100%** |
| false accepts (wrong but verifier-accepted) | **0** (audited two ways) |
| accuracy among model-accepted answers | 100% |
| cost | 244 calls, **2.44 per problem** |

## Reading
The verifier is a perfect gate: **0 false accepts** — it never trusted a wrong answer,
and every accepted answer was independently re-verified both residue-consistent and
correct. Verifier feedback repaired a modest **9/100** (slightly better than Slice 06's
0/30 — terse modulus feedback carries a little signal for llama3.1 on small products,
but it is weak). The 67 the model could not fix were escalated to exact compute, giving
100% final accuracy by construction, at ~2.4× the single-call cost.

Honest scope: for pure multiplication the deterministic fallback is free and exact, so
the model is beside the point (you would just compute a*b). The value is the **controller
mechanism** and its guarantees — retry-or-escalate behind a sound, zero-false-accept gate
with an audited cost — which generalize to tasks where the model *is* needed and recompute
*isn't* free. Confirms the thesis: the model is a weak arithmetic executor; RouteMap
(verify → repair → escalate) makes the pipeline trustworthy.

Reproduce: `cd routemap_trachtenberg_test_pack/routemap_trachtenberg && python run_retry.py
--n 100 --model llama3.1 --max-retries 2` (resumable).
