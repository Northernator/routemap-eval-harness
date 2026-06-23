"""Manual decode loop with explicit, budget-limited KV-cache eviction (real memory savings).

Works directly on the model's live Cache object across transformers versions (no legacy round-trip).
RoPE / absolute position is kept correct after eviction by passing explicit position_ids = the TRUE
original sequence index (the kept keys retain their original rotation). `dense` is the anchor: if it
retrieves the needle but eviction policies do not, the position handling needs a per-model tweak.
"""
from __future__ import annotations
import numpy as np

from .importance import PositionImportance
from .policies import keep_indices
from .guard import Guard
from .importance import window_mass


def _num_layers(cache):
    if hasattr(cache, "key_cache") and getattr(cache, "key_cache"):
        return len(cache.key_cache)
    if hasattr(cache, "layers"):
        return len(cache.layers)
    return len(cache)


def _get_kv(cache, i):
    if hasattr(cache, "key_cache") and getattr(cache, "key_cache"):
        return cache.key_cache[i], cache.value_cache[i]
    if hasattr(cache, "layers"):
        return cache.layers[i].keys, cache.layers[i].values
    return cache[i][0], cache[i][1]


def _set_kv(cache, i, k, v):
    if hasattr(cache, "key_cache") and getattr(cache, "key_cache"):
        cache.key_cache[i] = k; cache.value_cache[i] = v
    elif hasattr(cache, "layers"):
        cache.layers[i].keys = k; cache.layers[i].values = v
    else:
        raise RuntimeError("legacy tuple cache is immutable; expected a DynamicCache")


def _seq_len(cache):
    k, _ = _get_kv(cache, 0)
    return k.shape[2]


def _evict(cache, keep_idx):
    import torch
    keep = [int(x) for x in keep_idx]
    for i in range(_num_layers(cache)):
        k, v = _get_kv(cache, i)
        idx = torch.as_tensor(keep, dtype=torch.long, device=k.device)
        _set_kv(cache, i, k.index_select(2, idx), v.index_select(2, idx))
    if hasattr(cache, "_seen_tokens"):
        cache._seen_tokens = len(keep)
    return cache


def _attn_received(attentions):
    import torch
    acc = None
    for la in attentions:
        m = la[0].mean(0).sum(0)  # [heads,q,k] -> mean heads -> [q,k] -> sum q -> [k]
        acc = m if acc is None else acc + m
    return (acc / len(attentions)).detach().to("cpu", dtype=torch.float32).numpy()


def _attn_last(attentions):
    import torch
    acc = None
    for la in attentions:
        a = la[0, :, -1, :].mean(0)  # [heads,k] -> [k]
        acc = a if acc is None else acc + a
    return (acc / len(attentions)).detach().to("cpu", dtype=torch.float32).numpy()


def _maybe_evict(cache, imp, guard, policy, budget, n_sink):
    L = _seq_len(cache)
    if policy == "dense" or L <= budget:
        return
    keep = keep_indices(policy, L, budget, importance=imp.scores(L), mass=imp.mass_scores(L), n_sink=n_sink)
    m = imp.mass_scores(L)
    guard.count_false_prunes(m / (m.sum() + 1e-9), keep, L)
    _evict(cache, keep)
    imp.mass = imp.mass[keep]; imp.prior = imp.prior[keep]


def manual_generate(model, tok, prompt_ids, *, policy="routemap", budget=128, n_sink=4,
                    max_new_tokens=24, device="cpu", priors=None, eos_id=None, conf_threshold=0.15):
    import torch
    mdev = next(model.parameters()).device
    prompt_ids = prompt_ids.to(mdev)
    prompt_len = int(prompt_ids.shape[1])
    on_cuda = device == "cuda" and torch.cuda.is_available()
    if on_cuda:
        torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()

    guard = Guard()
    priors = np.full(prompt_len, 0.5) if priors is None else np.asarray(priors, dtype=np.float64)[:prompt_len]
    imp = PositionImportance(priors)

    with torch.no_grad():
        out = model(prompt_ids, use_cache=True, output_attentions=True)
    cache = out.past_key_values
    imp.mass[:prompt_len] += _attn_received(out.attentions)[:prompt_len]
    true_pos = prompt_len
    _maybe_evict(cache, imp, guard, policy, budget, n_sink)

    generated, next_logits = [], out.logits[:, -1, :]
    eos_id = getattr(tok, "eos_token_id", None) if eos_id is None else eos_id
    for _ in range(max_new_tokens):
        probs = torch.softmax(next_logits.float(), dim=-1)[0].detach().cpu().numpy()
        guard.confidence_check(probs, conf_threshold)
        nxt = int(torch.argmax(next_logits, dim=-1))
        generated.append(nxt)
        if eos_id is not None and nxt == eos_id:
            break
        inp = torch.tensor([[nxt]], device=mdev)
        position_ids = torch.tensor([[true_pos]], device=mdev)
        with torch.no_grad():
            out = model(inp, past_key_values=cache, use_cache=True, output_attentions=True,
                        position_ids=position_ids)
        cache = out.past_key_values
        next_logits = out.logits[:, -1, :]
        true_pos += 1
        imp.extend(1)
        sa = _attn_last(out.attentions)
        imp.mass[:sa.shape[0]] += sa
        _maybe_evict(cache, imp, guard, policy, budget, n_sink)

    peak = 0
    if on_cuda:
        torch.cuda.synchronize(); peak = int(torch.cuda.max_memory_allocated())
    return {"text": tok.decode(generated, skip_special_tokens=True), "tokens": generated,
            "peak_vram_bytes": peak, "final_cache_len": _seq_len(cache), **guard.summary()}



def _window_layer_attn(attentions, ctx_len):
    """Per-layer head-averaged attention of the observation-window queries over the first ctx_len keys.
    Returns list of [W, ctx_len] numpy arrays (only this slice is reduced; bounded memory)."""
    import torch
    out = []
    for la in attentions:
        a = la[0].mean(0)            # [heads, W, K] -> mean heads -> [W, K]
        a = a[:, :ctx_len]           # keep only context keys
        out.append(a.detach().to("cpu", dtype=torch.float32).numpy())
    return out


def generate_efficient(model, tok, prompt_ids, *, policy="routemap", budget=128, n_sink=4,
                       obs_window=32, max_new_tokens=24, device="cpu", priors=None, eos_id=None):
    """Memory-efficient KV routing (the variant for capable GPUs / FlashAttention).

    SnapKV-style: prefill the context with SDPA (no quadratic attention materialised), then run only the
    last `obs_window` prompt tokens with attentions to score importance over the context — materialising
    just [obs_window, ctx_len], not [seq, seq]. The prompt cache is then compressed once and the short
    answer decoded with SDPA, so peak VRAM reflects the (compressed) KV cache and eviction shows a real win.
    """
    import torch
    mdev = next(model.parameters()).device
    prompt_ids = prompt_ids.to(mdev)
    seq = int(prompt_ids.shape[1])
    on_cuda = device == "cuda" and torch.cuda.is_available()
    if on_cuda:
        torch.cuda.reset_peak_memory_stats(); torch.cuda.synchronize()
    guard = Guard()
    priors = np.full(seq, 0.5) if priors is None else np.asarray(priors, dtype=np.float64)[:seq]
    imp = PositionImportance(priors)

    W = int(min(obs_window, seq))
    ctx_len = seq - W
    with torch.no_grad():
        if ctx_len > 0:
            out_ctx = model(prompt_ids[:, :ctx_len], use_cache=True)            # SDPA, no attentions
            cache = out_ctx.past_key_values
            out_win = model(prompt_ids[:, ctx_len:], past_key_values=cache, use_cache=True,
                            output_attentions=True)                            # only [W, ctx_len] materialised
            cache = out_win.past_key_values
            mass_ctx = window_mass(_window_layer_attn(out_win.attentions, ctx_len))  # [ctx_len]
            imp.mass[:mass_ctx.shape[0]] += mass_ctx
            next_logits = out_win.logits[:, -1, :]
        else:
            out = model(prompt_ids, use_cache=True, output_attentions=True)
            cache = out.past_key_values
            imp.mass[:seq] += _attn_received(out.attentions)[:seq]
            next_logits = out.logits[:, -1, :]
    # the observation window (the question) is always load-bearing -> force-keep via high prior
    if ctx_len > 0:
        imp.prior[ctx_len:] = np.maximum(imp.prior[ctx_len:], 0.95)
    true_pos = seq

    if policy != "dense" and _seq_len(cache) > budget:
        L = _seq_len(cache)
        keep = keep_indices(policy, L, budget, importance=imp.scores(L), mass=imp.mass_scores(L), n_sink=n_sink)
        m = imp.mass_scores(L); guard.count_false_prunes(m / (m.sum() + 1e-9), keep, L)
        _evict(cache, keep)

    generated = []
    eos_id = getattr(tok, "eos_token_id", None) if eos_id is None else eos_id
    for _ in range(max_new_tokens):
        probs = torch.softmax(next_logits.float(), dim=-1)[0].detach().cpu().numpy()
        guard.confidence_check(probs)
        nxt = int(torch.argmax(next_logits, dim=-1))
        generated.append(nxt)
        if eos_id is not None and nxt == eos_id:
            break
        inp = torch.tensor([[nxt]], device=mdev)
        position_ids = torch.tensor([[true_pos]], device=mdev)
        with torch.no_grad():
            out = model(inp, past_key_values=cache, use_cache=True, position_ids=position_ids)  # SDPA
        cache = out.past_key_values
        next_logits = out.logits[:, -1, :]
        true_pos += 1

    peak = 0
    if on_cuda:
        torch.cuda.synchronize(); peak = int(torch.cuda.max_memory_allocated())
    return {"text": tok.decode(generated, skip_special_tokens=True), "tokens": generated,
            "peak_vram_bytes": peak, "final_cache_len": _seq_len(cache), **guard.summary()}

__all__ = ["manual_generate", "generate_efficient"]
