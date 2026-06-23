"""Digital Route residue engine v1.

Pure, exact modular fingerprints for arithmetic expression families.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


DEFAULT_MODULI: tuple[int, ...] = (7, 9, 11, 13, 37, 101)


def _validate_moduli(moduli: Iterable[int] | None) -> tuple[int, ...]:
    bank = tuple(DEFAULT_MODULI if moduli is None else moduli)
    if not bank:
        raise ValueError("modulus bank must not be empty")
    if any(not isinstance(m, int) or m <= 1 for m in bank):
        raise ValueError("all moduli must be integers greater than 1")
    return bank


def _family(expr_spec: Mapping[str, Any]) -> str:
    family = expr_spec.get("family", expr_spec.get("type"))
    if not isinstance(family, str):
        raise ValueError("expr_spec must include string family")
    return family.lower()


def _int_field(expr_spec: Mapping[str, Any], name: str) -> int:
    value = expr_spec.get(name)
    if not isinstance(value, int):
        raise ValueError(f"expr_spec field {name!r} must be an int")
    return value


def _nonnegative_int_field(expr_spec: Mapping[str, Any], name: str) -> int:
    value = _int_field(expr_spec, name)
    if value < 0:
        raise ValueError(f"expr_spec field {name!r} must be nonnegative")
    return value


def _values_field(expr_spec: Mapping[str, Any]) -> tuple[int, ...]:
    values = expr_spec.get("values")
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise ValueError("expr_spec field 'values' must be an iterable of ints")
    result = tuple(values)
    if any(not isinstance(value, int) for value in result):
        raise ValueError("all values must be ints")
    return result


def digital_root(value: int) -> int:
    """Return base-10 digital root for positive integers, with 0 -> 0."""

    if not isinstance(value, int):
        raise TypeError("value must be an int")
    if value < 0:
        raise ValueError("digital_root is defined here for N >= 0")
    if value == 0:
        return 0
    return 1 + ((value - 1) % 9)


def _factorial_mod(n: int, modulus: int) -> int:
    if n >= modulus:
        return 0
    residue = 1 % modulus
    for value in range(2, n + 1):
        residue = (residue * (value % modulus)) % modulus
    return residue


def _fib_pair_mod(n: int, modulus: int) -> tuple[int, int]:
    if n == 0:
        return 0, 1 % modulus
    a, b = _fib_pair_mod(n >> 1, modulus)
    c = (a * ((2 * b - a) % modulus)) % modulus
    d = (a * a + b * b) % modulus
    if n & 1:
        return d, (c + d) % modulus
    return c, d


def _fibonacci_mod(n: int, modulus: int) -> int:
    return _fib_pair_mod(n, modulus)[0]


def _fingerprint_mod(expr_spec: Mapping[str, Any], modulus: int) -> int:
    family = _family(expr_spec)
    if family == "power":
        base = _int_field(expr_spec, "base")
        exponent = _nonnegative_int_field(expr_spec, "exponent")
        return pow(base, exponent, modulus)
    if family == "factorial":
        n = _nonnegative_int_field(expr_spec, "n")
        return _factorial_mod(n, modulus)
    if family == "fibonacci":
        n = _nonnegative_int_field(expr_spec, "n")
        return _fibonacci_mod(n, modulus)
    if family == "bigsum":
        return sum(value % modulus for value in _values_field(expr_spec)) % modulus
    if family == "bigprod":
        residue = 1 % modulus
        for value in _values_field(expr_spec):
            residue = (residue * (value % modulus)) % modulus
        return residue
    raise ValueError(f"unsupported expression family: {family!r}")


def fingerprint(
    expr_spec: Mapping[str, Any],
    moduli: Iterable[int] | None = None,
) -> dict[int, int]:
    """Return {modulus: expression residue} without full expansion."""

    bank = _validate_moduli(moduli)
    return {modulus: _fingerprint_mod(expr_spec, modulus) for modulus in bank}


def fingerprint_of_value(
    value: int,
    moduli: Iterable[int] | None = None,
) -> dict[int, int]:
    """Return {modulus: value residue} for a claimed concrete integer."""

    if not isinstance(value, int):
        raise TypeError("value must be an int")
    bank = _validate_moduli(moduli)
    return {modulus: value % modulus for modulus in bank}
