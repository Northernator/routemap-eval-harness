"""KV keep-index policies. Pure numpy; returns sorted kept positions of length min(seq_len, budget)."""
from __future__ import annotations
import numpy as np

POLICIES = ("dense", "recency_window", "h2o", "routemap")

def keep_indices(policy, seq_len, budget, *, importance=None, mass=None, n_sink=4):
    if policy == "dense" or seq_len <= budget:
        return np.arange(seq_len)
    if policy == "recency_window":
        return np.arange(seq_len - budget, seq_len)
    n_sink = int(min(n_sink, budget, seq_len))
    sinks = np.arange(n_sink)
    cand = np.arange(n_sink, seq_len)
    k = budget - n_sink
    if k <= 0:
        return np.sort(sinks[:budget])
    if policy == "h2o":
        score = np.asarray(mass, dtype=np.float64)[cand]
    elif policy == "routemap":
        score = np.asarray(importance, dtype=np.float64)[cand]
    else:
        raise ValueError(f"unknown policy {policy!r}")
    top = cand[np.argsort(-score, kind="stable")[:k]]
    return np.sort(np.union1d(sinks, top))

__all__ = ["keep_indices", "POLICIES"]
