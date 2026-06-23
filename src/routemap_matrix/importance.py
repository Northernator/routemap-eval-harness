"""Per-position KV importance = accumulated attention mass + recency + token-class prior.
Array-based (numpy). The torch decode loop converts attention weights to numpy before calling."""
from __future__ import annotations
import numpy as np

CLASS_PRIOR = {
    "named_entity": 1.0, "number": 1.0, "formula": 1.0, "citation": 0.9, "negation": 0.9,
    "code_token": 0.9, "content_word": 0.8, "instruction": 0.7,
    "function_word": 0.15, "punctuation": 0.10, "unknown": 0.5,
}

def token_class_priors(tokens):
    """tokens: list[str] -> np.array of per-position prior in [0,1] (uses routemap_token if available)."""
    try:
        from routemap_token.prior import classify_token
    except Exception:
        classify_token = None
    vals = []
    for tok in tokens:
        cls = classify_token(tok) if classify_token else "unknown"
        vals.append(CLASS_PRIOR.get(cls, 0.5))
    return np.asarray(vals, dtype=np.float64)


def window_mass(layer_attn):
    """SnapKV-style observation-window mass. layer_attn: list of [W, K] arrays (head-averaged attention
    of the W observation queries over K keys). Returns [K] = mean over layers of (sum over the W queries).
    Materialises only [W, K] per layer, not [seq, seq] -> memory-efficient importance."""
    import numpy as np
    acc = None
    for a in layer_attn:
        s = np.asarray(a, dtype=np.float64).sum(axis=0)
        acc = s if acc is None else acc + s
    return acc / max(1, len(layer_attn))

class PositionImportance:
    def __init__(self, prior, *, w_mass=0.5, w_recency=0.2, w_prior=0.3, decay=0.02):
        self.prior = np.asarray(prior, dtype=np.float64)
        self.mass = np.zeros_like(self.prior)
        self.w_mass, self.w_recency, self.w_prior, self.decay = w_mass, w_recency, w_prior, decay

    def update(self, attn_step):
        a = np.asarray(attn_step, dtype=np.float64)
        self.mass[:a.shape[0]] += a

    def extend(self, n_new):
        if n_new > 0:
            self.prior = np.concatenate([self.prior, np.full(n_new, 0.5)])
            self.mass = np.concatenate([self.mass, np.zeros(n_new)])

    def scores(self, seq_len):
        mass = self.mass[:seq_len]
        m = mass / (mass.max() + 1e-9)
        pos = np.arange(seq_len)
        recency = np.exp(-self.decay * (seq_len - 1 - pos))
        return self.w_mass * m + self.w_recency * recency + self.w_prior * self.prior[:seq_len]

    def mass_scores(self, seq_len):
        return self.mass[:seq_len].copy()

__all__ = ["PositionImportance", "token_class_priors", "CLASS_PRIOR", "window_mass"]
