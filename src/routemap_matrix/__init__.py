"""routemap_matrix: KV-cache importance routing (research-only, memory-led).
Torch-dependent modules (model, decode, bench) are imported lazily so the pure
route-and-validate core (importance, policies, guard, kv, metrics) works without torch."""
__all__ = ["importance", "policies", "guard", "kv", "metrics"]
