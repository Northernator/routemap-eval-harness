"""Thin re-exports for the existing checker framework."""

from __future__ import annotations

from dr_checker_framework_v1 import (
    ArithmeticChecker,
    CheckResult,
    Checker,
    CoverageReport,
    Router,
    default_checkers,
    default_router,
)


__all__ = [
    "ArithmeticChecker",
    "CheckResult",
    "Checker",
    "CoverageReport",
    "Router",
    "default_checkers",
    "default_router",
]
