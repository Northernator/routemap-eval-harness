# Phase 3 Slice 12 - TokenRouteQA Real Gold Wiring

Date: 2026-06-23

## Purpose

Harden `routemap_token` by replacing the constructed-only TokenRouteQA benchmark path with real gold data and token-boundary-safe needed-label matching.

## Files Changed

- `src/routemap_token/bench.py`
- `rt_test_token.py`

## Real Gold Wiring

Dataset source: `v1_full_extraction_gold`

Dataset size: 99 samples

Loaded read-only sources:

- `data/v1/gold/v1_full_extraction_gold_v1.csv`
- `data/gold/gold_segments_filled.csv`
- `data/v1/gold/v1_qa_targets.csv`
- `data/gold/gold_qa_filled.csv`

Each segment becomes a `TokenQASample`:

- `context`: segment `text`
- `question`: first deterministic QA query requiring the segment, if present
- `needed_phrases`: split `gold_entities` on `|` and `;`, plus locatable QA `gold_answer`
- fallback dataset only used if real gold files are absent

## Token-Boundary Labeling

`needed_token_indices()` now tokenizes both passage and needed phrase, then labels a token as needed only when it participates in a contiguous case-insensitive token sequence match. This fixes substring leakage such as evidence `not` matching inside `note`.

Needed phrase coverage: 114/282 = 0.404

Unlocated phrases are reported honestly and contribute no needed tokens.

## Leak Guard

Contextual features still receive no gold answer or evidence labels. Gold phrases are used only after routing to label `later_needed` for evaluation and trace rows. The no-leak test still perturbs gold answer/evidence and verifies identical route decisions.

## Real-Gold TokenRouteQA Card

| Metric | Value |
| --- | ---: |
| max_reduction_at_recall_loss_lt_0.02 | 0.357 |
| recall_loss_at_best_0.02 | 0.000 |
| max_reduction_at_recall_loss_lt_0.01 | 0.357 |
| recall_loss_at_best_0.01 | 0.000 |
| random_drop_recall_matched | 0.642 |
| naive_stopword_recall_matched | 0.855 |
| policy_vs_random_recall_delta | 0.358 |
| policy_vs_naive_stopword_recall_delta | 0.145 |
| minimum_bar | PASS |
| strong_bar | FAIL |

The strong bar is reported honestly as FAIL on the real-gold run: reduction at zero recall loss is 35.7%, below the 50-70% strong target.

## Verification

```text
python -B -m pytest rt_test_token.py -q
8 passed

python -B -m routemap_token run --out %TEMP%\routemap_token_real_gold
minimum_bar PASS, strong_bar FAIL
```

## Index Note

`PHASE3_INDEX.md` was intentionally left unchanged to keep the requested scope to `routemap_token` edits and this new record. Suggested index row:

`- 2026-06-23 - Slice 12: TokenRouteQA wired to real gold; dataset 99, needed coverage 0.404, minimum bar PASS, strong bar FAIL.`
