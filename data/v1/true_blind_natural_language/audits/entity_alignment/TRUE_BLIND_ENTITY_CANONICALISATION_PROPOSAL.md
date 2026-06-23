# True-Blind Entity Canonicalisation Proposal

Status: PROPOSED ONLY. These files are not evaluator inputs and must not replace true_blind_gold.csv or prediction CSVs.

The safe automated proposal is delimiter canonicalisation only: parse JSON-list gold entities into semicolon-delimited strings while leaving ontology mapping for human review.

- proposed gold: `data\v1\true_blind_natural_language\audits\entity_alignment\proposed\true_blind_gold_entities_canonicalised_PROPOSED.csv`
- proposed R6 predictions: `data\v1\true_blind_natural_language\audits\entity_alignment\proposed\R6_true_blind_predictions_entities_canonicalised_PROPOSED.csv`
- low-confidence cooccurrence aliases are listed separately and are not applied.

Recommended next test: human-review candidate aliases or expand ontology_v1, save as a named ablation input, then rerun metrics as an ablation report rather than replacing the true-blind benchmark.
