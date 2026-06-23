# Entity Matching Diagnostic v1

ABLATION ONLY. Gold is frozen; this diagnostic must not tune or promote the locked true-blind test, prompts, taxonomies, thresholds, ontology, evaluator, or R6.

- embedding_axis_ran: true
- embedding_skip_reason: available

## All Gold Rows

| matcher | threshold | variant | soft_jaccard | soft_f1 |
|---|---|---|---|---|
| M0_exact_canonical | 1.0 | combined_v3 | 0.011806 | 0.018122 |
| M1_normalized_exact | 1.0 | combined_v3 | 0.009028 | 0.013492 |
| M2_token_set_jaccard | 0.3 | combined_v3 | 0.018882 | 0.030192 |
| M2_token_set_jaccard | 0.5 | combined_v3 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.6 | combined_v3 | 0.020734 | 0.032507 |
| M3_fuzzy_difflib | 0.7 | combined_v3 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.8 | combined_v3 | 0.009028 | 0.013492 |
| M3_fuzzy_difflib | 0.9 | combined_v3 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.5 | combined_v3 | 0.021528 | 0.033664 |
| M4_embedding_cosine | 0.6 | combined_v3 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.7 | combined_v3 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.8 | combined_v3 | 0.009028 | 0.013492 |
| M0_exact_canonical | 1.0 | D | 0.011806 | 0.018122 |
| M1_normalized_exact | 1.0 | D | 0.009028 | 0.013492 |
| M2_token_set_jaccard | 0.3 | D | 0.018882 | 0.030192 |
| M2_token_set_jaccard | 0.5 | D | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.6 | D | 0.020734 | 0.032507 |
| M3_fuzzy_difflib | 0.7 | D | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.8 | D | 0.009028 | 0.013492 |
| M3_fuzzy_difflib | 0.9 | D | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.5 | D | 0.021528 | 0.033664 |
| M4_embedding_cosine | 0.6 | D | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.7 | D | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.8 | D | 0.009028 | 0.013492 |
| M0_exact_canonical | 1.0 | R6 | 0.011806 | 0.018122 |
| M1_normalized_exact | 1.0 | R6 | 0.009028 | 0.013492 |
| M2_token_set_jaccard | 0.3 | R6 | 0.018882 | 0.030192 |
| M2_token_set_jaccard | 0.5 | R6 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.6 | R6 | 0.020734 | 0.032507 |
| M3_fuzzy_difflib | 0.7 | R6 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.8 | R6 | 0.009028 | 0.013492 |
| M3_fuzzy_difflib | 0.9 | R6 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.5 | R6 | 0.021528 | 0.033664 |
| M4_embedding_cosine | 0.6 | R6 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.7 | R6 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.8 | R6 | 0.009028 | 0.013492 |

## Scored Rows

| matcher | threshold | variant | soft_jaccard | soft_f1 |
|---|---|---|---|---|
| M0_exact_canonical | 1.0 | combined_v3 | 0.011806 | 0.018122 |
| M1_normalized_exact | 1.0 | combined_v3 | 0.009028 | 0.013492 |
| M2_token_set_jaccard | 0.3 | combined_v3 | 0.018882 | 0.030192 |
| M2_token_set_jaccard | 0.5 | combined_v3 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.6 | combined_v3 | 0.020734 | 0.032507 |
| M3_fuzzy_difflib | 0.7 | combined_v3 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.8 | combined_v3 | 0.009028 | 0.013492 |
| M3_fuzzy_difflib | 0.9 | combined_v3 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.5 | combined_v3 | 0.021528 | 0.033664 |
| M4_embedding_cosine | 0.6 | combined_v3 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.7 | combined_v3 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.8 | combined_v3 | 0.009028 | 0.013492 |
| M0_exact_canonical | 1.0 | D | 0.011806 | 0.018122 |
| M1_normalized_exact | 1.0 | D | 0.009028 | 0.013492 |
| M2_token_set_jaccard | 0.3 | D | 0.018882 | 0.030192 |
| M2_token_set_jaccard | 0.5 | D | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.6 | D | 0.020734 | 0.032507 |
| M3_fuzzy_difflib | 0.7 | D | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.8 | D | 0.009028 | 0.013492 |
| M3_fuzzy_difflib | 0.9 | D | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.5 | D | 0.021528 | 0.033664 |
| M4_embedding_cosine | 0.6 | D | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.7 | D | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.8 | D | 0.009028 | 0.013492 |
| M0_exact_canonical | 1.0 | R6 | 0.011806 | 0.018122 |
| M1_normalized_exact | 1.0 | R6 | 0.009028 | 0.013492 |
| M2_token_set_jaccard | 0.3 | R6 | 0.018882 | 0.030192 |
| M2_token_set_jaccard | 0.5 | R6 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.6 | R6 | 0.020734 | 0.032507 |
| M3_fuzzy_difflib | 0.7 | R6 | 0.013790 | 0.021594 |
| M3_fuzzy_difflib | 0.8 | R6 | 0.009028 | 0.013492 |
| M3_fuzzy_difflib | 0.9 | R6 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.5 | R6 | 0.021528 | 0.033664 |
| M4_embedding_cosine | 0.6 | R6 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.7 | R6 | 0.009028 | 0.013492 |
| M4_embedding_cosine | 0.8 | R6 | 0.009028 | 0.013492 |

## Headroom

| variant | gold_entities_total | frac_gold_text_present | frac_gold_captured_by_prediction | headroom_gap |
|---|---|---|---|---|
| combined_v3 | 350 | 0.988571 | 0.008571 | 0.980000 |
| D | 350 | 0.988571 | 0.008571 | 0.980000 |
| R6 | 350 | 0.988571 | 0.008571 | 0.980000 |

## Verdicts

| boolean | value |
|---|---|
| metric_brittleness_significant | NO |
| synonymy_gap | NO |
| extractor_failure_dominant | YES |
| embedding_axis_ran | YES |

## Recommendation

pursue a domain-general entity extractor; current predictions do not recover gold entities even under relaxed matching.
