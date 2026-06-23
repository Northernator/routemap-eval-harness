# Domain-General Entity Extractor v1

ABLATION ONLY. Gold is frozen. This is a feasibility read with a priori extractor constants, not a tuned true-blind score.

- embedding_axis_ran: true
- embedding_status: available
- llm_status: skipped: --with-llm not passed
- headroom_ceiling_context: 0.988571

## Main Table

| variant | matcher | threshold | soft_f1 | soft_precision | soft_recall | soft_jaccard | mean_preds_per_seg |
|---|---|---|---|---|---|---|---|
| proper_quoted | M1_normalized_exact | 1.0 | 0.064297 | 0.222222 | 0.037847 | 0.037847 | 0.597 |
| proper_quoted | M3_fuzzy_difflib | 0.6 | 0.075871 | 0.250000 | 0.045255 | 0.045255 | 0.597 |
| proper_quoted | M4_embedding_cosine | 0.5 | 0.089363 | 0.277778 | 0.054282 | 0.053356 | 0.597 |
| noun_chunks_topk | M1_normalized_exact | 1.0 | 0.190923 | 0.147569 | 0.279134 | 0.123061 | 8.000 |
| noun_chunks_topk | M3_fuzzy_difflib | 0.6 | 0.467148 | 0.378472 | 0.634755 | 0.318631 | 8.000 |
| noun_chunks_topk | M4_embedding_cosine | 0.5 | 0.537401 | 0.435764 | 0.728588 | 0.379233 | 8.000 |
| ontology_v1_reference | M1_normalized_exact | 1.0 | 0.013492 | 0.027778 | 0.009028 | 0.009028 | 0.264 |
| ontology_v1_reference | M3_fuzzy_difflib | 0.6 | 0.032507 | 0.076389 | 0.021197 | 0.020734 | 0.264 |
| ontology_v1_reference | M4_embedding_cosine | 0.5 | 0.033664 | 0.076389 | 0.021991 | 0.021528 | 0.264 |

## Verdicts

| boolean | value |
|---|---|
| beats_ontology_baseline | YES |
| reaches_in_domain_band | YES |
| precision_healthy | YES |
| llm_variant_ran | NO |

## Recommendation

Adopt extractive entity field as next development path, starting from noun_chunks_topk with fixed dev-set tuning before any fresh blind eval.
