# Entity Alignment Ablation v1 Comparison

ABLATION ONLY. Gold was frozen before prediction. These results must not promote R6 or tune the locked true-blind test, prompts, taxonomies, thresholds, ontology, or evaluator.

## Metrics

| condition | variant | role | coarse_3 | entity_jaccard | entity_exact | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---|---|---|---|---|---|---|---|---|
| C0_original | combined_v3 | 0.306 | 0.556 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C0_original | D | 0.236 | 0.306 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C0_original | R6 | 0.306 | 0.556 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C1_delimiter_only | combined_v3 | 0.306 | 0.556 | 0.012 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C1_delimiter_only | D | 0.236 | 0.306 | 0.012 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C1_delimiter_only | R6 | 0.306 | 0.556 | 0.012 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C2_option_a_alias | combined_v3 | 0.306 | 0.556 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C2_option_a_alias | D | 0.236 | 0.306 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C2_option_a_alias | R6 | 0.306 | 0.556 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C3_option_b_expanded_PROPOSAL | combined_v3 | 0.306 | 0.556 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C3_option_b_expanded_PROPOSAL | D | 0.236 | 0.306 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| C3_option_b_expanded_PROPOSAL | R6 | 0.306 | 0.556 | 0.015 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Alias Coverage

| measure | value |
|---|---|
| unique_gold_entities | 337 |
| mapped_high_medium | 5 |
| mapped_low_approved | 0 |
| total_applied | 5 |
| coverage_fraction | 0.014837 |

## Verdict Checks

| check | value |
|---|---|
| parity_check_passed | YES |
| delimiter_fix_recovers_jaccard | YES |
| alias_alignment_reaches_target_band | NO |
| ontology_expansion_attempted | YES |
| ontology_expansion_helps | NO |

## ABLATION Fair R6 Read

C2 checks:

| check | value |
|---|---|
| role_beats_combined | NO |
| coarse_3_preserved_or_improved | YES |
| relaxed_1_beats_combined | NO |
| relaxed_2_matches_or_beats_combined | YES |
| relaxed_3_matches_combined | YES |
| strict_not_lower_than_combined | YES |

C3 PROPOSAL checks:

| check | value |
|---|---|
| role_beats_combined | NO |
| coarse_3_preserved_or_improved | YES |
| relaxed_1_beats_combined | NO |
| relaxed_2_matches_or_beats_combined | YES |
| relaxed_3_matches_combined | YES |
| strict_not_lower_than_combined | YES |

## Recommendation

Delimiter and high/medium alias map are insufficient; run human-reviewed ontology expansion or domain-general entity matching before interpreting entity-dependent strict/relaxed metrics.
