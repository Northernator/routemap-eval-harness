# Phase 3 Slice 11 - Token Importance Fingerprint

Date: 2026-06-23

## Purpose

Create `routemap_token`, a standalone token-importance prior that routes cheap tokens away while preserving answer/evidence tokens for QA-style contexts.

## Idea to Discipline

Chris's instinct was to group words into value-types: function words like `a`, `an`, `the`, and `them` are cheap, while content words like `island` and `artist` carry more value. The disciplined version gives each token a static class plus IDF prior, refines it with context, then emits a route decision. The value is the route score attached to the token, not an integer id.

## Design

- `prior.py`: static class and IDF prior.
- `context.py`: inference-only contextual features; no gold answer/evidence input.
- `policy.py`: risk-aware route action with hard keep defaults for negation, numbers, formulas, code, citations, named entities, and instructions.
- `trace.py`: JSONL trace rows with `later_needed` as eval-only label.
- `bench.py`: TokenRouteQA fallback dataset, metrics, baselines, bars.
- `run_token_bench.py`: CLI.

## Leakage Guard

Gold answer and evidence spans are used only to label `later_needed` during evaluation. Contextual features use question overlap, entity flag, negation/modal, position, citation boundary, quote boundary, and neighbors. Perturbing gold answer/evidence leaves route decisions unchanged.

## TokenRouteQA Card

| Metric | Value |
| --- | ---: |
| max_reduction_at_recall_loss_lt_0.02 | 0.344 |
| recall_loss_at_best_0.02 | 0.000 |
| max_reduction_at_recall_loss_lt_0.01 | 0.344 |
| recall_loss_at_best_0.01 | 0.000 |
| random_drop_recall_matched | 0.786 |
| naive_stopword_recall_matched | 0.929 |
| policy_vs_random_recall_delta | 0.214 |
| policy_vs_naive_stopword_recall_delta | 0.071 |
| minimum_bar | PASS |
| strong_bar | FAIL |

Dataset source: `fallback_constructed_token_route_qa`

Dataset size: 6 samples

IDF source: `data\documents`

## Verification

Run with:

```text
python -B -m pytest rt_test_token.py -q
6 passed

python -B -m routemap_token run --out <temp-dir>
```

## Index Note

`PHASE3_INDEX.md` was intentionally left unchanged to preserve the new-files-only package scope. Suggested index row:

`- 2026-06-23 - Slice 11: token-importance fingerprint package; TokenRouteQA minimum bar PASS, leakage guard verified.`
