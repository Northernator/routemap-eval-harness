"""Load a small causal LM for KV-routing experiments. GPU run; toy/CPU path for the self-check."""
from __future__ import annotations

def free_vram_gb():
    import torch
    if not torch.cuda.is_available():
        return 0.0
    free, _total = torch.cuda.mem_get_info()
    return free / 1e9

def load_model(name=None, *, prefer_fp16=True, efficient=False):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    if name is None:
        name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" if free_vram_gb() >= 6.0 else "Qwen/Qwen2.5-0.5B-Instruct"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dt = torch.float16 if (device == "cuda" and prefer_fp16) else torch.float32
    tok = AutoTokenizer.from_pretrained(name)
    try:
        model = AutoModelForCausalLM.from_pretrained(name, dtype=dt, attn_implementation=("sdpa" if efficient else "eager"))
    except TypeError:
        model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=dt, attn_implementation=("sdpa" if efficient else "eager"))
    return model.to(device).eval(), tok, device

def toy_model(vocab_size=128):
    """Tiny random Llama (RoPE + DynamicCache) — SAME cache path as the real model, no download."""
    from transformers import LlamaForCausalLM, LlamaConfig
    cfg = LlamaConfig(hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                      num_attention_heads=4, num_key_value_heads=4, vocab_size=vocab_size,
                      max_position_embeddings=4096, attn_implementation="eager")
    return LlamaForCausalLM(cfg).eval()

__all__ = ["load_model", "toy_model", "free_vram_gb"]
