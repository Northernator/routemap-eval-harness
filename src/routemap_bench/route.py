"""Route-engine answer and verify paths for HugeArithmeticRouteBench."""

from __future__ import annotations

import time
from typing import Any

from routemap_digital import fib_mod_via_cycle, fingerprint, linear_recurrence_period, verify
from routemap_digital.verify import NOT_RULED_OUT, RULED_OUT_WRONG

from .tasks import TaskInstance, exact_value_feasible


def route_answer(task: TaskInstance) -> tuple[bool, Any, float]:
    start = time.perf_counter()
    if not task.route_decidable:
        return False, None, time.perf_counter() - start
    kind = task.query["kind"]
    if kind == "digital_root":
        residue = fingerprint(task.expr_spec, (9,))[9]
        answer = 9 if residue == 0 else residue
    elif kind in {"mod_m", "last_k_digits"}:
        modulus = int(task.query["modulus"])
        answer = fingerprint(task.expr_spec, (modulus,))[modulus]
    elif kind == "divisibility":
        modulus = int(task.query["modulus"])
        answer = fingerprint(task.expr_spec, (modulus,))[modulus] == 0
    elif kind == "fibonacci_state":
        answer = fib_mod_via_cycle(int(task.expr_spec["n"]), int(task.query["modulus"]))
    elif kind == "linear_recurrence_residue":
        answer = _linear_recurrence_route_answer(task)
    else:
        return False, None, time.perf_counter() - start
    return True, answer, time.perf_counter() - start


def verify_claim(task: TaskInstance, claimed_answer: Any) -> dict[str, Any]:
    kind = task.query["kind"]
    modulus = int(task.query.get("modulus", 9))
    if kind == "divisibility":
        if bool(claimed_answer):
            result = verify(task.expr_spec, 0, (modulus,))
            return {"verdict": result["verdict"], "disagreeing_moduli": result["disagreeing_moduli"], "checked": True}
        residue = fingerprint(task.expr_spec, (modulus,))[modulus]
        verdict = RULED_OUT_WRONG if residue == 0 else NOT_RULED_OUT
        return {"verdict": verdict, "disagreeing_moduli": [modulus] if residue == 0 else [], "checked": True}
    if kind == "impossibility":
        residue = fingerprint(task.expr_spec, (modulus,))[modulus]
        actual_possible = residue in set(task.query["allowed_residues"])
        verdict = NOT_RULED_OUT if bool(claimed_answer) == actual_possible else RULED_OUT_WRONG
        return {"verdict": verdict, "disagreeing_moduli": [modulus] if verdict == RULED_OUT_WRONG else [], "checked": True}
    if not task.route_decidable:
        return {"verdict": "NOT_ROUTE_DECIDABLE", "disagreeing_moduli": [], "checked": False}
    elif kind in {"linear_recurrence_residue", "fibonacci_state"}:
        answerable, answer, _ = route_answer(task)
        if not answerable:
            return {"verdict": "NOT_ROUTE_DECIDABLE", "disagreeing_moduli": [], "checked": False}
        expr_spec = {"family": "bigsum", "values": [int(answer)]}
        claimed_value = int(claimed_answer)
    else:
        expr_spec = task.expr_spec
        claimed_value = _digital_root_to_residue(claimed_answer) if kind == "digital_root" else int(claimed_answer)
    result = verify(expr_spec, claimed_value, (modulus,))
    return {"verdict": result["verdict"], "disagreeing_moduli": result["disagreeing_moduli"], "checked": True}


def full_expansion_answer(task: TaskInstance) -> tuple[bool, Any, float]:
    if not task.full_expansion_feasible or task.expr_spec.get("family") in {"linear_recurrence", "pascal"}:
        return False, None, 0.0
    start = time.perf_counter()
    value = exact_value_feasible(task.expr_spec)
    kind = task.query["kind"]
    if kind == "digital_root":
        answer = 0 if value == 0 else 1 + ((value - 1) % 9)
    elif kind in {"mod_m", "last_k_digits"}:
        answer = value % int(task.query["modulus"])
    elif kind == "divisibility":
        answer = value % int(task.query["modulus"]) == 0
    elif kind == "impossibility":
        residue = value % int(task.query["modulus"])
        answer = residue in set(task.query["allowed_residues"])
    else:
        return False, None, time.perf_counter() - start
    return True, answer, time.perf_counter() - start


def evaluate_task(task: TaskInstance, claimed_answer: Any) -> dict[str, Any]:
    answerable, answer, route_seconds = route_answer(task)
    full_ok, full_answer, full_seconds = full_expansion_answer(task)
    verdict = verify_claim(task, claimed_answer)
    raw_correct = claimed_answer == task.ground_truth
    route_correct = answerable and answer == task.ground_truth
    route_checkable = bool(verdict["checked"])
    wrong = not raw_correct
    catchable, blind_spot = _classify_wrong(task, claimed_answer, route_checkable, wrong)
    caught_wrong = wrong and verdict["verdict"] == RULED_OUT_WRONG
    false_rejection = raw_correct and verdict["verdict"] == RULED_OUT_WRONG
    return {
        "task_id": task.task_id,
        "family": task.family,
        "size_class": task.size_class,
        "route_decidable": task.route_decidable,
        "route_answerable": answerable,
        "route_checkable": route_checkable,
        "full_expansion_feasible": task.full_expansion_feasible,
        "ground_truth": task.ground_truth,
        "claimed_answer": claimed_answer,
        "raw_correct": raw_correct,
        "route_answer": answer,
        "route_correct": route_correct,
        "verdict": verdict["verdict"],
        "caught_wrong": caught_wrong,
        "false_rejection": false_rejection,
        "catchable": catchable,
        "blind_spot": blind_spot,
        "route_seconds": route_seconds,
        "full_expansion_checked": full_ok,
        "full_expansion_answer": full_answer,
        "full_expansion_seconds": full_seconds,
    }


def _classify_wrong(task: TaskInstance, claimed_answer: Any, route_checkable: bool, wrong: bool) -> tuple[bool, bool]:
    if not wrong or not route_checkable:
        return False, False
    if isinstance(task.ground_truth, bool):
        return True, False
    try:
        modulus = _checked_modulus(task)
        residue_consistent = (int(claimed_answer) - int(task.ground_truth)) % modulus == 0
    except (TypeError, ValueError):
        return True, False
    return not residue_consistent, residue_consistent


def _checked_modulus(task: TaskInstance) -> int:
    return int(task.query.get("modulus", 9))


def _linear_recurrence_route_answer(task: TaskInstance) -> int:
    coeffs = [int(value) for value in task.expr_spec["coeffs"]]
    init = [int(value) for value in task.expr_spec["init"]]
    modulus = int(task.query["modulus"])
    n = int(task.expr_spec["n"])
    period = linear_recurrence_period(coeffs, init, modulus)
    order = len(coeffs)
    if n < order:
        return init[n] % modulus
    state = tuple(value % modulus for value in init)
    target_steps = n - order + 1
    mu = int(period["mu"])
    lam = int(period["lam"])
    if target_steps >= mu:
        target_steps = mu + ((target_steps - mu) % lam)
    for _ in range(target_steps):
        next_value = sum(coef * value for coef, value in zip(coeffs, state)) % modulus
        state = state[1:] + (next_value,)
    return state[-1]


def _digital_root_to_residue(value: Any) -> int:
    number = int(value)
    return 0 if number == 9 else number % 9


__all__ = ["NOT_RULED_OUT", "RULED_OUT_WRONG", "evaluate_task", "full_expansion_answer", "route_answer", "verify_claim"]
