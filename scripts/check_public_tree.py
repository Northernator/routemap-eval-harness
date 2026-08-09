#!/usr/bin/env python3
"""Fail closed when tracked files contain common private material.

This guard complements, but does not replace, a full-history secret scanner and
GitHub secret scanning with push protection.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    line: int | None = None

    def display(self) -> str:
        location = f"{self.path}:{self.line}" if self.line is not None else self.path
        return f"{location}: {self.rule}"


CONTENT_RULES = (
    ("private key material", re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")),
    ("GitHub access token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,255}|github_pat_[A-Za-z0-9_]{50,255})\b")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("OpenAI or Anthropic API key", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("live Stripe secret", re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{16,}\b")),
    ("credential embedded in URL", re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")),
    (
        "personal Windows user-home path",
        re.compile(r"(?i)\b[A-Z]:[\\/]+Users[\\/]+(?!Public(?:[\\/]|$)|runneradmin(?:[\\/]|$))[^\\/\s]+[\\/]"),
    ),
    (
        "personal Unix user-home path",
        re.compile(r"/(?:Users|home)/(?!runner(?:/|$)|github(?:/|$))[^/\s]+/"),
    ),
)

BLOCKED_NAMES = {
    ".env",
    "credentials.json",
    "application_default_credentials.json",
    "id_rsa",
    "id_ed25519",
}
BLOCKED_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
GENERATED_PREFIXES = ("data/outputs/", "data/runs/", "EVIDENCE/")


def tracked_paths(root: Path = ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [path.decode("utf-8") for path in result.stdout.split(b"\0") if path]


def _path_findings(relative_path: str) -> list[Finding]:
    normalized = PurePosixPath(relative_path).as_posix()
    name = PurePosixPath(normalized).name.lower()
    suffix = PurePosixPath(normalized).suffix.lower()
    findings: list[Finding] = []

    if name in BLOCKED_NAMES or (name.startswith(".env.") and name != ".env.example"):
        findings.append(Finding(normalized, "secret-bearing filename is tracked"))
    if suffix in BLOCKED_SUFFIXES:
        findings.append(Finding(normalized, "private-key or certificate filename is tracked"))
    if normalized.startswith(GENERATED_PREFIXES):
        findings.append(Finding(normalized, "local generated-output path is tracked"))
    return findings


def scan_paths(root: Path, paths: Iterable[str]) -> list[Finding]:
    findings: list[Finding] = []
    for relative_path in paths:
        findings.extend(_path_findings(relative_path))
        path = root / relative_path
        try:
            data = path.read_bytes()
        except OSError:
            findings.append(Finding(relative_path, "tracked file cannot be read"))
            continue
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for rule, pattern in CONTENT_RULES:
                if pattern.search(line):
                    findings.append(Finding(relative_path, rule, line_number))
    return findings


def main() -> int:
    paths = tracked_paths()
    findings = scan_paths(ROOT, paths)
    if findings:
        print("Public-tree guard: FAIL", file=sys.stderr)
        for finding in findings:
            print(f"- {finding.display()}", file=sys.stderr)
        print("Matched values are intentionally redacted.", file=sys.stderr)
        return 1
    print(f"Public-tree guard: PASS ({len(paths)} tracked files scanned)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
