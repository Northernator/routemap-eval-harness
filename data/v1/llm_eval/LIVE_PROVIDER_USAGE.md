# Live Provider Usage

## Safety

Live providers are optional. The default RouteMap LLM harness is offline and file-based. Do not use the locked fresh test for prompt tuning: generate requests once, run the provider once, save outputs, validate them, and evaluate fairly.

Never write API keys to disk. Provider scripts read keys only from environment variables.

## Supported Provider Modes

- `manual_copy`: prints request/prompt information for manual copy/paste workflows.
- `ollama_http`: calls a local Ollama HTTP server.
- `openai_http`: calls OpenAI Chat Completions over HTTPS using standard-library `urllib`.
- `anthropic_http`: calls Anthropic Messages over HTTPS using standard-library `urllib`.
- `custom_command`: sends each prompt to a local command over stdin and records stdout.

## Environment Variables

- `OPENAI_API_KEY`: required for `openai_http`.
- `ANTHROPIC_API_KEY`: required for `anthropic_http`.
- `OLLAMA_HOST`: optional for `ollama_http`; defaults to `http://localhost:11434`.

## Output Format

Provider outputs are JSONL. Use Format A or Format B from `data/v1/llm_eval/LLM_OUTPUT_FORMAT.md`.

The live runner writes accepted wrapper JSONL records containing:

- `segment_id`
- `provider`
- `model`
- either `extraction` or `raw_response`

Invalid provider responses should be stored as `raw_response` and caught by validation.
