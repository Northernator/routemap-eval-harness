# Slice 18 — Trachtenberg digit-local prompting (negative result)

Date: 2026-06-23
Purpose: test whether giving a small LLM a digit-local arithmetic *route* (Trachtenberg unit
rules / general digit convolution) makes its multiplication more reliable than freeform — and
whether the residue verifier catches whatever slips. This is a **producer** question (does the
route help the model compute?), not a checker question.

Code: `routemap_trachtenberg_test_pack/routemap_trachtenberg/` (standalone experiment pack at the
workspace root; planned repo home `src/experiments/trachtenberg_prompting/`). Contains the routes
(×5/6/7/11/12/13 + general digit convolution, each with a per-column trace), an inlined residue
verifier that mirrors `routemap_digital` (proven verdict-for-verdict equal, 0 mismatches / 20,000),
error-injection coverage, and a pluggable ollama harness (`run_real.py`).

## Setup
- Model: ollama **llama3.1** (8B), temperature 0, num_predict 700.
- N=30 problems, seed 7, 3–4 digit × 3–4 digit, **identical across modes** (gap is method, not numbers).
- Modes: `freeform` (just compute a×b) · `longmult` (standard long-multiplication-with-scratchpad —
  the in-distribution baseline a route must beat) · `route` (digit-convolution route template).
- Scored by the residue bank {7,9,11,13,37,101}; independently re-scored from the raw response cache.

## Result (single run; offline route-correctness + verifier-coverage separately at 100%)
| Mode | Raw accuracy | mean s/call | Verifier catch on wrong | Residual (wrong & undetected) |
| --- | ---: | ---: | --- | ---: |
| freeform | **11/30 = 36.7%** | 12.4 | 19/19 = 1.000 | 0 |
| longmult | 1/30 = 3.3% | 35.2 | 29/29 = 1.000 | 0 |
| route | 1/30 = 3.4% | 63.4 | 28/28 = 1.000 | 0 |

Verifier total: **76/76 wrong answers ruled out, 0 residual, 0 false-reject** of the correct answers.

## Reading
Structure did NOT help — it hurt. Both "show your work" modes were ~11× WORSE than freeform, not
better. A small model cannot reliably execute a long digit-by-digit procedure: it drops carries,
mis-adds partial products, botches the convolution, and sometimes fails to emit the answer format.
Forcing the procedure multiplies the failure points instead of constraining them. The route is also
the slowest (63 s/call) and least answer-compliant (only 20/30 emitted a clean `ANSWER:` line).

Checked NOT a truncation/parse artifact: only 1–2 near-cap responses per structured mode, and the
spot-checked failures are genuine arithmetic (e.g. 940×648 → model formed partial products then
mis-added them to 608880).

The verifier is the win: across all three generation methods it ruled out every wrong answer at zero
false-positive — the route-and-validate thesis holding on a real model's natural errors (same shape
as Slice 02's 27/27).

## Conclusion
Trachtenberg-style digit-local prompting **worsened** llama3.1 arithmetic versus freeform; the residue
verifier reconfirmed (76/76). **Producer refuted, checker reconfirmed.** Do not build a
`routemap_trachtenberg` rule library for LLM prompting. Lesson: for small models, procedural
chain-of-thought can be an *error multiplier*; sound route validation is safer than trusting the
generated working.

Caveat: N=30, a single small local model. Chain-of-thought usually helps *larger* models, so this is
a small-model-execution result, not a universal claim. The RouteMap-native version still worth
testing keeps the division of labour right: the model *selects* the route, deterministic code
*executes* the arithmetic, the verifier *validates*, the controller *escalates*.

Reproduce: `cd routemap_trachtenberg_test_pack/routemap_trachtenberg && python run_real.py --n 30
--model llama3.1` (resumable). Offline evidence (no model): `python experiment.py` +
`python verify_independent.py`.
