# FULL_EXTRACTION_LLM_ENTITIES_REPORT

Development read. LLM entity outputs are cached JSONL from local Ollama llama3.1 at temperature 0. Prompt is frozen and train-derived; no locked test files were read.

Prompt SHA256: `80c558d39443eb7e5ab19aec62ddeed0f1d3d08f6c82a18ae1e0f0d92e919abd`

## dev

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy | frac_softj_ge_0_5 | mean_preds_per_seg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ontology | exact | 0.452083 | 0.225000 | 0.525000 | 0.525000 | 0.525000 | 0.987500 | NA | 1.637500 |
| ontology | soft-difflib | 0.469345 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 | 1.637500 |
| ontology | soft-embedding | 0.465179 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 | 1.637500 |
| v2 | exact | 0.452083 | 0.225000 | 0.525000 | 0.525000 | 0.525000 | 0.987500 | NA | 2.537500 |
| v2 | soft-difflib | 0.472991 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 | 2.537500 |
| v2 | soft-embedding | 0.474702 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 | 2.537500 |
| llm_open | exact | 0.021250 | 0.000000 | 0.025000 | 0.025000 | 0.025000 | 0.987500 | NA | 0.837500 |
| llm_open | soft-difflib | 0.064167 | 0.012500 | 0.062500 | 0.062500 | 0.062500 | 0.987500 | 0.062500 | 0.837500 |
| llm_open | soft-embedding | 0.087083 | 0.012500 | 0.087500 | 0.087500 | 0.087500 | 0.987500 | 0.087500 | 0.837500 |
| llm_hybrid | exact | 0.452083 | 0.225000 | 0.525000 | 0.525000 | 0.525000 | 0.987500 | NA | 1.737500 |
| llm_hybrid | soft-difflib | 0.478512 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 | 1.737500 |
| llm_hybrid | soft-embedding | 0.471429 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 0.987500 | 0.550000 | 1.737500 |
| gold_other_llm_open | exact | 0.021250 | 0.012500 | 0.025000 | 0.025000 | 0.025000 | 1.000000 | NA | 0.837500 |
| gold_other_llm_open | soft-difflib | 0.064167 | 0.012500 | 0.062500 | 0.062500 | 0.062500 | 1.000000 | 0.062500 | 0.837500 |
| gold_other_llm_open | soft-embedding | 0.087083 | 0.025000 | 0.087500 | 0.087500 | 0.087500 | 1.000000 | 0.087500 | 0.837500 |
| gold_other_llm_hybrid | exact | 0.452083 | 0.250000 | 0.537500 | 0.537500 | 0.537500 | 1.000000 | NA | 1.737500 |
| gold_other_llm_hybrid | soft-difflib | 0.478512 | 0.275000 | 0.550000 | 0.550000 | 0.550000 | 1.000000 | 0.550000 | 1.737500 |
| gold_other_llm_hybrid | soft-embedding | 0.471429 | 0.275000 | 0.550000 | 0.550000 | 0.550000 | 1.000000 | 0.550000 | 1.737500 |

## true_blind

| variant | metric_mode | entity_avg_jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 | role_accuracy | frac_softj_ge_0_5 | mean_preds_per_seg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ontology | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA | 0.263889 |
| ontology | soft-difflib | 0.020734 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 | 0.263889 |
| ontology | soft-embedding | 0.021528 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0.000000 | 0.263889 |
| v2 | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA | 4.847222 |
| v2 | soft-difflib | 0.127552 | 0.000000 | 0.013889 | 0.013889 | 0.013889 | 1.000000 | 0.013889 | 4.847222 |
| v2 | soft-embedding | 0.170211 | 0.000000 | 0.027778 | 0.027778 | 0.027778 | 1.000000 | 0.027778 | 4.847222 |
| llm_open | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA | 0.902778 |
| llm_open | soft-difflib | 0.150959 | 0.041667 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 | 0.902778 |
| llm_open | soft-embedding | 0.159061 | 0.069444 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 | 0.902778 |
| llm_hybrid | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA | 0.958333 |
| llm_hybrid | soft-difflib | 0.127976 | 0.027778 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 | 0.958333 |
| llm_hybrid | soft-embedding | 0.136872 | 0.055556 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 | 0.958333 |
| gold_other_llm_open | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA | 0.902778 |
| gold_other_llm_open | soft-difflib | 0.150959 | 0.041667 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 | 0.902778 |
| gold_other_llm_open | soft-embedding | 0.159061 | 0.069444 | 0.180556 | 0.180556 | 0.180556 | 1.000000 | 0.180556 | 0.902778 |
| gold_other_llm_hybrid | exact | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | NA | 0.958333 |
| gold_other_llm_hybrid | soft-difflib | 0.127976 | 0.027778 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 | 0.958333 |
| gold_other_llm_hybrid | soft-embedding | 0.136872 | 0.055556 | 0.125000 | 0.125000 | 0.125000 | 1.000000 | 0.125000 | 0.958333 |

## Verdicts

| llm_beats_v2_outdomain_meanJ | llm_unblocks_relaxed_outdomain | llm_goldother_ceiling_outdomain | llm_indomain_no_regression |
| --- | --- | --- | --- |
| 0.000000 | 1.000000 | 0.180556 | 1.000000 |

## Recommendation

LLM entities move true-blind relaxed rows off zero; compare open vs hybrid on a fresh blind split before adoption.