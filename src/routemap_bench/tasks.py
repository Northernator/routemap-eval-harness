"""HugeArithmeticRouteBench task generation with independent ground truth.

Ground truth in this module is computed with Python stdlib algorithms that do
not import routemap_digital. The benchmark tests the route engine; it never
uses the engine as its oracle.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass
from typing import Any


FAMILIES = (
    "digital_root",
    "mod_m",
    "last_k_digits",
    "divisibility",
    "impossibility",
    "linear_recurrence_residue",
    "fibonacci_state",
    "pascal_row_entry",
)
SIZE_CLASSES = ("small", "large", "huge")


@dataclass(frozen=True)
class TaskInstance:
    task_id: str
    family: str
    prompt: str
    expr_spec: dict[str, Any]
    query: dict[str, Any]
    ground_truth: int | bool
    size_class: str
    full_expansion_feasible: bool
    route_decidable: bool

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=True, sort_keys=True, separators=(",", ":"))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_tasks(n: int, seed: int = 7, families: str | list[str] | tuple[str, ...] = "all") -> list[TaskInstance]:
    if n <= 0:
        raise ValueError("n must be positive")
    selected = list(FAMILIES if families == "all" else families)
    unknown = sorted(set(selected) - set(FAMILIES))
    if unknown:
        raise ValueError(f"unknown families: {', '.join(unknown)}")
    rng = random.Random(seed)
    tasks: list[TaskInstance] = []
    index = 0
    while len(tasks) < n:
        family = selected[index % len(selected)]
        size_class = SIZE_CLASSES[(index // len(selected)) % len(SIZE_CLASSES)]
        tasks.append(_make_task(family, size_class, len(tasks), rng))
        index += 1
    return tasks


def compute_ground_truth(expr_spec: dict[str, Any], query: dict[str, Any]) -> int | bool:
    kind = query["kind"]
    if kind == "digital_root":
        residue = independent_expr_mod(expr_spec, 9)
        return 0 if query.get("allow_zero") and residue == 0 and _can_be_zero(expr_spec) else (9 if residue == 0 else residue)
    if kind in ("mod_m", "last_k_digits"):
        return independent_expr_mod(expr_spec, int(query["modulus"]))
    if kind == "divisibility":
        return independent_expr_mod(expr_spec, int(query["modulus"])) == 0
    if kind == "impossibility":
        residue = independent_expr_mod(expr_spec, int(query["modulus"]))
        possible = residue in set(query["allowed_residues"])
        return possible
    if kind == "linear_recurrence_residue":
        return linear_recurrence_term_mod(
            expr_spec["coeffs"],
            expr_spec["init"],
            int(expr_spec["n"]),
            int(query["modulus"]),
        )
    if kind == "fibonacci_state":
        return fib_mod(int(expr_spec["n"]), int(query["modulus"]))
    if kind == "pascal_row_entry":
        return lucas_binom_mod_prime(int(expr_spec["n"]), int(expr_spec["k"]), int(query["prime"]))
    raise ValueError(f"unknown query kind: {kind!r}")


def independent_expr_mod(expr_spec: dict[str, Any], modulus: int) -> int:
    family = expr_spec["family"]
    if family == "power":
        return pow(int(expr_spec["base"]), int(expr_spec["exponent"]), modulus)
    if family == "factorial":
        return factorial_mod(int(expr_spec["n"]), modulus)
    if family == "fibonacci":
        return fib_mod(int(expr_spec["n"]), modulus)
    if family == "bigsum":
        return sum(int(value) % modulus for value in expr_spec["values"]) % modulus
    if family == "bigprod":
        residue = 1 % modulus
        for value in expr_spec["values"]:
            residue = (residue * (int(value) % modulus)) % modulus
        return residue
    raise ValueError(f"unsupported expression family for residue GT: {family!r}")


def exact_value_feasible(expr_spec: dict[str, Any]) -> int:
    family = expr_spec["family"]
    if family == "power":
        return int(expr_spec["base"]) ** int(expr_spec["exponent"])
    if family == "factorial":
        return math.factorial(int(expr_spec["n"]))
    if family == "fibonacci":
        return fib_exact(int(expr_spec["n"]))
    if family == "bigsum":
        return sum(int(value) for value in expr_spec["values"])
    if family == "bigprod":
        product = 1
        for value in expr_spec["values"]:
            product *= int(value)
        return product
    raise ValueError(f"unsupported exact family: {family!r}")


def factorial_mod(n: int, modulus: int) -> int:
    if n < 0:
        raise ValueError("factorial n must be nonnegative")
    if n >= modulus:
        return 0
    residue = 1 % modulus
    for value in range(2, n + 1):
        residue = (residue * (value % modulus)) % modulus
    return residue


def factorial_last_k_digits(n: int, k: int) -> int:
    modulus = 10**k
    if trailing_zero_count_factorial(n) >= k:
        return 0
    return factorial_mod(n, modulus)


def trailing_zero_count_factorial(n: int) -> int:
    total = 0
    divisor = 5
    while divisor <= n:
        total += n // divisor
        divisor *= 5
    return total


def fib_mod(n: int, modulus: int) -> int:
    return _fib_pair_mod(n, modulus)[0]


def fib_exact(n: int) -> int:
    return _fib_pair_exact(n)[0]


def _fib_pair_mod(n: int, modulus: int) -> tuple[int, int]:
    if n == 0:
        return 0, 1 % modulus
    a, b = _fib_pair_mod(n >> 1, modulus)
    c = (a * ((2 * b - a) % modulus)) % modulus
    d = (a * a + b * b) % modulus
    if n & 1:
        return d, (c + d) % modulus
    return c, d


def _fib_pair_exact(n: int) -> tuple[int, int]:
    if n == 0:
        return 0, 1
    a, b = _fib_pair_exact(n >> 1)
    c = a * (2 * b - a)
    d = a * a + b * b
    if n & 1:
        return d, c + d
    return c, d


def linear_recurrence_term_mod(coeffs: list[int], init: list[int], n: int, modulus: int) -> int:
    order = len(coeffs)
    if order != len(init):
        raise ValueError("coeffs and init must have same length")
    if n < order:
        return init[n] % modulus
    transition = [[0 for _ in range(order)] for _ in range(order)]
    for col, coeff in enumerate(coeffs):
        transition[order - 1][col] = coeff % modulus
    for row in range(order - 1):
        transition[row][row + 1] = 1
    powered = matrix_pow_mod(transition, n - order + 1, modulus)
    state = [[value % modulus] for value in init]
    result = matrix_mul_mod(powered, state, modulus)
    return result[-1][0] % modulus


def matrix_pow_mod(matrix: list[list[int]], exponent: int, modulus: int) -> list[list[int]]:
    size = len(matrix)
    result = [[1 if row == col else 0 for col in range(size)] for row in range(size)]
    base = matrix
    exp = exponent
    while exp:
        if exp & 1:
            result = matrix_mul_mod(result, base, modulus)
        base = matrix_mul_mod(base, base, modulus)
        exp >>= 1
    return result


def matrix_mul_mod(left: list[list[int]], right: list[list[int]], modulus: int) -> list[list[int]]:
    rows = len(left)
    cols = len(right[0])
    inner = len(right)
    return [
        [sum(left[row][k] * right[k][col] for k in range(inner)) % modulus for col in range(cols)]
        for row in range(rows)
    ]


def lucas_binom_mod_prime(n: int, k: int, prime: int) -> int:
    if k < 0 or k > n:
        return 0
    result = 1
    nn = n
    kk = k
    while nn or kk:
        ni = nn % prime
        ki = kk % prime
        if ki > ni:
            return 0
        result = (result * math.comb(ni, ki)) % prime
        nn //= prime
        kk //= prime
    return result


def _make_task(family: str, size_class: str, index: int, rng: random.Random) -> TaskInstance:
    maker = {
        "digital_root": _digital_root_task,
        "mod_m": _mod_m_task,
        "last_k_digits": _last_k_digits_task,
        "divisibility": _divisibility_task,
        "impossibility": _impossibility_task,
        "linear_recurrence_residue": _linear_recurrence_task,
        "fibonacci_state": _fibonacci_state_task,
        "pascal_row_entry": _pascal_task,
    }[family]
    return maker(index, size_class, rng)


def _digital_root_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    expr = _power_or_fib_expr(index, size_class, rng)
    query = {"kind": "digital_root"}
    gt = compute_ground_truth(expr, query)
    prompt = f"digital_root({describe_expr(expr)})"
    return _task(index, "digital_root", prompt, expr, query, gt, size_class, size_class != "huge", True)


def _mod_m_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    modulus = rng.choice([7, 9, 11, 13, 37, 101, 1009])
    expr = _mixed_expr(index, size_class, rng)
    query = {"kind": "mod_m", "modulus": modulus}
    gt = compute_ground_truth(expr, query)
    return _task(index, "mod_m", f"{describe_expr(expr)} mod {modulus}", expr, query, gt, size_class, size_class != "huge", True)


def _last_k_digits_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    k = rng.choice([2, 3, 4, 5])
    if size_class == "huge":
        expr = {"family": "factorial", "n": 20000 + index}
        note = " trailing-zero shortcut applies"
    else:
        expr = _mixed_expr(index, size_class, rng)
        note = ""
    query = {"kind": "last_k_digits", "k": k, "modulus": 10**k, "note": note.strip()}
    gt = factorial_last_k_digits(expr["n"], k) if expr["family"] == "factorial" else compute_ground_truth(expr, query)
    return _task(index, "last_k_digits", f"last {k} digits of {describe_expr(expr)}{note}", expr, query, gt, size_class, size_class != "huge", True)


def _divisibility_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    modulus = rng.choice([7, 9, 11, 13, 37, 101])
    expr = _mixed_expr(index, size_class, rng)
    query = {"kind": "divisibility", "modulus": modulus}
    gt = compute_ground_truth(expr, query)
    return _task(index, "divisibility", f"does {modulus} divide {describe_expr(expr)}?", expr, query, gt, size_class, size_class != "huge", True)


def _impossibility_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    modulus = rng.choice([3, 4, 8])
    allowed = sorted({(value * value) % modulus for value in range(modulus)})
    expr = _mixed_expr(index, size_class, rng)
    query = {"kind": "impossibility", "predicate": "perfect_square_residue", "modulus": modulus, "allowed_residues": allowed}
    gt = compute_ground_truth(expr, query)
    return _task(index, "impossibility", f"can {describe_expr(expr)} be a perfect square modulo {modulus}?", expr, query, gt, size_class, size_class != "huge", False)


def _linear_recurrence_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    modulus = rng.choice([7, 11, 37, 101])
    n = {"small": 20 + index, "large": 2000 + index * 7, "huge": 10**6 + index * 31}[size_class]
    expr = {"family": "linear_recurrence", "coeffs": [1, 1], "init": [2, 1], "n": n}
    query = {"kind": "linear_recurrence_residue", "modulus": modulus}
    gt = compute_ground_truth(expr, query)
    return _task(index, "linear_recurrence_residue", f"Lucas-like recurrence term {n} mod {modulus}", expr, query, gt, size_class, False, True)


def _fibonacci_state_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    modulus = rng.choice([7, 9, 11, 13, 37, 101])
    n = {"small": 30 + index, "large": 5000 + index * 17, "huge": 10**7 + index * 101}[size_class]
    expr = {"family": "fibonacci", "n": n}
    query = {"kind": "fibonacci_state", "modulus": modulus}
    gt = compute_ground_truth(expr, query)
    return _task(index, "fibonacci_state", f"F({n}) mod {modulus}", expr, query, gt, size_class, size_class == "small", True)


def _pascal_task(index: int, size_class: str, rng: random.Random) -> TaskInstance:
    prime = rng.choice([2, 3, 5, 7, 11])
    n = {"small": 40 + index, "large": 5000 + index, "huge": 10**9 + index * 37}[size_class]
    k = rng.randint(0, min(1000, n))
    expr = {"family": "pascal", "n": n, "k": k}
    query = {"kind": "pascal_row_entry", "prime": prime}
    gt = compute_ground_truth(expr, query)
    return _task(index, "pascal_row_entry", f"C({n},{k}) mod {prime}", expr, query, gt, size_class, size_class == "small", False)


def _task(
    index: int,
    family: str,
    prompt: str,
    expr_spec: dict[str, Any],
    query: dict[str, Any],
    ground_truth: int | bool,
    size_class: str,
    full_expansion_feasible: bool,
    route_decidable: bool,
) -> TaskInstance:
    return TaskInstance(
        task_id=f"harb_{index:05d}",
        family=family,
        prompt=prompt,
        expr_spec=expr_spec,
        query=query,
        ground_truth=ground_truth,
        size_class=size_class,
        full_expansion_feasible=full_expansion_feasible,
        route_decidable=route_decidable,
    )


def _power_or_fib_expr(index: int, size_class: str, rng: random.Random) -> dict[str, Any]:
    if index % 2 == 0:
        exponent = {"small": 30 + index, "large": 2500 + index * 11, "huge": 10**7 + index * 101}[size_class]
        return {"family": "power", "base": rng.randint(2, 99), "exponent": exponent}
    n = {"small": 35 + index, "large": 4000 + index * 13, "huge": 10**7 + index * 103}[size_class]
    return {"family": "fibonacci", "n": n}


def _mixed_expr(index: int, size_class: str, rng: random.Random) -> dict[str, Any]:
    choice = index % 5
    if choice == 0:
        exponent = {"small": 12 + index, "large": 1800 + index * 7, "huge": 10**7 + index * 3}[size_class]
        return {"family": "power", "base": rng.randint(2, 80), "exponent": exponent}
    if choice == 1:
        n = {"small": 20 + index % 10, "large": 1400 + index, "huge": 20000 + index}[size_class]
        return {"family": "factorial", "n": n}
    if choice == 2:
        n = {"small": 50 + index, "large": 3000 + index * 5, "huge": 10**7 + index}[size_class]
        return {"family": "fibonacci", "n": n}
    if choice == 3:
        values = [rng.randint(-10**6, 10**6) for _ in range({"small": 4, "large": 80, "huge": 500}[size_class])]
        return {"family": "bigsum", "values": values}
    values = [rng.randint(-50, 50) or 1 for _ in range({"small": 4, "large": 80, "huge": 500}[size_class])]
    return {"family": "bigprod", "values": values}


def describe_expr(expr_spec: dict[str, Any]) -> str:
    family = expr_spec["family"]
    if family == "power":
        return f"{expr_spec['base']}^{expr_spec['exponent']}"
    if family == "factorial":
        return f"{expr_spec['n']}!"
    if family == "fibonacci":
        return f"F({expr_spec['n']})"
    if family == "bigsum":
        return f"sum({len(expr_spec['values'])} terms)"
    if family == "bigprod":
        return f"prod({len(expr_spec['values'])} terms)"
    if family == "linear_recurrence":
        return f"linrec(n={expr_spec['n']})"
    if family == "pascal":
        return f"C({expr_spec['n']},{expr_spec['k']})"
    return family


def _can_be_zero(expr_spec: dict[str, Any]) -> bool:
    return expr_spec.get("family") in {"bigsum", "bigprod"} and 0 in expr_spec.get("values", [])


__all__ = [
    "FAMILIES",
    "SIZE_CLASSES",
    "TaskInstance",
    "compute_ground_truth",
    "exact_value_feasible",
    "generate_tasks",
    "independent_expr_mod",
    "linear_recurrence_term_mod",
    "lucas_binom_mod_prime",
]
