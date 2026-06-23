# Ollama llama3.1 Provider Failure Note

## What Happened

The saved `ollama_llama31_outputs_full.jsonl` file did not contain real model completions. Each row contained a `raw_response` JSON object with a connection-refused error from the local Ollama HTTP endpoint.

## Why Previous Metrics Are Invalid

Before this patch, raw error JSON was parsed as a generic object and normalized into default extraction values:

- `role = BACKGROUND`
- `entities = []`
- `operative_status = DESCRIPTIVE`
- `relation = sets_context`
- `answer_relevant = MAYBE`

That made provider failures look like valid but low-quality model outputs. The previous `Role accuracy: 0.127` and `Entity Jaccard: 0.000` should not be interpreted as llama3.1 semantic performance.

## Patched Validation Result

The patched validator reclassifies the existing file as:

- Requests: 79
- Outputs: 79
- Matched: 79
- Valid outputs: 0
- Provider/error outputs: 79
- Invalid outputs: 79

The patched evaluation has:

- Evaluated rows: 0
- Missing/invalid rows: 79

## Fix Ollama Before Rerunning

Check Ollama is running:

```powershell
curl http://localhost:11434/api/tags
```

Start Ollama if installed:

```powershell
ollama serve
```

Check model exists:

```powershell
ollama list
```

Pull model if needed:

```powershell
ollama pull llama3.1
```

Dry-run:

```powershell
python src/run_live_llm_provider.py --provider ollama_http --model llama3.1 --requests data/v1/llm_eval/requests/fresh_adjudicated_requests.jsonl --out data/v1/llm_eval/outputs/ollama_test.jsonl --limit 1 --dry-run
```

Live 1-row smoke:

```powershell
python src/run_live_llm_provider.py --provider ollama_http --model llama3.1 --requests data/v1/llm_eval/requests/fresh_adjudicated_requests.jsonl --out data/v1/llm_eval/outputs/ollama_smoke_1.jsonl --limit 1 --execute
```

Validate smoke:

```powershell
python src/validate_llm_extraction_outputs.py --requests data/v1/llm_eval/requests/fresh_adjudicated_requests.jsonl --outputs data/v1/llm_eval/outputs/ollama_smoke_1.jsonl --report data/v1/llm_eval/reports/ollama_smoke_1_validation.md
```
