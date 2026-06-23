"""Thin re-export of the validated Digital Route residue engine."""

from __future__ import annotations

from dr_residue_engine_v1 import DEFAULT_MODULI, digital_root, fingerprint, fingerprint_of_value


__all__ = ["DEFAULT_MODULI", "digital_root", "fingerprint", "fingerprint_of_value"]
