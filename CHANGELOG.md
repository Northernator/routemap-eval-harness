# Changelog

Notable user-facing changes are recorded here. RouteMap follows semantic versioning once a release is tagged.

## 0.1.0 — Unreleased

### Added

- Installable `routemap-harness` package with CLI, bundled decision schema, and cockpit HTML.
- Optional API, benchmark, model-matrix, and development dependency groups.
- Local FastAPI cockpit, audit/replay stores, and fail-closed route-and-validate workflows.
- Full CI, acceptance, evidence, packaging, and installed-wheel verification surfaces.
- Contribution, support, security, conduct, issue, pull-request, and release-governance guidance.

### Changed

- Evidence execution now reports every required step and exits non-zero when an executed step fails.
- CI tests supported Python 3.10 and 3.11 with SHA-pinned GitHub Actions.
- Generated audit, run, evidence, build, environment, and secret-bearing files are ignored by default.

### Known limitations

- One-sided validators can establish some wrong outputs; they do not certify accepted outputs as correct.
- Optional provider adapters may send prompts to third parties and can incur cost or privacy exposure.
- Matrix/KV results remain hardware-gated, and several research lanes are characterized negatives.
- Tracked benchmark artifacts retain non-personal local-path provenance from their original runs.
