# Model Adapters

`src/routemap_harness/adapters.py` defines the harness model-call contract:

```python
model_fn(
    prompt: str,
    *,
    model_ref: str,
    runtime: str = "ollama",
    auth_mode: str = "local",
    timeout: int = 60,
    strict_model: bool = False,
    fallbacks: list[str] | None = None,
) -> str
```

The return value is plain text. Harness adapters return a `ModelResponse`, a `str` subclass with attached call metadata.

## Runtime Split

| Runtime | Auth mode | Status | Notes |
| --- | --- | --- | --- |
| `ollama` | `local` | supported baseline | Uses local `http://127.0.0.1:11434/api/generate`, temperature 0. |
| `openai` | `api_key` | optional | Requires `OPENAI_API_KEY`; uses HTTPS API through stdlib `urllib`. |
| `anthropic` | `api_key` | optional | Requires `ANTHROPIC_API_KEY`; uses HTTPS API through stdlib `urllib`. |
| `codex` | OAuth/CLI | experimental stub | Disabled by default. Do not bypass provider terms. |
| `claude-cli` | OAuth/CLI | experimental stub | Disabled by default. Do not bypass provider terms. |
| `gemini-cli` | OAuth/CLI | experimental stub | Disabled by default. Do not bypass provider terms. |

## Audit Metadata

Each adapter call records:

- `provider`
- `model_ref`
- `runtime`
- `auth_mode`
- `fallback_used`
- `latency_ms`
- `tokens`
- `cost_usd`
- `run_id`
- `session_id`

Repair decisions embed this under `validator_record.model_call`, and copy `model`, `tokens`, and `cost_usd` to the optional top-level harness audit fields when present.

## Reproducibility Pinning

When `ROUTEMAP_RUN_ID` or `ROUTEMAP_SESSION_ID` is set, the first successful provider/runtime/model selection is pinned for that ID inside the process. Later calls in the same run/session reuse the pinned runtime and model so benchmarks do not silently drift across providers.

`strict_model=True` disables fallback behavior and raises visibly if the requested runtime/model fails or is unavailable.
