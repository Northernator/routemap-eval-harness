"""Model-agnostic solvers for HugeArithmeticRouteBench."""

from __future__ import annotations

import json
import random
import urllib.request
from pathlib import Path
from typing import Any, Protocol

from .tasks import TaskInstance


class Solver(Protocol):
    name: str

    def solve(self, task: TaskInstance) -> Any:
        ...


class OracleSolver:
    name = "oracle"

    def solve(self, task: TaskInstance) -> Any:
        return task.ground_truth


class NoisyEngineSolver:
    name = "noisy"

    def __init__(self, p: float = 0.5, error: str = "random", seed: int = 7):
        if not 0 <= p <= 1:
            raise ValueError("p must be in [0,1]")
        if error not in {"random", "off_by_M"}:
            raise ValueError("error must be random or off_by_M")
        self.p = p
        self.error = error
        self.rng = random.Random(seed)

    def solve(self, task: TaskInstance) -> Any:
        if self.rng.random() < self.p:
            return task.ground_truth
        if isinstance(task.ground_truth, bool):
            return not task.ground_truth
        offset = int(task.query.get("modulus", 9)) if self.error == "off_by_M" else self.rng.randint(1, 99)
        if self.error == "random" and offset % int(task.query.get("modulus", 97)) == 0:
            offset += 1
        return int(task.ground_truth) + offset


class CachedSolver:
    name = "cached"

    def __init__(self, path: str | Path):
        self.rows = _load_jsonl(Path(path))
        self.by_prompt = {str(row.get("prompt", "")): str(row.get("raw_response", "")) for row in self.rows}

    def solve(self, task: TaskInstance) -> Any:
        if task.prompt not in self.by_prompt:
            raise KeyError(f"no cached response for {task.task_id}")
        raw = self.by_prompt[task.prompt]
        try:
            return int(raw.strip().replace(",", ""))
        except ValueError:
            return raw


class OllamaSolver:
    name = "ollama"

    def __init__(self, model: str = "llama3.1", timeout_seconds: int = 60):
        self.model = model
        self.timeout_seconds = timeout_seconds

    def solve(self, task: TaskInstance) -> Any:
        payload = json.dumps(
            {
                "model": self.model,
                "stream": False,
                "prompt": f"Return ONLY the answer.\n{task.prompt}",
                "options": {"temperature": 0, "num_predict": 128},
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
        raw = str(data.get("response", "")).strip()
        if isinstance(task.ground_truth, bool):
            return raw.lower() in {"true", "yes", "1"}
        return int(raw.replace(",", ""))


def build_solver(name: str, *, p: float, error: str, seed: int, cache_path: Path | None = None) -> Solver:
    if name == "oracle":
        return OracleSolver()
    if name == "noisy":
        return NoisyEngineSolver(p=p, error=error, seed=seed)
    if name == "cached":
        if cache_path is None:
            raise ValueError("cached solver requires cache_path")
        return CachedSolver(cache_path)
    if name == "ollama":
        return OllamaSolver()
    raise ValueError(f"unknown solver: {name!r}")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


__all__ = ["CachedSolver", "OllamaSolver", "OracleSolver", "NoisyEngineSolver", "Solver", "build_solver"]
