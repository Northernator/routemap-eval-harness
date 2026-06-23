"""Backend-agnostic KV eviction bookkeeping: works on numpy arrays or torch tensors."""
from __future__ import annotations

def evict_kv(layers, keep_idx, seq_dim=2):
    """layers: list of (k, v), each [batch, heads, seq, dim]. Returns new list gathered to keep_idx."""
    return [(_take(k, keep_idx, seq_dim), _take(v, keep_idx, seq_dim)) for k, v in layers]

def _take(t, idx, dim):
    import numpy as np
    if isinstance(t, np.ndarray):
        return np.take(t, np.asarray(idx, dtype=np.int64), axis=dim)
    import torch  # only reached for torch tensors
    if not isinstance(idx, torch.Tensor):
        idx = torch.as_tensor(list(int(i) for i in idx), dtype=torch.long, device=t.device)
    return t.index_select(dim, idx)

__all__ = ["evict_kv"]
