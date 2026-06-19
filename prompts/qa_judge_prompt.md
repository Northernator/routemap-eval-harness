You are an evaluator model.

Judge whether the answer is grounded in the provided source passages.

Return strict JSON:

{
  "correctness_0_2": 0,
  "completeness_0_2": 0,
  "hallucination_0_2": 0,
  "uses_required_sources": true,
  "missing_sources": [],
  "notes": "brief explanation"
}

Query:
{{QUERY}}

Required source ids:
{{REQUIRED_SOURCE_IDS}}

Retrieved source passages:
{{SOURCES}}

Answer:
{{ANSWER}}