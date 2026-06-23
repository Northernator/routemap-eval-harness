# ROLE_LLM_CLASSIFIER_REPORT

Local Ollama llama3.1, temperature 0. Prompt examples are frozen seed_train rows only. Locked fresh/adjudicated test files are not read or scored.

Known prior locked-test references: centroid 8-role 0.456; coarse-3 0.810; true-blind combined/R6 role reference 0.306.

## Accuracy by taxonomy

| dataset | model | taxonomy | accuracy |
| --- | --- | --- | --- |
| dev | llm | fine_8 | 0.825000 |
| dev | llm | coarse_5 | 0.850000 |
| dev | llm | coarse_4 | 0.912500 |
| dev | llm | coarse_3 | 0.937500 |
| dev | baseline | fine_8 | 0.525000 |
| dev | baseline | coarse_5 | 0.600000 |
| dev | baseline | coarse_4 | 0.612500 |
| dev | baseline | coarse_3 | 0.775000 |
| true_blind | llm | fine_8 | 0.555556 |
| true_blind | llm | coarse_5 | 0.625000 |
| true_blind | llm | coarse_4 | 0.638889 |
| true_blind | llm | coarse_3 | 0.680556 |
| true_blind | baseline | fine_8 | 0.125000 |
| true_blind | baseline | coarse_5 | 0.166667 |
| true_blind | baseline | coarse_4 | 0.180556 |
| true_blind | baseline | coarse_3 | 0.319444 |

## Hard-pair confusion counts

| dataset | model | gold | pred | count |
| --- | --- | --- | --- | --- |
| dev | llm | CLAIM | DEFINE | 0 |
| dev | llm | DEFINE | CLAIM | 0 |
| dev | llm | RESULT | CLAIM | 0 |
| dev | llm | CLAIM | RESULT | 0 |
| dev | llm | BACKGROUND | CLAIM | 1 |
| dev | llm | CLAIM | BACKGROUND | 0 |
| dev | baseline | CLAIM | DEFINE | 1 |
| dev | baseline | DEFINE | CLAIM | 1 |
| dev | baseline | RESULT | CLAIM | 0 |
| dev | baseline | CLAIM | RESULT | 0 |
| dev | baseline | BACKGROUND | CLAIM | 0 |
| dev | baseline | CLAIM | BACKGROUND | 1 |
| true_blind | llm | CLAIM | DEFINE | 0 |
| true_blind | llm | DEFINE | CLAIM | 0 |
| true_blind | llm | RESULT | CLAIM | 0 |
| true_blind | llm | CLAIM | RESULT | 0 |
| true_blind | llm | BACKGROUND | CLAIM | 5 |
| true_blind | llm | CLAIM | BACKGROUND | 0 |
| true_blind | baseline | CLAIM | DEFINE | 0 |
| true_blind | baseline | DEFINE | CLAIM | 0 |
| true_blind | baseline | RESULT | CLAIM | 3 |
| true_blind | baseline | CLAIM | RESULT | 0 |
| true_blind | baseline | BACKGROUND | CLAIM | 1 |
| true_blind | baseline | CLAIM | BACKGROUND | 0 |

## Parse rates

| dataset | rows | parse_failed | invalid_label | parse_invalid_rate |
| --- | --- | --- | --- | --- |
| dev | 80 | 0 | 0 | 0.000000 |
| true_blind | 72 | 0 | 0 | 0.000000 |

## Verdicts

| llm_beats_baseline_8role_dev | llm_beats_baseline_outdomain_8role | llm_beats_0306_outdomain_reference | llm_coarse3_strong | hard_pairs_reduced | hard_pair_total_llm | hard_pair_total_baseline |
| --- | --- | --- | --- | --- | --- | --- |
| true | true | true | true | true | 6 | 7 |

## Recommendation

Adopt the LLM role classifier for diagnostic runs. Operationally, coarse_3 is the strongest taxonomy; keep fine_8 as an analysis label until hard-boundary errors shrink. Next step: inspect CLAIM/DEFINE and RESULT/CLAIM residuals, then reserve the locked fresh test for one final read.