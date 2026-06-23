# Natural Language Blind Split Provenance

- output: `data\v1\heldout\natural_language_blind\natural_language_blind_gold.csv`
- source file: `data\v1\gold\v1_full_extraction_gold_v1_noleak.csv`
- split creation status: created
- random seed: 20260622
- final row count: 99
- segment ID pattern: DOC0001, DOC0002, DOC0003, DOC0004, DOC0005, DOC0006, DOC0007, DOC0008, DOC0009, DOC0010
- exclusion rules: removed any segment_id present in HELDOUT2 calibration or EXPAND boundary-stress heldout sets
- true blind status: constructed pseudo-blind split, not a true blind split
- why it qualifies: natural route-note document segments, full-extraction compatible, larger than expanded_test_v2, distinct from HELDOUT2 calibration and EXPAND boundary-stress rows
- limitations: source is historical v1 train/dev-allowed corpus; gold fields are first-pass/locked benchmark labels rather than fresh independent adjudication; this should support promotion confidence but not replace a new externally collected blind set
- gold files modified: no
