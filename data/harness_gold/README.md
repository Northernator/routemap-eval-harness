# Harness Gold Fixture

Frozen harness acceptance fixture for all lanes.

- `cases.jsonl` contains known-correct and known-wrong examples for each lane.
- `SHA256SUMS` locks fixture bytes. Tests refuse to score if a locked file changes.
- `sound_lane=true` rows enforce zero false accepts and `false_positive_rate == 0.000`.
