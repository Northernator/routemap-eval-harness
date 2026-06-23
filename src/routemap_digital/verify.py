"""Thin re-export of the validated Digital Route verifier."""

from __future__ import annotations

from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG, verify


__all__ = ["NOT_RULED_OUT", "RULED_OUT_WRONG", "verify"]
