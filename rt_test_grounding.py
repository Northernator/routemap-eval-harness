from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from routemap_validators.grounding import check_grounding
from routemap_validators.verdicts import NOT_RULED_OUT, RULED_OUT_WRONG, UNCHECKABLE


SOURCE = {"S1": "The RouteMap harness rejected 7 unsafe calls in London on 2026-06-24."}


def test_grounded_answer_passes() -> None:
    decision = check_grounding("RouteMap rejected 7 unsafe calls in London on 2026-06-24 [S1].", SOURCE)

    assert decision.verdict == NOT_RULED_OUT
    assert decision.checker == "grounding_guard"


def test_missing_entity_and_number_are_named() -> None:
    decision = check_grounding("RouteMap rejected 9 unsafe calls in Paris on 2026-06-24 [S1].", SOURCE)

    assert decision.verdict == RULED_OUT_WRONG
    assert "Paris" in decision.reason
    assert "9" in decision.reason


def test_missing_citation_is_rejected() -> None:
    decision = check_grounding("RouteMap rejected 7 unsafe calls in London on 2026-06-24.", SOURCE)

    assert decision.verdict == RULED_OUT_WRONG
    assert "missing citation marker" in decision.reason


def test_no_checkable_claims_is_uncheckable() -> None:
    decision = check_grounding("It was handled well.", "It was handled well.", require_citation=False)

    assert decision.verdict == UNCHECKABLE
    assert "no checkable" in decision.reason


def test_grounding_is_deterministic_and_noleak() -> None:
    answer = "RouteMap rejected 7 unsafe calls in London on 2026-06-24 [S1]."
    first = check_grounding(answer, SOURCE).record
    second = check_grounding(answer, SOURCE).record
    assert first["verdict"] == second["verdict"]
    assert first["reason"] == second["reason"]
    params = inspect.signature(check_grounding).parameters
    assert "gold" not in params
    assert "label" not in params
    assert "evidence" not in params
