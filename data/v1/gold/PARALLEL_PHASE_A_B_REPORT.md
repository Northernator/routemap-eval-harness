# Parallel Phase A/B Report

## Why This Phase Exists

RouteMap v1 showed measurable coarse route signal but weak exact full extraction. This phase prepares a provider-ready extractor path while expanding development data for boundary and entity coverage.

## Phase A Outputs

- JSON extraction contract: `src/routemap_extraction_contract.py`
- Provider interface: `src/routemap_extractor_provider.py`
- Offline rule provider and prompt-only provider
- Rule provider report: `data/v1/gold/ROUTEMAP_EXTRACTOR_RULE_PROVIDER_RESULTS.md`

## Phase B Outputs

- Expanded dataset size: 560 rows
- Split sizes: train 392, dev 84, test 84
- Coverage: 400 boundary-pair rows plus 160 entity-focused rows
- Role report: `data/v1/gold/EXPANDED_ROLE_BASELINE_RESULTS_V2.md`
- Entity report: `data/v1/gold/EXPANDED_ENTITY_BASELINE_RESULTS_V2.md`

## Expanded Data Impact

- Best role model on locked_fresh_adjudicated: `old_plus_expanded_train` / `word_unigram_bigram_nb` fine_8 0.506
- Best role model on expanded_test_v2: `old_plus_expanded_train` / `char_3_5gram_nb` fine_8 1.000
- Best entity model on locked_fresh_adjudicated: `ontology_v1` Jaccard 0.506, F1 0.634
- Best entity model on expanded_test_v2: `expanded_gazetteer` Jaccard 0.587, F1 0.724

## Next Recommendation

If expanded-data gains transfer to the locked fresh test, use the expansion for the next full extractor development cycle. If gains are mostly internal to expanded_test_v2, move to real LLM provider evaluation with frozen prompts and batch scoring.

Synthetic expansion is useful for development but must later be replaced or augmented with real documents and human labels.