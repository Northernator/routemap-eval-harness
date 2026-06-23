"""Cycle detection for residue-decidable routes.

Cycle detection works in modular state spaces. It answers residue and route
questions; it does not reconstruct full integer values.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


def detect_cycle(step_fn: Callable[[Any], Any], start: Any) -> tuple[int, int]:
    """Return Brent cycle indices (mu, lam) for a deterministic state function."""

    power = 1
    lam = 1
    tortoise = start
    hare = step_fn(start)
    while tortoise != hare:
        if power == lam:
            tortoise = hare
            power *= 2
            lam = 0
        hare = step_fn(hare)
        lam += 1
    tortoise = start
    hare = start
    for _ in range(lam):
        hare = step_fn(hare)
    mu = 0
    while tortoise != hare:
        tortoise = step_fn(tortoise)
        hare = step_fn(hare)
        mu += 1
    return mu, lam


def power_cycle(base: int, modulus: int) -> dict[str, int | list[int]]:
    """Return cycle metadata for residues of base^1, base^2, ... modulo modulus."""

    _validate_modulus(modulus)
    start = base % modulus
    step = lambda residue: (residue * base) % modulus
    mu, lam = detect_cycle(step, start)
    sequence: list[int] = []
    value = start
    for _ in range(mu + lam):
        sequence.append(value)
        value = step(value)
    return {"mu": mu, "lam": lam, "sequence": sequence}


def pisano_period(modulus: int) -> int:
    """Return Fibonacci pair-state period modulo modulus."""

    _validate_modulus(modulus)
    step = lambda state: (state[1], (state[0] + state[1]) % modulus)
    mu, lam = detect_cycle(step, (0, 1 % modulus))
    if mu != 0:
        raise ValueError("unexpected Fibonacci pre-period")
    return lam


def linear_recurrence_period(coeffs: Sequence[int], init: Sequence[int], modulus: int) -> dict[str, int]:
    _validate_modulus(modulus)
    if not coeffs:
        raise ValueError("coeffs must not be empty")
    if len(coeffs) != len(init):
        raise ValueError("coeffs and init must have the same length")
    if any(not isinstance(value, int) for value in coeffs) or any(not isinstance(value, int) for value in init):
        raise ValueError("coeffs and init values must be ints")
    coefficients = tuple(value % modulus for value in coeffs)
    start = tuple(value % modulus for value in init)

    def step(state: tuple[int, ...]) -> tuple[int, ...]:
        next_value = sum(coef * value for coef, value in zip(coefficients, state)) % modulus
        return state[1:] + (next_value,)

    mu, lam = detect_cycle(step, start)
    return {"mu": mu, "lam": lam}


def pow_mod_via_cycle(base: int, exponent: int, modulus: int) -> int:
    if not isinstance(exponent, int) or exponent < 0:
        raise ValueError("exponent must be a nonnegative int")
    _validate_modulus(modulus)
    if exponent == 0:
        return 1 % modulus
    cycle = power_cycle(base, modulus)
    sequence = cycle["sequence"]
    mu = int(cycle["mu"])
    lam = int(cycle["lam"])
    index = exponent - 1
    if index < mu:
        return sequence[index]
    return sequence[mu + ((index - mu) % lam)]


def fib_mod_via_cycle(n: int, modulus: int) -> int:
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a nonnegative int")
    _validate_modulus(modulus)
    period = pisano_period(modulus)
    target = n % period
    a, b = 0, 1 % modulus
    for _ in range(target):
        a, b = b, (a + b) % modulus
    return a


def _validate_modulus(modulus: int) -> None:
    if not isinstance(modulus, int) or modulus <= 1:
        raise ValueError("modulus must be an integer greater than 1")


__all__ = [
    "detect_cycle",
    "fib_mod_via_cycle",
    "linear_recurrence_period",
    "pisano_period",
    "pow_mod_via_cycle",
    "power_cycle",
]
