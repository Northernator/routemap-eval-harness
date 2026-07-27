# Contributing to RouteMap

Thanks for helping improve RouteMap. This repository is a research-oriented reliability harness: changes
must preserve its one-sided verdicts, deterministic offline path, locked audit schema, and generated-output
boundaries.

By participating, you agree to follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

## Contribution licensing

By intentionally submitting a contribution for inclusion, you represent that you have the right to submit
it and agree that it is licensed under the license applicable to that part of the repository: Apache-2.0
for software, tests, scripts, schemas, configuration, packaging, automation, and cockpit code; CC BY 4.0
for repository-authored documentation, prompts, examples, benchmark fixtures, annotations, datasets, and
reports. Clearly identify material governed by different terms before submission; maintainers must accept
those terms explicitly.

## Before opening a change

- Use [`SUPPORT.md`](SUPPORT.md) to choose the right discussion or issue path.
- Report vulnerabilities privately as described in [`SECURITY.md`](SECURITY.md).
- Keep changes focused. Discuss broad architecture changes before implementing them.
- Do not include credentials, private prompts, personal data, proprietary datasets, or output you lack
  permission to publish.

## Local setup

From a fresh clone:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

On bash/macOS, activate with `source .venv/bin/activate`. Python 3.11 is the primary verification version;
the package supports Python 3.10+. More detail is in [`docs/RUNNING.md`](docs/RUNNING.md).

## Required design boundaries

- Keep the default path local, offline, and deterministic.
- Compose existing controller and validator packages; do not duplicate routing or checking logic in the harness.
- Verdicts remain one-sided: `RULED_OUT_WRONG`, `NOT_RULED_OUT`, or `UNCHECKABLE`. Never present
  `NOT_RULED_OUT` as proof of correctness.
- Never execute model-produced Python or shell content. Python-code checks parse syntax only.
- Do not weaken `schemas/harness_decision_v1.schema.json` or silently drop audit fields.
- Write generated artifacts only under ignored output locations: `data/outputs/`, `data/runs/`, or `EVIDENCE/`.
- Do not regenerate frozen gold/blind sets in normal test or evidence runners.
- Reuse the exact-compute path for arithmetic escalation; never evaluate model output.

Read [`AGENTS.md`](AGENTS.md) for the complete invariants before changing a validation lane.

## Tests and evidence

Run from the repository root with `src` on `PYTHONPATH` if you did not install editable:

```powershell
$env:PYTHONPATH = "src"
python -m pytest -q
python scripts/check_acceptance.py
git diff --check
```

For a change affecting a lane, runner, evidence claim, or release behavior, also run:

```powershell
python run_evidence.py
```

Add focused regression tests for behavior changes. Lane changes must keep the frozen-gold zero-false-accept
gate green and update evidence documentation when a durable claim changes. Report skips and environment-gated
steps explicitly; a skipped check is not a pass.

## Dependencies

Required dependencies must remain minimal and explicit. Isolate optional integrations in their existing
requirements files. A pull request adding or widening a dependency must explain:

- why standard-library or existing dependencies are insufficient;
- whether it is core, development, API, or hardware/model optional;
- security and maintenance implications; and
- fresh-environment installation evidence.

## Data and benchmark contributions

State provenance, collection method, license/permission, and any privacy review for new data. Prefer small,
reviewable fixtures. Never commit provider credentials, private conversations, customer data, local absolute
paths, or generated outputs containing sensitive prompts. Changes to checksum-locked datasets require
maintainer coordination and a clearly documented new dataset version.

## Pull requests

Keep commits and pull requests narrowly scoped. The pull request should include:

- problem and intended behavior;
- files and invariants affected;
- tests and evidence commands run, with outcomes and skips;
- dependency or dataset changes;
- compatibility or migration notes; and
- screenshots for visible UI changes.

Maintainers may ask for a smaller change, additional falsification cases, or independent evidence before merge.
