from __future__ import annotations

from pathlib import Path

import run_evidence


def _set_output(monkeypatch, tmp_path: Path) -> Path:
    output = tmp_path / "EVIDENCE"
    monkeypatch.setattr(run_evidence, "OUT", output)
    return output


def test_evidence_runner_returns_nonzero_and_captures_all_required_failures(
    monkeypatch, tmp_path: Path
) -> None:
    output = _set_output(monkeypatch, tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(
        run_evidence,
        "STEPS",
        [
            ("passing check", ["pass"], "passes"),
            ("failing check", ["fail"], "fails"),
            ("later check", ["later"], "still runs"),
        ],
    )
    monkeypatch.setattr(run_evidence, "GATED", [])

    def fake_run(argv, timeout=1200):
        calls.append(argv[0])
        return (1, "failure detail") if argv[0] == "fail" else (0, "success detail")

    monkeypatch.setattr(run_evidence, "_run", fake_run)

    assert run_evidence.main() == 1
    assert calls == ["pass", "fail", "later"]
    results = (output / "RESULTS.md").read_text(encoding="utf-8")
    assert "| failing check | FAIL | fails |" in results
    assert "failure detail" in results


def test_evidence_runner_allows_unavailable_optional_gate(
    monkeypatch, tmp_path: Path
) -> None:
    output = _set_output(monkeypatch, tmp_path)
    monkeypatch.setattr(run_evidence, "STEPS", [("required check", ["pass"], "required")])
    monkeypatch.setattr(run_evidence, "GATED", [("optional check", ["optional"], "torch")])
    monkeypatch.setattr(run_evidence, "MATRIX_DEPS", False)
    monkeypatch.setattr(run_evidence, "_run", lambda argv, timeout=1200: (0, "success"))

    assert run_evidence.main() == 0
    results = (output / "RESULTS.md").read_text(encoding="utf-8")
    assert "| optional check | SKIP | torch |" in results


def test_evidence_runner_fails_when_available_optional_gate_fails(
    monkeypatch, tmp_path: Path
) -> None:
    _set_output(monkeypatch, tmp_path)
    monkeypatch.setattr(run_evidence, "STEPS", [("required check", ["pass"], "required")])
    monkeypatch.setattr(run_evidence, "GATED", [("available check", ["fail"], "torch")])
    monkeypatch.setattr(run_evidence, "MATRIX_DEPS", True)
    monkeypatch.setattr(
        run_evidence,
        "_run",
        lambda argv, timeout=1200: (1, "failure") if argv[0] == "fail" else (0, "success"),
    )

    assert run_evidence.main() == 1


def test_evidence_workflow_is_complete_and_fail_closed() -> None:
    workflow = (
        Path(__file__).resolve().parents[1] / ".github/workflows/evidence.yml"
    ).read_text(encoding="utf-8")

    for required in (
        "permissions:\n  contents: read",
        'python -m pip install -e ".[dev]"',
        "python -m pytest -q tests",
        "rt_test_elements.py",
        "rt_test_grounding.py",
        "python scripts/check_public_tree.py",
        "python scripts/check_acceptance.py",
        "python run_evidence.py",
        "if-no-files-found: error",
    ):
        assert required in workflow
    assert "continue-on-error" not in workflow
    assert "uses: actions/checkout@v" not in workflow
    assert "uses: actions/setup-python@v" not in workflow
    assert "uses: actions/upload-artifact@v" not in workflow
