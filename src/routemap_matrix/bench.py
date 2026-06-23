"""Needle-in-haystack long-context KV-routing benchmark. GPU run (CPU works on a tiny model).

Honest framing: peak VRAM and needle accuracy are the result on this hardware; tokens/sec is INDICATIVE
only (no FlashAttention on Maxwell). The `dense` policy is the correctness anchor.
"""
from __future__ import annotations
import json
from pathlib import Path

from .metrics import answer_hit

FILLER = "The committee reviewed the routine quarterly logistics report without further comment. "


def build_needle(tok, *, context_chars=6000, secret="BLUE-MARLIN-42", seed=7):
    needle = f"IMPORTANT: the secret access code is {secret}. "
    body = FILLER * max(1, context_chars // len(FILLER))
    mid = len(body) // 2
    prompt = (body[:mid] + needle + body[mid:]
              + "\n\nQuestion: What is the secret access code?\nAnswer: The secret access code is")
    ids = tok(prompt, return_tensors="pt").input_ids
    return ids, secret


def run(*, root=".", model_name=None, context_chars=6000, budgets=(64, 128, 256),
        policies=("dense", "recency_window", "h2o", "routemap"), max_new_tokens=12,
        n_sink=4, out=None, seed=7, efficient=False, obs_window=32):
    from .model import load_model
    from .decode import manual_generate, generate_efficient
    from .importance import token_class_priors
    model, tok, device = load_model(model_name, efficient=efficient)
    ids, secret = build_needle(tok, context_chars=context_chars, seed=seed)
    prompt_len = int(ids.shape[1])
    toks = tok.convert_ids_to_tokens(ids[0].tolist())
    priors = token_class_priors([t.lstrip("Ġ▁ ") for t in toks])
    rows = []
    for policy in policies:
        budget_set = [prompt_len] if policy == "dense" else list(budgets)
        for budget in budget_set:
            gen = generate_efficient if efficient else manual_generate
            kw = {"obs_window": obs_window} if efficient else {}
            r = gen(model, tok, ids, policy=policy, budget=int(budget), n_sink=n_sink,
                    max_new_tokens=max_new_tokens, device=device, priors=priors, eos_id=tok.eos_token_id, **kw)
            rows.append({"policy": policy, "budget": int(budget), "prompt_len": prompt_len,
                         "needle_hit": bool(answer_hit(r["text"], secret)),
                         "peak_vram_bytes": r["peak_vram_bytes"], "final_cache_len": r["final_cache_len"],
                         "guard_triggers": r["guard_triggers"], "false_prunes": r["false_prunes"],
                         "answer": r["text"][:80]})
    result = {"model": model_name or "auto", "device": device, "efficient": efficient, "prompt_len": prompt_len,
              "context_chars": context_chars, "rows": rows}
    if out:
        Path(out).mkdir(parents=True, exist_ok=True)
        Path(out, "matrix_kv_report.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        Path(out, "matrix_kv_report.md").write_text(report(result), encoding="utf-8")
    return result


def report(result):
    lines = ["# KV-Cache Importance Routing (routemap_matrix)", "",
             f"Model: `{result['model']}` on `{result['device']}` | prompt_len {result['prompt_len']}", "",
             "Memory + needle accuracy are the result; tokens/sec is INDICATIVE only "
             "(no FlashAttention on Maxwell). `dense` is the correctness anchor.", "",
             "| policy | budget | needle_hit | peak_VRAM_MB | final_cache_len | guard_triggers | false_prunes |",
             "| --- | ---: | :---: | ---: | ---: | ---: | ---: |"]
    for r in result["rows"]:
        lines.append(f"| {r['policy']} | {r['budget']} | {'Y' if r['needle_hit'] else 'n'} | "
                     f"{r['peak_vram_bytes'] / 1e6:.1f} | {r['final_cache_len']} | "
                     f"{r['guard_triggers']} | {r['false_prunes']} |")
    return "\n".join(lines)

__all__ = ["run", "report", "build_needle"]
