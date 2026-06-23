"""Sound checker framework v1 for Digital RouteMap Phase 3.

Checkers are one-sided: they may rule out provably wrong outputs, but never
certify correctness.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from dr_verifier_v1 import NOT_RULED_OUT, RULED_OUT_WRONG, verify


@dataclass(frozen=True)
class CheckResult:
    verdict: str
    reason: str
    checker: str
    coverage_note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "reason": self.reason,
            "checker": self.checker,
            "coverage_note": self.coverage_note,
        }


class Checker(Protocol):
    name: str

    def applies_to(self, claim: Mapping[str, Any]) -> bool:
        ...

    def check(self, claim: Mapping[str, Any]) -> CheckResult:
        ...

    def coverage(self) -> str:
        ...

    def blind_spot_example(self) -> str:
        ...


class ArithmeticChecker:
    name = "arithmetic_residue_v1"

    def applies_to(self, claim: Mapping[str, Any]) -> bool:
        return claim.get("type") == "arithmetic" and "expr_spec" in claim and "claimed_answer" in claim

    def check(self, claim: Mapping[str, Any]) -> CheckResult:
        result = verify(claim["expr_spec"], int(claim["claimed_answer"]), claim.get("moduli"))
        if result["verdict"] == RULED_OUT_WRONG:
            reason = "claimed integer disagrees with exact expression residue on moduli: " + " ".join(
                str(modulus) for modulus in result["disagreeing_moduli"]
            )
        else:
            reason = "claimed integer shares the active residue fingerprint; correctness is not proven"
        return CheckResult(result["verdict"], reason, self.name, self.coverage())

    def coverage(self) -> str:
        return (
            "Catches arithmetic answers whose difference from truth is nonzero modulo at least one "
            "active modulus; cannot catch errors that are multiples of the combined modulus."
        )

    def blind_spot_example(self) -> str:
        return "For 2 + 3, claimed 33666638 passes the default bank because it differs from 5 by M=33666633."


class Router:
    def __init__(self, checkers: Iterable[Checker]):
        self.checkers = list(checkers)

    def applicable_checkers(self, claim: Mapping[str, Any]) -> list[Checker]:
        return [checker for checker in self.checkers if checker.applies_to(claim)]

    def check(self, claim: Mapping[str, Any]) -> dict[str, Any]:
        results = [checker.check(claim) for checker in self.applicable_checkers(claim)]
        ruled_out = [result for result in results if result.verdict == RULED_OUT_WRONG]
        verdict = RULED_OUT_WRONG if ruled_out else NOT_RULED_OUT
        reason = "; ".join(result.reason for result in ruled_out) if ruled_out else "no applicable checker ruled out this output"
        return {
            "verdict": verdict,
            "reason": reason,
            "checks": [result.as_dict() for result in results],
            "applicable_checkers": [result.checker for result in results],
        }


class CoverageReport:
    def __init__(self, checkers: Iterable[Checker]):
        self.checkers = list(checkers)

    def rows(self) -> list[dict[str, str]]:
        return [
            {
                "checker": checker.name,
                "coverage": checker.coverage(),
                "blind_spot_example": checker.blind_spot_example(),
            }
            for checker in self.checkers
        ]

    def text(self) -> str:
        lines: list[str] = []
        for row in self.rows():
            lines.append(f"{row['checker']}: {row['coverage']} Blind spot: {row['blind_spot_example']}")
        return "\n".join(lines)


def default_checkers() -> list[Checker]:
    from dr_checker_code_v1 import PythonCodeChecker
    from dr_checker_schema_v1 import JsonSchemaChecker

    return [ArithmeticChecker(), PythonCodeChecker(), JsonSchemaChecker()]


def default_router() -> Router:
    return Router(default_checkers())
