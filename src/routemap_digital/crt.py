"""Chinese Remainder helpers with explicit ambiguity reporting.

CRT reconstruction is honest: residues identify one value modulo M, where M
is the product of the coprime bank. The original integer is reconstructed only
when an external upper bound proves the true value is below M.
"""

from __future__ import annotations

import math
from collections.abc import Mapping


def are_pairwise_coprime(moduli: list[int] | tuple[int, ...]) -> bool:
    bank = tuple(moduli)
    if any(not isinstance(modulus, int) or modulus <= 1 for modulus in bank):
        return False
    for left_index, left in enumerate(bank):
        for right in bank[left_index + 1:]:
            if math.gcd(left, right) != 1:
                return False
    return True


def crt_combine(residues: Mapping[int, int]) -> dict[str, int | bool]:
    normalized = _normalize_residues(residues)
    moduli = tuple(normalized)
    if not are_pairwise_coprime(moduli):
        raise ValueError("CRT requires pairwise-coprime moduli")
    modulus_product = math.prod(moduli)
    total = 0
    for modulus, residue in normalized.items():
        partial = modulus_product // modulus
        inverse = pow(partial, -1, modulus)
        total += residue * partial * inverse
    return {
        "value": total % modulus_product,
        "modulus_product": modulus_product,
        "pairwise_coprime": True,
    }


def reconstruct(residues: Mapping[int, int], upper_bound: int | None = None) -> dict[str, int | bool | str]:
    """Return the CRT value, marking whether it is the true integer or x mod M."""

    combined = crt_combine(residues)
    modulus_product = int(combined["modulus_product"])
    if upper_bound is not None:
        if not isinstance(upper_bound, int) or upper_bound < 0:
            raise ValueError("upper_bound must be a nonnegative int or None")
        if upper_bound <= modulus_product:
            return {
                "value": combined["value"],
                "modulus_product": modulus_product,
                "ambiguous": False,
                "note": "upper_bound <= M, so the CRT representative is the true integer",
            }
    return {
        "value": combined["value"],
        "modulus_product": modulus_product,
        "ambiguous": True,
        "note": "value is unique only modulo M; no lossless recovery without a bound <= M",
    }


def _normalize_residues(residues: Mapping[int, int]) -> dict[int, int]:
    if not residues:
        raise ValueError("residues must not be empty")
    normalized: dict[int, int] = {}
    for raw_modulus, raw_residue in residues.items():
        if not isinstance(raw_modulus, int) or raw_modulus <= 1:
            raise ValueError("all residue moduli must be integers greater than 1")
        if not isinstance(raw_residue, int):
            raise ValueError("all residues must be integers")
        normalized[raw_modulus] = raw_residue % raw_modulus
    return normalized


__all__ = ["are_pairwise_coprime", "crt_combine", "reconstruct"]
