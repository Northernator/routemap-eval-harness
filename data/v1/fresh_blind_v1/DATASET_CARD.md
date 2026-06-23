# fresh_blind_v1 Dataset Card

fresh_blind_v1 is a deterministic synthetic blind split for an internal RouteMap sanity check.

## Generation

- Seed: 20260622
- Default author: seeded templates, offline, no Ollama/provider calls.
- Optional --llm-author can use local Ollama for prose only; gold remains declared by construction, but shared-model contamination risk increases.
- Gold labels are assigned before prediction from declared segment intent, not inferred by the frozen model under test.

## Domains

- EmberDispatch Wildfire Crew Rotation
- TrackWindow Rail Possession Planning
- ColdVault Vaccine Distribution
- PlowGrid Snow Route Salting
- StageTurn Theater Changeover Desk
- HarborScale Seafood Auction Grading
- PlotLedger Cemetery Record Office
- FiberFix Broadband Restoration
- CourtVoice Interpreter Scheduling
- MenuSwitch School Meal Substitutions

## De-confliction

Existing true-blind topics inspected and avoided:
- CivicAid Permit Triage
- ClinicPulse Backlog Monitor
- EventMesh Incident Queue
- FraudSieve Invoice Controls
- GreenLedger Supplier Risk
- GridLens Battery Maintenance
- HarborFlow Container Exceptions
- HeritageVault Catalogue Routes
- LawBrief Disclosure Tracker
- RiverWatch Flood Notes
- RoboInspect Factory Checks
- TutorTrail Learning Routes

Exact selected-topic overlap with existing true-blind topics: none
AI-governance/safety banned-title hits: none

## Balance

- BACKGROUND: 20
- DEFINE: 20
- CLAIM: 20
- METHOD: 20
- RESULT: 20
- LIMITATION: 20
- NEXT_STEP: 20
- EXAMPLE: 20

## Caveat

This is synthetic internal-sanity gold, not a publishable headline benchmark. Use fresh_blind_annotation_template.csv for independent human annotation, or replace this set with real external documents before reporting a credible external number.

## Validator

Compatible true-blind schema validator errors: none
