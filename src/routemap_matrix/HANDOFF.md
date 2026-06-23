# Phase 6 GPU handoff — KV-cache importance routing (routemap_matrix)

**Goal:** run the memory-efficient variant on a capable GPU to measure the real **memory-vs-quality** trade-off
that a GTX 980M (Maxwell, no FlashAttention) cannot show. On Maxwell the quadratic attention materialisation
dominated memory and hid the KV-cache win; on Ampere-class hardware with SDPA/FlashAttention that goes away.

## Hardware needed
- NVIDIA **Ampere or newer** (RTX 30-series / 40-series, A-series, etc.) — anything with working SDPA/FlashAttention.
- 8 GB+ VRAM. (Not Maxwell/Pascal — those are why we're handing this off.)

## Setup (on the GPU box)
```powershell
# pull the repo, then from the harness root:
cd <repo>\routemap_eval_harness\routemap_eval_harness
$env:PYTHONPATH='src'
# your GPU is not Maxwell, so use a current torch build for your CUDA (no wheel pinning needed):
pip install torch --index-url https://download.pytorch.org/whl/cu124   # or cu121 / latest for your CUDA
pip install "transformers>=4.44" accelerate
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

## Run
```powershell
# 1) self-check (CPU, tiny model, no download) — both code paths; must print SELFCHECK PASS: True
python -m routemap_matrix selfcheck

# 2) the memory-efficient run (the point of this handoff):
python -m routemap_matrix run --efficient --context-chars 8000 --budgets 64,128,256,512

# 3) (optional) stress the KV cache with a much longer context — where the memory win should be clearest:
python -m routemap_matrix run --efficient --context-chars 30000 --budgets 128,256,512,1024

# 4) (optional, for contrast) the non-efficient path that hit the wall on Maxwell:
python -m routemap_matrix run --context-chars 8000 --budgets 64,128,256
```
Auto-picks TinyLlama-1.1B (or Qwen2.5-0.5B if <6 GB free), fp16, SDPA when `--efficient`.

## What to look for
- `dense` row is the correctness anchor: `needle_hit` should be **Y**.
- With `--efficient`, the eviction policies (`recency_window`, `h2o`, `routemap`) should now show **lower
  `peak_VRAM_MB` than dense** — that's the memory win the 980M couldn't produce.
- `routemap` / `h2o` should retrieve the needle (**Y**) at budgets where `recency_window` does not — that's the
  importance signal doing real work (the observation window keeps the needle).
- **Headline = the peak-VRAM reduction (dense vs routemap) at the smallest budget that still holds the needle**,
  plus where routemap beats recency on the needle-vs-budget curve.

## What to send back
The full run table(s), plus: GPU name + VRAM, and `torch` / `transformers` versions. That's enough to fold the
result into the record and the architecture report.

## Honest expectations
This completes the route-and-validate story on the attention layer: a memory-vs-quality trade-off with a guard
and an audit trail. It demonstrates the *mechanism* — it is **not** expected to beat tuned, published KV methods
(H2O, SnapKV). Report whichever way it falls; a clean characterization is the goal.

## If eviction policies still miss the needle (needle_hit n) while dense is Y
That isolates one thing: the **RoPE position handling after eviction** (see the `decode.py` docstring — kept keys
keep their original rotation; the new query is rotated at its true index via `position_ids`). Send the table and
it can be tuned per model; the route/validate **logic** is already CPU-verified (`rm_test_matrix.py`, 9/9).
