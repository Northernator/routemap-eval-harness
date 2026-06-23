"""CLI for the unified controller demo."""

from __future__ import annotations

import argparse
from pathlib import Path

from .demo import action_plan_table, run_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="routemap_controller")
    parser.add_argument("demo", nargs="?")
    parser.add_argument("--out", default="data/v1/digital_route/slice_15_controller")
    args = parser.parse_args(argv)
    plans = run_demo(Path(args.out))
    print(action_plan_table(plans))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
