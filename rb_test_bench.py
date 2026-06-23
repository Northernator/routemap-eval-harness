from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from routemap_bench.route import evaluate_task
from routemap_bench.run_bench import run, write_tasks
from routemap_bench.tasks import (
    compute_ground_truth,
    factorial_last_k_digits,
    generate_tasks,
    independent_expr_mod,
    linear_recurrence_term_mod,
    lucas_binom_mod_prime,
)


def test_ground_truth_independence_inline_recompute() -> None:
    tasks = generate_tasks(32, seed=123)
    for task in tasks:
        assert compute_ground_truth(task.expr_spec, task.query) == task.ground_truth
        assert "routemap_digital" not in compute_ground_truth.__globals__


def test_oracle_solver_never_false_rejects_correct_route_decidable(tmp_path: Path) -> None:
    result = run(solver_name="oracle", n=64, seed=5, out=tmp_path)
    metrics = result["summary"]["metrics"]
    assert f"{metrics['raw_solver_accuracy']:.3f}" == "1.000"
    assert f"{metrics['false_rejection_rate']:.3f}" == "0.000"


def test_noisy_random_catches_and_off_by_m_blind_spot(tmp_path: Path) -> None:
    random_result = run(solver_name="noisy", error="random", p=0.0, n=64, seed=6, out=tmp_path / "random")
    random_metrics = random_result["summary"]["metrics"]
    assert f"{random_metrics['verifier_catch_rate']:.3f}" == "1.000"
    blind_result = run(solver_name="noisy", error="off_by_M", p=0.0, n=64, seed=6, out=tmp_path / "blind")
    blind_metrics = blind_result["summary"]["metrics"]
    assert f"{blind_metrics['blind_spot_rate']:.3f}" == "0.000"
    assert all(row["verdict"] != "RULED_OUT_WRONG" for row in blind_result["rows"] if row["blind_spot"])
    assert f"{blind_metrics['oracle_verifier_agreement']:.3f}" == "1.000"


def test_classification_is_ground_truth_derived_not_solver_derived() -> None:
    task = next(task for task in generate_tasks(80, seed=12) if task.family == "mod_m" and not isinstance(task.ground_truth, bool))
    modulus = int(task.query["modulus"])
    blind = evaluate_task(task, int(task.ground_truth) + modulus)
    assert blind["blind_spot"] is True
    assert blind["catchable"] is False
    assert blind["verdict"] == "NOT_RULED_OUT"
    catchable = evaluate_task(task, int(task.ground_truth) + 1)
    assert catchable["catchable"] is True
    assert catchable["blind_spot"] is False
    assert catchable["verdict"] == "RULED_OUT_WRONG"


def test_family_ground_truth_cards() -> None:
    last_digits = next(task for task in generate_tasks(40, seed=9) if task.family == "last_k_digits")
    assert last_digits.ground_truth == independent_expr_mod(last_digits.expr_spec, last_digits.query["modulus"])
    div = next(task for task in generate_tasks(40, seed=10) if task.family == "divisibility")
    assert div.ground_truth == (independent_expr_mod(div.expr_spec, div.query["modulus"]) == 0)
    impossible_tasks = [task for task in generate_tasks(80, seed=11) if task.family == "impossibility"]
    assert {bool(task.ground_truth) for task in impossible_tasks} == {False, True}


def test_deterministic_tasks_jsonl(tmp_path: Path) -> None:
    tasks_a = generate_tasks(50, seed=77)
    tasks_b = generate_tasks(50, seed=77)
    path_a = tmp_path / "a.jsonl"
    path_b = tmp_path / "b.jsonl"
    write_tasks(path_a, tasks_a)
    write_tasks(path_b, tasks_b)
    assert path_a.read_bytes() == path_b.read_bytes()


def test_compute_saved_and_huge_flags(tmp_path: Path) -> None:
    result = run(solver_name="oracle", n=96, seed=8, out=tmp_path)
    metrics = result["summary"]["metrics"]
    assert metrics["compute_saved_overall"] > 1
    assert "large" in metrics["compute_saved_by_size"]
    assert "compute_saved_large" in metrics
    assert metrics["speed_bar_basis"] == "expansion_impossible"
    assert any(row["size_class"] == "huge" and not row["full_expansion_feasible"] for row in result["rows"])


def test_oracle_verifier_agreement_full_run(tmp_path: Path) -> None:
    result = run(solver_name="noisy", error="off_by_M", p=0.0, n=96, seed=14, out=tmp_path)
    assert f"{result['summary']['metrics']['oracle_verifier_agreement']:.3f}" == "1.000"
