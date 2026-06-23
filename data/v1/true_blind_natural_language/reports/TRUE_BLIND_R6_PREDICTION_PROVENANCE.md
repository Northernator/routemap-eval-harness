# Heldout R6 Generalisation Split Provenance

- source split: `data\v1\true_blind_natural_language\annotation\true_blind_gold_frozen.csv`
- split status: existing test split, not newly sampled
- row selection: all rows from `expanded_test_v2.csv`
- evaluated rows requested: 72
- calibration leakage check: no overlap with `HELDOUT2` calibration segment_ids
- gold files modified: no
- Ollama model: `llama3.1:latest` via local HTTP endpoint
- Ollama raw output status: generated_or_resumed_raw_outputs
- combined_v3 boundary-role model: `base_plus_boundary_train` / `centroid`
- selected boundary prediction column: `pred_base_plus_boundary_train_centroid`
- selected boundary calibration accuracy: 0.532
- R6 rule: unchanged coarse_3 guard between D/Ollama role and combined_v3 role; ontology_v1 entities; combined_v3 answer/status/relation
