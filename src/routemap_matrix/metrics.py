"""Pure metric helpers for the needle-in-haystack KV-routing benchmark."""
from __future__ import annotations

def answer_hit(generated_text, needle):
    return needle.strip().lower() in (generated_text or "").lower()

def reduction(dense_bytes, routed_bytes):
    return 0.0 if dense_bytes <= 0 else 1.0 - (routed_bytes / dense_bytes)

__all__ = ["answer_hit", "reduction"]
