## Summary

Describe the focused problem and resulting behavior.

## Verification

- [ ] Added or updated focused regression tests
- [ ] `python -m pytest -q`
- [ ] `python scripts/check_acceptance.py`
- [ ] `git diff --check`
- [ ] `python run_evidence.py` when lane/evidence/release behavior changed
- [ ] Reported all skipped or environment-gated checks

Commands and results:

## Safety and compatibility

- [ ] Preserves one-sided verdict semantics
- [ ] Does not execute model output
- [ ] Preserves audit-schema and frozen-dataset invariants
- [ ] Writes generated artifacts only to ignored output directories
- [ ] Documents dependency, dataset, API, or compatibility changes
- [ ] Contains no credentials, personal/private data, or unredacted prompts/logs

## UI changes

Include screenshots and keyboard/mobile verification when applicable.
