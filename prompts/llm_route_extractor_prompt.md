You are a route extraction model.

Given a document passage, extract a structured route label.

Return strict JSON:

{
  "role": "DEFINE|CLAIM|METHOD|RESULT|LIMITATION|NEXT_STEP|EXAMPLE|BACKGROUND|MODIFY|EXCEPT|SUPPORTS|CONTRADICTS|DEPENDS_ON",
  "entities": ["..."],
  "operative_status": "OPERATIVE|BACKGROUND|EXAMPLE|REJECTED_DRAFT|HISTORICAL|NON_BINDING|UNKNOWN",
  "relation": "defines|modifies|excepts|supports|contradicts|depends_on|causes|measures|reports|limits|next_step|background_to",
  "confidence": 0.0,
  "rationale": "one sentence"
}

Passage:
{{PASSAGE}}