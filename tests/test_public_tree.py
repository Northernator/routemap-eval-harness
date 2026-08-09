from __future__ import annotations

from pathlib import Path

from scripts.check_public_tree import scan_paths, tracked_paths


ROOT = Path(__file__).resolve().parents[1]


def test_public_tree_guard_rejects_private_material_without_echoing_it(tmp_path: Path) -> None:
    secret = "github_pat_" + "A" * 60
    private_home = "C:" + "\\" + "Users" + "\\" + "private-owner" + "\\" + "project"
    (tmp_path / "unsafe.txt").write_text(
        f"token={secret}\nhome={private_home}\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("SAFE_NAME=unsafe\n", encoding="utf-8")

    findings = scan_paths(tmp_path, ["unsafe.txt", ".env"])
    rendered = "\n".join(finding.display() for finding in findings)

    assert "GitHub access token" in rendered
    assert "personal Windows user-home path" in rendered
    assert "secret-bearing filename is tracked" in rendered
    assert secret not in rendered


def test_public_tree_guard_allows_placeholders_and_nonpersonal_provenance(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "OPENAI_API_KEY=sk-...\nREPO=C:\\dev\\RouteMap\n",
        encoding="utf-8",
    )

    assert scan_paths(tmp_path, [".env.example"]) == []


def test_current_tracked_tree_passes_public_guard() -> None:
    assert scan_paths(ROOT, tracked_paths(ROOT)) == []
