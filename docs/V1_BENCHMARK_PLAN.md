# RouteMap v1.0 Benchmark Plan

## Goal

Build the first serious human-gold benchmark for testing whether RouteMap route labels improve retrieval, source grounding, and comparison reduction against keyword, neural embedding, and LLM route-extraction baselines.

## Target Dataset

- Target document count: 25-50 real documents.
- Target segment count: 1,000-2,500 annotated segments.
- Target QA query count: 150-300 human-written questions.
- Minimum per-document coverage: at least 10 labeled segments and 3 QA queries for every included document.
- Preferred mix: policy, contracts, research notes, technical design docs, and dependency/change documents.

## Annotation Rules

- Label passage role by the job the passage performs, not only topic.
- Use only the route schema roles and relations in `configs/route_schema.json`.
- Fill every required label: `gold_role`, `gold_entities`, `gold_operative_status`, `gold_relation`, and `gold_answer_relevant`.
- Use `gold_entities` as `|`-separated normalized entity names.
- Use `gold_answer_relevant = 1` only when the segment is directly needed for at least one benchmark answer.
- Prefer conservative labels when unsure; write uncertainty in `notes`.
- Every completed file must pass `python src/validate_gold_labels.py --gold <file>`.

## QA Rules

- Each QA target must include one natural language `query`, at least one `gold_required_segment_ids` value, a concise `gold_answer`, and optional `notes`.
- Required source segment ids must exist in the gold segment file.
- Questions should test route-sensitive distinctions such as definitions vs examples, operative clauses vs background, modifications, exceptions, limitations, and next steps.
- Include near-miss questions where keyword overlap alone may retrieve background or illustrative passages.
- Every completed QA file must pass `python src/validate_qa_targets.py --qa <file> --gold-segments <gold-segments>`.

## Acceptance Criteria

- At least 1,000 validated human-gold segments.
- At least 150 validated QA questions.
- Each target role has at least 50 examples where the corpus supports it.
- Batch evaluation completes with `python src/run_batch_eval.py`.
- `run_summary.md`, `report.html`, and all charts are generated.
- RouteMap must be compared against keyword and neural embeddings when optional neural dependencies are available.
- Known limitations and excluded documents are documented.

## Metrics

- Retrieval: Hit@K, MRR, comparisons/query, comparison reduction percentage.
- Route extraction: role accuracy, operative-status accuracy, relation accuracy, entity exact match, entity Jaccard, invalid output count, confusion matrices.
- QA: source hit, all required sources used, answer contains gold terms, simple hallucination flag, correctness proxy, completeness proxy.
- Reporting: timestamped run manifest, Markdown summary, HTML report, and chart PNGs.

## Limitations

- v1.0 uses human-gold labels but still relies on deterministic proxy QA judging unless external evaluators are added.
- Stub LLM labels copy gold labels and only validate pipeline mechanics.
- Neural embedding results depend on local model availability and first-run downloads.
- Human annotation consistency will need adjudication if multiple annotators participate.
- The first benchmark is expected to be small enough for rapid iteration, not final statistical proof.
