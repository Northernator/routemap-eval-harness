# routemap_matrix — KV-cache importance routing (Phase 6, research-only)

Composes the RouteMap route-and-validate loop onto the attention/KV layer: score each KV position by
**accumulated attention mass + recency + the routemap_token class prior**, keep a per-layer budget, evict
the rest, and run a **guard** (confidence + false-prune tracking) so degradation is surfaced, not silent.

## Honest scope (GTX 980M / Maxwell)
- **No FlashAttention** on Maxwell — runs eager attention. **Peak VRAM** and **needle accuracy** are the
  result; **tokens/sec is indicative only** (weak baseline, dated GPU).
- This is a **research-only mechanism demo**, per the roadmap's own clause. Lead with memory + quality.
- `dense` policy is the correctness anchor; `recency_window` and `h2o` are baselines; `routemap` is ours.

## Run
```
pip install "transformers>=4.44" accelerate
python -m routemap_matrix selfcheck                 # CPU, tiny random model, no download — validates the loop
python -m routemap_matrix run --context-chars 8000 --budgets 64,128,256
```
Auto-picks Qwen2.5-0.5B-Instruct (or TinyLlama-1.1B if >=6GB free), fp16 on CUDA.

## Verified vs. to-run
The route/validate **core** (importance, policies, guard, kv eviction, metrics) is unit-verified on CPU.
The torch decode loop + peak-VRAM numbers run on the GPU. Known risk: KV-eviction **position handling**
(`decode.py` docstring) — if eviction policies score ~0 needle accuracy while `dense` is high, that's the
knob to tweak per model.
