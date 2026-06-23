# Natural Blind R6 Prediction Provenance

- natural split: `data\v1\heldout\natural_language_blind\natural_language_blind_gold.csv`
- rows: 99
- combined_v3: fixed boundary-augmented role model selected before this test; ontology_v1 entities; combined_v3 status/relation/answer rules
- D: Ollama llama3.1 role/status/relation; ontology_v1 entities; combined_v3 answer relevance
- R6: unchanged coarse_3 guard between D/Ollama role and combined_v3 role; ontology_v1 entities; combined_v3 status/relation/answer
- gold labels were not used to generate or alter predictions
