"""HugeArithmeticRouteBench orchestration."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from .metrics import compute_metrics, markdown_table
from .route import evaluate_task
from .solvers import build_solver
from .tasks import FAMILIES, TaskInstance, generate_tasks


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "data" / "v1" / "digital_route" / "slice_09_hugearith"
DEFAULT_CACHE = ROOT / "data" / "v1" / "digital_route" / "slice_02_real_model" / "llm_raw_outputs_full.jsonl"


def run(
    *,
    solver_name: str = "noisy",
    families: str = "all",
    n: int = 200,
    seed: int = 7,
    error: str = "random",
    p: float = 0.5,
    out: Path = DEFAULT_OUT,
) -> dict[str, Any]:
    selected = FAMILIES if families == "all" else tuple(item.strip() for item in families.split(",") if item.strip())
    tasks = generate_tasks(n, seed=seed, families=selected)
    solver = build_solver(solver_name, p=p, error=error, seed=seed, cache_path=DEFAULT_CACHE)
    rows: list[dict[str, Any]] = []
    for task in tasks:
        try:
            claimed = solver.solve(task)
        except Exception as exc:
            claimed = f"UNSOLVED:{type(exc).__name__}:{exc}"
        rows.append(evaluate_task(task, claimed))
    metrics = compute_metrics(rows)
    out.mkdir(parents=True, exist_ok=True)
    write_tasks(out / "tasks.jsonl", tasks)
    write_results(out / "results.csv", rows)
    summary = {
        "solver": solver_name,
        "families": list(selected),
        "n": n,
        "seed": seed,
        "error": error,
        "p": p,
        "metrics": metrics,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    card = benchmark_card(summary)
    (out / "benchmark_card.md").write_text(card, encoding="utf-8")
    return {"tasks": tasks, "rows": rows, "summary": summary, "card": card}


def benchmark_card(summary: dict[str, Any]) -> str:
    return f"""# HugeArithmeticRouteBench

Solver: `{summary['solver']}`

Seed: `{summary['seed']}`

N: `{summary['n']}`

Error mode: `{summary['error']}`

## Metrics

{markdown_table(summary['metrics'])}

## Coverage Caveats

`impossibility` and `pascal_row_entry` tasks are predicate/verification-only in this slice and are counted honestly outside the route-answerable subset. CRT/cycle routes answer residues; they do not reconstruct full huge integers.

Catch rate is over residue-INCONSISTENT (catchable) wrong answers; residue-consistent errors are the characterized blind spot, reported separately. Speed bar basis is labelled.

## Methodology Guard

Ground truth is frozen in `tasks.jsonl` and computed by independent Python stdlib code in `routemap_bench.tasks`, not by `routemap_digital`.
"""


def write_tasks(path: Path, tasks: list[TaskInstance]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for task in tasks:
            handle.write(task.to_json() + "\n")


def write_results(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="routemap_bench")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--solver", choices=["oracle", "noisy", "cached", "ollama"], default="noisy")
    run_parser.add_argument("--families", default="all")
    run_parser.add_argument("--n", type=int, default=200)
    run_parser.add_argument("--seed", type=int, default=7)
    run_parser.add_argument("--error", choices=["random", "off_by_M"], default="random")
    run_parser.add_argument("--p", type=float, default=0.5)
    run_parser.add_argument("--out", default=str(DEFAULT_OUT))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command != "run":
        parser.print_help()
        return 2
    result = run(
        solver_name=args.solver,
        families=args.families,
        n=args.n,
        seed=args.seed,
        error=args.error,
        p=args.p,
        out=Path(args.out),
    )
    print(result["card"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["DEFAULT_OUT", "benchmark_card", "main", "run", "write_tasks"]
