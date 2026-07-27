# TRUE_BLIND_GOLD_README

Generated file: `true_blind_gold.csv`

Rows: 72
Segments: TB001–TB072
Source: newly generated natural-language route-note style segments, not copied from existing RouteMap gold/test/calibration rows.

Important honesty note:
- This is an **assistant-generated external blind test file** for the repository, not a human-annotated gold file.
- It is useful for a quick blind-ish pipeline run because the rows are new to the local repo.
- For the strongest scientific result, replace or review these labels manually before treating the metrics as publication-grade.

Suggested placement:

`data/v1/true_blind_natural_language/annotation/true_blind_gold.csv`

Columns included:
- `segment_id`
- `source_doc`
- `source_topic`
- `segment_index`
- `route_question`
- `segment_text`
- non-prefixed labels: `role`, `entities`, `operative_status`, `relation`, `answer_relevance`
- gold-prefixed labels: `gold_role`, `gold_entities`, `gold_operative_status`, `gold_relation`, `gold_answer_relevance`

Label caveat:
If `validate_true_blind_gold.py` rejects enum values, use Codex to map the label strings to the repo's exact allowed enum names. The included labels use these values:

Roles:
`DEFINE`, `BACKGROUND`, `METHOD`, `LIMITATION`, `RESULT`, `NEXT_STEP`, `MODIFY`, `EXCEPT`, `EXAMPLE`

Operative status:
`OPERATIVE`, `NON_OPERATIVE`

Relations:
`SUPPORTS`, `CONTEXT`, `CONSTRAINS`, `RESULT_OF`, `NEXT_STEP`, `MODIFIES`, `EXCEPTS`, `EXEMPLIFIES`

Answer relevance:
`RELEVANT`

Entity format:
JSON array strings, e.g. `["CivicAid Permit Triage", "council service requests"]`.
