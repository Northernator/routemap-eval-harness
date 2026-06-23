"""Validate step: detect eviction-induced degradation and escalate; track false-prune incidents."""
from __future__ import annotations
import numpy as np

def kl_divergence(p, q, eps=1e-9):
    p = np.asarray(p, dtype=np.float64) + eps
    q = np.asarray(q, dtype=np.float64) + eps
    p /= p.sum(); q /= q.sum()
    return float(np.sum(p * np.log(p / q)))

class Guard:
    def __init__(self, kl_threshold=0.10, fp_tau=0.02):
        self.kl_threshold = kl_threshold; self.fp_tau = fp_tau
        self.checks = 0; self.triggers = 0; self.false_prunes = 0

    def check(self, p_dense, p_budget):
        self.checks += 1
        kl = kl_divergence(p_dense, p_budget)
        escalate = kl > self.kl_threshold
        if escalate:
            self.triggers += 1
        return escalate, kl

    def confidence_check(self, probs, threshold=0.15):
        import numpy as np
        self.checks += 1
        conf = float(np.max(np.asarray(probs, dtype=np.float64)))
        low = conf < threshold
        if low:
            self.triggers += 1
        return low, conf

    def count_false_prunes(self, dense_attn, kept_idx, seq_len):
        a = np.asarray(dense_attn, dtype=np.float64)[:seq_len]
        kept = set(int(i) for i in kept_idx)
        fp = int(sum(1 for pos in range(seq_len) if pos not in kept and a[pos] > self.fp_tau))
        self.false_prunes += fp
        return fp

    def summary(self):
        return {"guard_checks": self.checks, "guard_triggers": self.triggers,
                "guard_trigger_rate": self.triggers / max(1, self.checks),
                "false_prunes": self.false_prunes}

__all__ = ["Guard", "kl_divergence"]
