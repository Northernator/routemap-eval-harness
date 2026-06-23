"""CLI for embedding fingerprint retrieval benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

from .bench import report, run_benchmark, write_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="routemap_embedding")
    parser.add_argument("run", nargs="?")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default=None)
    parser.add_argument("--backend", choices=("tfidf", "minilm"), default="tfidf")
    parser.add_argument("--synthetic-n", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args(argv)
    result = run_benchmark(root=args.root, backend=args.backend, synthetic_n=args.synthetic_n, seed=args.seed)
    text = report(result)
    print(text)
    if args.out:
        write_outputs(result, Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
