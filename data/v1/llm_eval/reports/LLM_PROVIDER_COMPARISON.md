# LLM Provider Comparison

## Local Baselines

| baseline | score |
|---|---:|
| best local fine_8 role | 0.532 |
| ontology_v1 entity Jaccard | 0.506 |
| combined_v3 strict | 0.051 |
| combined_v3 relaxed_1 | 0.253 |
| combined_v3 relaxed_2 | 0.354 |
| combined_v3 relaxed_3 | 0.443 |

## Provider Runs

| report | role accuracy | entity Jaccard | strict | relaxed_1 | relaxed_2 | relaxed_3 |
|---|---:|---:|---:|---:|---:|---:|
| ollama_llama31_5_evaluation.md | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| ollama_llama31_5_v2_evaluation.md | 1.000 | 0.383 | 0.000 | 0.200 | 0.200 | 0.200 |
| ollama_llama31_full_evaluation.md | 0.127 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| ollama_llama31_full_v2_evaluation.md | 0.595 | 0.389 | 0.013 | 0.127 | 0.127 | 0.127 |
| sample_evaluation.md | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |