# Public release checklist

Use this checklist for the first public release and each later tagged release. A checked item means evidence
was reviewed for the exact release commit; it is not a permanent certification.

## Blocking decisions

- [ ] Maintainer confirmed Apache-2.0 for software and CC BY 4.0 for repository-authored documentation/data,
   including redistribution rights for tracked model/provider outputs.
- [ ] `LICENSE`, `LICENSE-DATA`, `NOTICE`, and `THIRD_PARTY_NOTICES.md` are present; README and data
   provenance inventory describe the same scope and exclusions.
- [ ] Maintainer reviewed Git history for personal data, local paths, secrets, and files that should not become
      public, then either rewrote history before publication or explicitly accepted the retained history.
- [ ] Packaging metadata, runtime dependencies, optional extras, and included package data are complete.
- [ ] CI executes the full intended test/acceptance surface and exits non-zero on any required failure.

## Repository and policy

- [ ] `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, and `CODE_OF_CONDUCT.md` render correctly.
- [ ] GitHub private vulnerability reporting is enabled.
- [ ] Default branch protection requires current CI checks and blocks force pushes.
- [ ] Issue/PR templates and repository description/topics point contributors to correct support channels.
- [ ] Release tag/version and changelog or release notes identify user-visible changes and known limitations.

## Privacy, secrets, and provenance

- [ ] Current tree and full history were scanned for credentials, private keys, tokens, personal contact data,
      private prompts, absolute local paths, and proprietary inputs.
- [ ] Tracked datasets and cached model outputs have documented provenance and permission for redistribution.
- [ ] Generated output directories remain ignored; no local audit/run output is accidentally staged.
- [ ] Optional provider examples use placeholders only, and logs/screenshots are redacted.

## Fresh-checkout verification

Run from a new clone or clean disposable environment:

```powershell
git status --short
git rev-parse HEAD
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
$env:PYTHONPATH = "src"
python -m pytest -q
python scripts/check_acceptance.py
python run_evidence.py
git diff --check
```

- [ ] Fresh installation succeeds without undeclared local dependencies.
- [ ] Full discovered tests pass; required lanes are not silently skipped.
- [ ] Every acceptance check passes.
- [ ] Evidence runner returns non-zero if any required step fails and generated report records all skips/failures.
- [ ] CLI help, one offline CLI example, and local API/UI startup work from installed package.
- [ ] Frozen gold and blind manifests verify without regeneration.

## Evidence record

Retain with release notes:

- full commit hash and release tag;
- clean-worktree result;
- Python, OS, architecture, dependency-lock or `pip freeze` snapshot;
- test, acceptance, and evidence outputs, including skip reasons;
- hashes of generated reports;
- dataset/manifest versions; and
- model/provider/runtime/hardware identifiers for conditional results.

Interpret all benchmark statements according to [`../EVIDENCE_PACK.md`](../EVIDENCE_PACK.md#10-interpretation-limits).
