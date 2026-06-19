"""
LLM route extraction runner skeleton.

This file intentionally does not include provider-specific API code.
Add your preferred provider call inside call_llm(prompt).

Inputs:
    data/gold/gold_segments_template.csv

Output:
    data/outputs/llm_route_labels.csv
"""
import argparse, json
from pathlib import Path
import pandas as pd

def call_llm(prompt: str) -> dict:
    # TODO: plug in OpenAI / Anthropic / Gemini / local model here.
    # Must return a dict matching prompts/llm_route_extractor_prompt.md
    raise NotImplementedError("Add your LLM provider call here.")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--segments", required=True)
    ap.add_argument("--prompt", default="prompts/llm_route_extractor_prompt.md")
    ap.add_argument("--out", default="data/outputs/llm_route_labels.csv")
    args = ap.parse_args()

    seg = pd.read_csv(args.segments)
    template = Path(args.prompt).read_text(encoding="utf-8")
    rows = []

    for _, row in seg.iterrows():
        prompt = template.replace("{{PASSAGE}}", str(row.text))
        try:
            result = call_llm(prompt)
        except NotImplementedError:
            result = {
                "role": "",
                "entities": [],
                "operative_status": "",
                "relation": "",
                "confidence": 0,
                "rationale": "LLM provider not configured"
            }
        rows.append({**row.to_dict(), **{
            "llm_role": result.get("role", ""),
            "llm_entities": "|".join(result.get("entities", [])),
            "llm_operative_status": result.get("operative_status", ""),
            "llm_relation": result.get("relation", ""),
            "llm_confidence": result.get("confidence", 0),
            "llm_rationale": result.get("rationale", ""),
        }})

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()