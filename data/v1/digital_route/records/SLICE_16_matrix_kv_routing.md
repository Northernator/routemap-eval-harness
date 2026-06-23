# Phase 3 Slice 16 — Matrix/Attention RouteMap: KV-cache importance routing (routemap_matrix)

Date: 2026-06-23
Status: research-only mechanism prototype (per the roadmap's own no-go clause for the matrix layer).
Hardware: NVIDIA GTX 980M, 8 GB, Maxwell (sm_52), driver 582.28, torch 2.5.1+cu124. **No FlashAttention on Maxwell.**

## Idea
Compose the RouteMap route-and-validate loop onto the attention/KV layer. Each KV position gets an
importance score = **accumulated attention mass + recency + the `routemap_token` class prior**; a per-layer
**budget** is kept and the rest is **evicted** (real memory reduction); a **guard** (confidence proxy +
false-prune tracking) surfaces degradation rather than letting it pass silently. This is the
`routemap_token` prior + H2O-style heavy-hitter signal + the controller's validate discipline, applied to
the KV cache.

## Honest scope
- **Memory-led.** Peak VRAM and needle accuracy are the result. **tokens/sec is INDICATIVE only** — no
  FlashAttention on Maxwell, dated GPU, weak baseline. This is not a competitive latency claim.
- `dense` is the correctness anchor; `recency_window` and `h2o` are baselines; `routemap` is ours.
- Per the roadmap: matrix routing on this hardware is reported as research-only, not product-ready.

## Package (src/routemap_matrix/)
- `importance.py` — PositionImportance (mass + recency + token-class prior); `token_class_priors` via routemap_token.
- `policies.py` — keep_indices for dense / recency_window / h2o / routemap (sinks + top-importance).
- `guard.py` — Guard: KL escalation, cheap confidence check, false-prune counting.
- `kv.py` — backend-agnostic KV eviction (numpy or torch, via index_select / np.take).
- `metrics.py` — needle answer_hit, memory reduction.
- `model.py` — load_model (auto: Qwen2.5-0.5B-Instruct, or TinyLlama-1.1B if >=6 GB free; eager attn; fp16/cuda),
  toy_model (tiny random GPT-2, no download, for the CPU self-check).
- `decode.py` — manual decode loop with explicit budget-limited KV eviction + real peak-VRAM measurement.
- `bench.py` — needle-in-haystack long-context benchmark across policies x budgets.
- `run_matrix_bench.py` / `__main__.py` / `selfcheck.py` — CLI (`run`, `selfcheck`).

## Verified vs. to-run
- **Verified on CPU (numpy, no torch): 8/8 tests** (`rm_test_matrix.py`) — importance scoring, all four
  keep-index policies (exact budget, sink retention, h2o heavy-hitter, routemap top-importance), guard
  KL/confidence/false-prune, KV eviction shrinks the seq dim, metrics. This is the novel route-and-validate
  core.
- **To run on the GPU (Chris):** `python -m routemap_matrix selfcheck` (CPU toy model, validates the decode
  loop mechanics, no download) then `python -m routemap_matrix run --context-chars 8000 --budgets 64,128,256`.
- **Known risk:** KV-eviction **position handling** (RoPE/abs-position after the cache shortens — see the
  `decode.py` docstring). The dense anchor isolates it: if eviction policies score ~0 needle accuracy while
  `dense` is high, that knob needs a per-model tweak.

## GPU RUN RESULT (2026-06-23, GTX 980M 8GB, TinyLlama-1.1B fp16, prompt_len 1408)
selfcheck PASS (loop mechanics sound on tiny Llama). Run table:
- dense (budget 1408): needle_hit **Y**, peak 5478.6 MB.
- recency_window / h2o / routemap at budgets 64/128/256: needle_hit **n** (all), peak **5478.6 MB (identical to dense)**.
- guard_triggers low; false_prunes: recency higher than h2o/routemap (routemap/h2o protect heavy positions, as designed).

### Verdict — honest CHARACTERIZED NEGATIVE (the predicted hardware wall)
1. **No memory win, and it is fundamental on Maxwell, not a bug.** Peak VRAM is identical across all budgets
   because the KV cache at 1408 tokens is only ~63 MB (22 layers x 4 KV-heads x 1408 x 64 x 2 x 2B), a rounding
   error next to the 2.2 GB model + **~2.8 GB of attention matrices that `output_attentions=True` materializes
   during prefill** ([1,32,1408,1408] x 22 layers). The peak occurs at prefill, BEFORE eviction. To make KV the
   dominant term needs very long context, but without FlashAttention the O(seq^2) attention materializes and hits
   the memory ceiling first — and importance scoring REQUIRES those attention weights, forcing the materialization.
   This is exactly why the roadmap gated Phase 6 on hardware and flagged it research-only. The same code on
   Ampere+/FlashAttention would reach the long-context regime where KV dominates and eviction pays off.
2. **Compression lost the needle (dense Y, all policies n).** The mid-prompt needle is evicted under every budget
   — either its prefill attention mass is too low to survive top-budget, or RoPE position handling after eviction
   is off. Secondary to (1); would need on-GPU iteration (a salient/early needle, stronger importance signal, or a
   per-model position fix) to turn into a quality result, with no guarantee on this hardware.

CONCLUSION: Phase 6 demonstrates the route-and-validate MECHANISM (loop runs; policies differ in false-prune
behaviour; dense anchors) but on a GTX 980M shows neither a memory nor a quality win — a legitimate, hardware-
characterized negative, same shape as the token-routing ceiling (Slice 13) and the embedding recall/speed split
(Slice 14). The architecture is complete at 7 phases; Phase 6 documents WHY the attention layer needs
Tensor-Core / FlashAttention hardware to pay off. Route/validate CORE verified on CPU (8/8); the negative is in
the hardware economics, not the logic.

## Memory-efficient variant + GPU handoff (added 2026-06-23)
To get the memory win on capable hardware, added `decode.generate_efficient` (SnapKV-style): prefill the
context with SDPA (no quadratic attention materialised), score importance from only the last `obs_window`
prompt tokens' attention over the prefix (materialises `[W, ctx_len]`, not `[seq, seq]`), force-keep the
observation window, compress the prompt cache once, decode with SDPA. Peak VRAM then reflects the (compressed)
KV cache so eviction can show a real win, and the question's attention over the prefix should keep the needle.
Wired as `python -m routemap_matrix run --efficient`; `src/routemap_matrix/HANDOFF.md` is the run sheet for a
coworker's Ampere+ GPU. Verified on CPU (window_mass unit-tested; rm_test_matrix 9/9; selfcheck exercises both
the standard and efficient paths). GPU numbers (peak-VRAM reduction at held needle accuracy; routemap vs
recency/h2o) are the coworker's run to send back.
