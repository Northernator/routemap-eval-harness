# PowerShell Provider Commands

Run from:

```powershell
Set-Location 'C:\dev\RouteMap\routemap_eval_harness\routemap_eval_harness'
```

## Generate Requests

```powershell
python src/generate_llm_extraction_requests.py --in data/v1/gold/model_test_fresh_adjudicated_role.csv --out data/v1/llm_eval/requests/fresh_adjudicated_requests.jsonl --limit 0
```

## Dry-Run Manual Preview

```powershell
python src/run_live_llm_provider.py --provider manual_copy --requests data/v1/llm_eval/requests/fresh_adjudicated_requests.jsonl --out data/v1/llm_eval/outputs/manual_outputs_preview.jsonl --limit 5 --dry-run
```

## Ollama Local Test

```powershell
python src/run_live_llm_provider.py --provider ollama_http --model llama3.1 --requests data/v1/llm_eval/requests/fresh_adjudicated_requests.jsonl --out data/v1/llm_eval/outputs/ollama_llama31_outputs.jsonl --limit 5 --sleep-seconds 0.5 --execute
```

## Validate And Evaluate Provider Output

```powershell
python src/evaluate_provider_output_file.py --provider-output data/v1/llm_eval/outputs/ollama_llama31_outputs.jsonl --provider-name ollama_llama31
```

## Compare Providers

```powershell
python src/compare_llm_provider_runs.py --reports-dir data/v1/llm_eval/reports --out data/v1/llm_eval/reports/LLM_PROVIDER_COMPARISON.md
```
