"""Metrics and benchmark bars for HugeArithmeticRouteBench."""

from __future__ import annotations

from typing import Any


def compute_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    route_answerable = [row for row in rows if row["route_answerable"]]
    checked = [row for row in rows if row.get("route_checkable")]
    wrong_route_checkable = [row for row in checked if not row["raw_correct"]]
    catchable = [row for row in wrong_route_checkable if row["catchable"]]
    caught_catchable = [row for row in catchable if row["verdict"] == "RULED_OUT_WRONG"]
    correct_checked = [row for row in checked if row["raw_correct"]]
    false_reject = [row for row in correct_checked if row["false_rejection"]]
    blind = [row for row in wrong_route_checkable if row["blind_spot"]]
    blind_caught = [row for row in blind if row["verdict"] == "RULED_OUT_WRONG"]
    agreement = [
        row
        for row in wrong_route_checkable
        if bool(row["catchable"]) == (row["verdict"] == "RULED_OUT_WRONG")
    ]
    compute_by_size = {
        size: _compute_saved([row for row in rows if row["size_class"] == size])
        for size in ("small", "large", "huge")
    }
    impossible_cases = len([row for row in rows if row.get("route_checkable") and not row["full_expansion_feasible"]])
    metrics = {
        "raw_solver_accuracy": _rate(len([row for row in rows if row["raw_correct"]]), total),
        "route_engine_accuracy": _rate(len([row for row in route_answerable if row["route_correct"]]), len(route_answerable)),
        "verifier_catch_rate": _rate(len(caught_catchable), len(catchable)),
        "false_rejection_rate": _rate(len(false_reject), len(correct_checked)),
        "route_decidable_coverage": _rate(len(checked), total),
        "blind_spot_rate": _rate(len(blind_caught), len(blind)),
        "oracle_verifier_agreement": _rate(len(agreement), len(wrong_route_checkable)),
        "compute_saved_overall": _compute_saved(rows),
        "compute_saved_large": compute_by_size["large"],
        "compute_saved_by_size": compute_by_size,
        "full_expansion_impossible_cases": impossible_cases,
        "route_answerable_n": len(route_answerable),
        "checked_n": len(checked),
        "wrong_checked_n": len(wrong_route_checkable),
        "catchable_n": len(catchable),
        "blind_spot_n": len(blind),
    }
    metrics.update(pass_fail(metrics))
    return metrics


def pass_fail(metrics: dict[str, Any]) -> dict[str, str]:
    catch = float(metrics["verifier_catch_rate"])
    false_reject = float(metrics["false_rejection_rate"])
    compute_saved_large = float(metrics["compute_saved_large"])
    impossible = int(metrics["full_expansion_impossible_cases"]) > 0
    if compute_saved_large >= 100.0:
        speed_basis = "10x_large"
    elif impossible:
        speed_basis = "expansion_impossible"
    elif compute_saved_large >= 10.0:
        speed_basis = "10x_large"
    else:
        speed_basis = "none"
    return {
        "verifier_minimum_bar": "PASS" if catch > 0.80 and false_reject < 0.03 else "FAIL",
        "verifier_strong_bar": "PASS" if catch > 0.95 and false_reject < 0.01 else "FAIL",
        "speed_minimum_bar": "PASS" if compute_saved_large >= 10.0 or impossible else "FAIL",
        "speed_strong_bar": "PASS" if compute_saved_large >= 100.0 or impossible else "FAIL",
        "speed_bar_basis": speed_basis,
    }


def markdown_table(metrics: dict[str, Any]) -> str:
    rows = [
        ("raw_solver_accuracy", f"{float(metrics['raw_solver_accuracy']):.3f}"),
        ("route_engine_accuracy", f"{float(metrics['route_engine_accuracy']):.3f}"),
        ("verifier_catch_rate", f"{float(metrics['verifier_catch_rate']):.3f}"),
        ("false_rejection_rate", f"{float(metrics['false_rejection_rate']):.3f}"),
        ("blind_spot_rate", f"{float(metrics['blind_spot_rate']):.3f}"),
        ("oracle_verifier_agreement", f"{float(metrics['oracle_verifier_agreement']):.3f}"),
        ("route_decidable_coverage", f"{float(metrics['route_decidable_coverage']):.3f}"),
        ("compute_saved_large", f"{float(metrics['compute_saved_large']):.3f}x"),
        ("compute_saved_overall", f"{float(metrics['compute_saved_overall']):.3f}x"),
        ("full_expansion_impossible_cases", str(metrics["full_expansion_impossible_cases"])),
        ("speed_bar_basis", metrics["speed_bar_basis"]),
        ("verifier_minimum_bar", metrics["verifier_minimum_bar"]),
        ("verifier_strong_bar", metrics["verifier_strong_bar"]),
        ("speed_minimum_bar", metrics["speed_minimum_bar"]),
        ("speed_strong_bar", metrics["speed_strong_bar"]),
    ]
    lines = ["| Metric | Value |", "| --- | ---: |"]
    lines.extend(f"| {name} | {value} |" for name, value in rows)
    return "\n".join(lines)


def _rate(numerator: int, denominator: int) -> float:
    return 0.0 if denominator == 0 else numerator / denominator


def _compute_saved(rows: list[dict[str, Any]]) -> float:
    full_timed = [row for row in rows if row["full_expansion_checked"] and row["route_answerable"] and row["route_seconds"] >= 0]
    full_time = sum(float(row["full_expansion_seconds"]) for row in full_timed)
    route_time = sum(max(float(row["route_seconds"]), 1e-9) for row in full_timed)
    return (full_time / route_time) if route_time else 0.0


__all__ = ["compute_metrics", "markdown_table", "pass_fail"]
