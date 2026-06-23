# fresh_blind_v2 Dataset Card

fresh_blind_v2 is a deterministic synthetic blind split with de-artifacting checks.

## Generation

- Seed: 20260623
- Offline templates only; no Ollama/provider calls.
- Gold is assigned by construction from segment intent before prediction.
- Banned lexical markers are rejected during generation.
- Gold entities are segment-local noun phrases and must appear verbatim in their segment.

## Domains

- Blood Bank Platelet Allocation
- Interlibrary Loan Queue
- Emergency Shelter Intake
- Veterinary Surgery Roster
- Ferry Terminal Loading
- Pharmacy Compounding Queue
- Fire Hydrant Inspection Rounds
- Hotel Room Turnover Desk
- Recycling Contamination Audit
- Community Sports Fixture Desk

## De-confliction

- Exact overlap with old topics: none
- AI-governance/safety title hits: none

## Balance

- BACKGROUND: 20
- DEFINE: 20
- CLAIM: 20
- METHOD: 20
- RESULT: 20
- LIMITATION: 20
- NEXT_STEP: 20
- EXAMPLE: 20

## Validation Gate

- verbatim_entity_rate: 1.000000
- banned_marker_hit_rate: 0.000000
- entity_vocab_diversity: 0.500000
- telegraph_probe_8role_accuracy: 0.875000

## Caveat

This remains synthetic gold. Use the annotation template for independent human annotation, or build a real external-document blind split before publishing a credible headline.
