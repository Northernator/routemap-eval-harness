# Phase 3 Slice 13 - TokenRouteQA Strong-Bar Push

Date: 2026-06-23

## Purpose

Push `routemap_token` toward the strong bar honestly: improve needed-span coverage first, add leak-safe inference-time scoring/clearing, and report the full reduction-vs-recall frontier without forcing a pass.

## Files Changed

- `src/routemap_token/bench.py`
- `src/routemap_token/context.py`
- `src/routemap_token/policy.py`
- `rt_test_token.py`
- `data/v1/digital_route/records/PHASE3_INDEX.md`
- `data/v1/digital_route/records/SLICE_13_token_strong_bar.md`

## Coverage

Before: 114/282 = 0.404

After: 133/282 = 0.472

Levers:

- token matching now lowercases, strips surrounding punctuation, and normalizes trailing plurals
- needed phrase matching remains contiguous whole-token matching
- unlocated multi-token phrases contribute their longest contiguous locatable sub-run of at least two tokens
- single-token substring matches remain disallowed

The lift is meaningful but also makes recall accounting stricter: 183 answer-bearing tokens are now evaluated, up from the prior labeled set.

## Leak-Safe Scoring And Clearing

Scoring levers:

- stronger question-overlap boost
- stronger sentence-initial / first-content-token boost
- low-information penalty for tokens that are both low-IDF and repeated non-first occurrences

Clearing levers:

- `negation`, `citation`, `code_token`, and `instruction` remain always-keep
- `named_entity`, `number`, and `formula` may bypass force-keep only when all inference-time conditions hold:
  no query overlap, low IDF, repeated non-first occurrence, no citation/negation/quote boundary, and not sentence-initial / first-content context
- distinctive entities are not cleared when they overlap the query, have high IDF, or are first mentions

Gold answer, evidence, and needed labels are not read by contextual features or clearing. The regression test now scrambles answer/evidence/needed phrases and verifies identical route scores/actions.

## TokenRouteQA Frontier

Dataset: `v1_full_extraction_gold` (99 samples)

IDF source: `data\documents`

| Recall loss tier | Threshold | Reduction | Recall loss | Policy-vs-random recall delta | Policy-vs-IDF-stopword recall delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| <0.01 | 0.55 | 0.343 | 0.005 | 0.344 | 0.617 |
| <0.02 | 0.55 | 0.343 | 0.005 | 0.344 | 0.617 |
| <0.05 | 0.65 | 0.378 | 0.049 | 0.333 | 0.590 |

## Full Curve

| Threshold | Reduction | Recall loss |
| ---: | ---: | ---: |
| 0.05 | 0.099 | 0.000 |
| 0.10 | 0.110 | 0.000 |
| 0.15 | 0.212 | 0.000 |
| 0.20 | 0.238 | 0.000 |
| 0.25 | 0.264 | 0.000 |
| 0.30 | 0.277 | 0.000 |
| 0.35 | 0.285 | 0.000 |
| 0.40 | 0.314 | 0.000 |
| 0.45 | 0.342 | 0.000 |
| 0.50 | 0.342 | 0.000 |
| 0.55 | 0.343 | 0.005 |
| 0.60 | 0.343 | 0.005 |
| 0.65 | 0.378 | 0.049 |
| 0.70 | 0.386 | 0.087 |
| 0.75 | 0.406 | 0.208 |
| 0.80 | 0.750 | 0.514 |
| 0.85 | 0.752 | 0.519 |
| 0.90 | 0.755 | 0.519 |
| 0.95 | 0.793 | 0.546 |

## Bars

| Bar | Result |
| --- | --- |
| minimum_bar | PASS |
| strong_bar | FAIL |

Strong bar was not honestly met. Achievable zero-loss reduction is 0.342; achievable near-zero-loss reduction under 1% recall loss is 0.343. The 50% strong threshold is not reachable on this data without real recall damage because the safe no/near-zero-loss region mostly exhausts punctuation and function words. The next reduction band starts dropping low-IDF domain content such as `risk`, `data`, `systems`, and `fairness`, which the stricter coverage pass now correctly marks as answer-bearing in several blank-query gold samples. Clearing repeated risk classes helps only when inference-safe, but aggressive clearing would also remove gold-needed repeated entities such as `AI`.

## Verification

```text
python -B -m pytest rt_test_token.py -q
10 passed

PYTHONPATH=src python -B -m routemap_token run --out %TEMP%\routemap_token_step5_final
needed_span_coverage 0.472
minimum_bar PASS
strong_bar FAIL
```
