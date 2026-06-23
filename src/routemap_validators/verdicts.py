"""Canonical verdict contract for RouteMap validators."""

from __future__ import annotations

from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG


UNCHECKABLE = "UNCHECKABLE"


class Verdict:
    RULED_OUT_WRONG = RULED_OUT_WRONG
    NOT_RULED_OUT = NOT_RULED_OUT
    UNCHECKABLE = UNCHECKABLE
    ALL = frozenset((RULED_OUT_WRONG, NOT_RULED_OUT, UNCHECKABLE))


ALL = Verdict.ALL


__all__ = ["Verdict", "RULED_OUT_WRONG", "NOT_RULED_OUT", "UNCHECKABLE", "ALL"]
