"""CPU self-check of the decode loop on a tiny random GPT-2 (no download). Validates eviction mechanics."""
from __future__ import annotations


def selfcheck():
    import numpy as np, torch
    from .model import toy_model
    from .decode import manual_generate, generate_efficient

    class Tok:
        eos_token_id = None
        def decode(self, ids, skip_special_tokens=True): return " ".join(str(int(i)) for i in ids)
        def convert_ids_to_tokens(self, ids): return [str(i) for i in ids]
        def __call__(self, *a, **k): raise NotImplementedError

    model = toy_model(vocab_size=128)
    ids = torch.randint(0, 128, (1, 40))
    pri = np.random.default_rng(0).random(40)
    ok = True
    for label, fn, kw in (("standard", manual_generate, {}), ("efficient", generate_efficient, {"obs_window": 8})):
        print(f"--- {label} path ---")
        for policy in ("dense", "recency_window", "h2o", "routemap"):
            r = fn(model, Tok(), ids, policy=policy, budget=16, n_sink=4, max_new_tokens=8,
                   device="cpu", priors=pri, **kw)
            within = (policy == "dense") or (r["final_cache_len"] <= 16 + 8)
            print(f"  {policy:16s} final_cache_len={r['final_cache_len']:3d} budget_ok={within} "
                  f"guard_triggers={r['guard_triggers']} false_prunes={r['false_prunes']}")
            ok = ok and within and bool(r["text"])
    print("SELFCHECK PASS:", ok)
    return 0 if ok else 1

__all__ = ["selfcheck"]
