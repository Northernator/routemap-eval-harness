# RouteMap LLM Evaluation Workflow

This directory supports offline LLM/provider evaluation without requiring API keys or SDKs.

1. Generate request JSONL files with `src/generate_llm_extraction_requests.py`.
2. Send request prompts to an LLM manually or through a separate provider runner.
3. Save outputs as JSONL in `outputs/`.
4. Validate outputs with `src/validate_llm_extraction_outputs.py`.
5. Convert valid outputs to prediction CSV with `src/ingest_llm_extraction_outputs.py`.
6. Evaluate predictions with `src/evaluate_llm_extraction_predictions.py`.
7. Compare runs with `src/compare_llm_provider_runs.py`.

Subdirectories:

- `requests/`: generated JSONL prompts for full benchmark runs.
- `outputs/`: manually saved provider JSONL outputs.
- `predictions/`: normalized prediction CSVs.
- `reports/`: validation, evaluation, and comparison reports.
- `samples/`: small request/output fixtures for testing the offline pipeline.

No script in this workflow calls an external API.
