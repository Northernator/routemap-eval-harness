# LLM Output Format

Save provider outputs as JSONL, one JSON object per line. Two formats are accepted.

## Format A - Clean Extraction

```json
{
  "segment_id": "HELDOUT2_S0001",
  "provider": "manual",
  "model": "gpt-or-claude-or-ollama",
  "extraction": {
    "role": "BACKGROUND",
    "entities": ["AI safety evaluation", "policy context"],
    "operative_status": "DESCRIPTIVE",
    "relation": "sets_context",
    "answer_relevant": "NO",
    "rationale": "Source context for policy framing."
  }
}
```

## Format B - Raw Response Wrapper

```json
{
  "segment_id": "HELDOUT2_S0001",
  "provider": "manual",
  "model": "gpt-or-claude-or-ollama",
  "raw_response": "{\"role\":\"BACKGROUND\",\"entities\":[\"AI safety evaluation\"],\"operative_status\":\"DESCRIPTIVE\",\"relation\":\"sets_context\",\"answer_relevant\":\"NO\",\"rationale\":\"Context row.\"}"
}
```

Rules:

- `segment_id` must match a request `segment_id`.
- `extraction` is preferred.
- `raw_response` is allowed if it contains parseable JSON.
- `entities` may be a list or a semicolon-separated string; the validator normalizes them.
- Invalid outputs are reported, not silently ignored.
