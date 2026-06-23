"""Digital Route verifier v1.

One-sided wrong-answer detection by modular residue disagreement.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from dr_residue_engine_v1 import DEFAULT_MODULI, fingerprint, fingerprint_of_value


RULED_OUT_WRONG = "RULED_OUT_WRONG"
NOT_RULED_OUT = "NOT_RULED_OUT"


def verify(
    expr_spec: Mapping[str, Any],
    claimed_answer: int,
    moduli: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Return a sound one-sided verdict; never returns "correct"."""

    bank = tuple(DEFAULT_MODULI if moduli is None else moduli)
    true_fingerprint = fingerprint(expr_spec, bank)
    claimed_fingerprint = fingerprint_of_value(claimed_answer, bank)
    disagreeing_moduli = [
        modulus
        for modulus in bank
        if true_fingerprint[modulus] != claimed_fingerprint[modulus]
    ]
    verdict = RULED_OUT_WRONG if disagreeing_moduli else NOT_RULED_OUT
    return {
        "verdict": verdict,
        "disagreeing_moduli": disagreeing_moduli,
        "true_fingerprint": true_fingerprint,
        "claimed_fingerprint": claimed_fingerprint,
    }
