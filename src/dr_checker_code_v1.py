"""Sound Python code checker v1."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from typing import Any

from dr_checker_framework_v1 import CheckResult
from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG


class PythonCodeChecker:
    name = "python_code_parse_v1"

    def applies_to(self, claim: Mapping[str, Any]) -> bool:
        return claim.get("type") == "python_code" and "source" in claim

    def check(self, claim: Mapping[str, Any]) -> CheckResult:
        source = str(claim["source"])
        try:
            ast.parse(source)
        except SyntaxError as exc:
            return CheckResult(
                RULED_OUT_WRONG,
                f"Python ast.parse raised SyntaxError at line {exc.lineno}: {exc.msg}",
                self.name,
                self.coverage(),
            )
        return CheckResult(
            NOT_RULED_OUT,
            "source parses as Python; logic and runtime behavior are not proven",
            self.name,
            self.coverage(),
        )

    def coverage(self) -> str:
        return "Catches syntactically impossible Python; cannot catch code that parses but computes the wrong result."

    def blind_spot_example(self) -> str:
        return "def add(a, b):\n    return a - b"
