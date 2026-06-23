# Role Adjudication Review Guide v2 Fresh

## Purpose

This review file supports manual adjudication of ambiguous role labels in the fresh held-out v2 dataset. The goal is to decide whether current `gold_role` labels should be accepted, changed later, or sent for additional review. This step does not create a corrected gold file.

## Model Predictions

Do not trust model predictions blindly. Rule, Naive Bayes, and hybrid predictions are included to reveal disagreement patterns and likely ambiguity boundaries. Treat them as review signals, not votes that automatically override `gold_role`.

## How To Fill The Review CSV

- `adjudicated_role`: leave blank until reviewed, then enter one role: BACKGROUND, CLAIM, DEFINE, METHOD, RESULT, LIMITATION, NEXT_STEP, or EXAMPLE.
- `adjudication_status`: leave blank until reviewed, then use ACCEPT_GOLD, CHANGE_GOLD, NEEDS_SECOND_REVIEW, or RUBRIC_AMBIGUOUS.
- `adjudication_reason`: write a short explanation for the decision, especially when changing or questioning the gold role.
- `rubric_issue`: leave blank until reviewed, then use NONE or one boundary value: CLAIM_DEFINE_BOUNDARY, METHOD_EXAMPLE_BOUNDARY, RESULT_CLAIM_BOUNDARY, BACKGROUND_CLAIM_BOUNDARY, LIMITATION_CLAIM_BOUNDARY, NEXT_STEP_METHOD_BOUNDARY, or MULTIWAY_AMBIGUOUS.
- `review_priority`: prefilled from model agreement. Do not edit unless regenerating the file from the pack.

## Tie-Break Rules

### BACKGROUND vs CLAIM

- BACKGROUND if the sentence mainly describes a source, document, project, page, or context.
- CLAIM if the sentence asserts a reusable thesis that could directly support an answer.

### CLAIM vs DEFINE

- DEFINE if the sentence gives the meaning, boundary, or identity of a term.
- CLAIM if it argues a point about how something behaves or why it matters.

### METHOD vs EXAMPLE

- METHOD if it tells what to do or describes a reusable procedure.
- EXAMPLE if it gives a concrete scenario or instance.

### RESULT vs CLAIM

- RESULT if it reports what a run, evaluation, test, document, or benchmark produced/shows.
- CLAIM if it is a general assertion not tied to a produced/evaluated outcome.

### LIMITATION vs CLAIM

- LIMITATION if the main function is caveat, insufficiency, boundary, failure mode, or constraint.
- CLAIM if the sentence is broader thesis language with negative wording but not mainly a caveat.

### NEXT_STEP vs METHOD

- NEXT_STEP if it proposes future work, a future benchmark, or a follow-up test.
- METHOD if it describes an existing procedure or how to perform a task now.

## Review Order

1. First review P1 rows.
2. Then review rows with `claim_vs_define`, `background_vs_claim`, and `claim_vs_method`.
3. Leave `all_correct` rows until last.

## Status Guidance

- Use ACCEPT_GOLD when `gold_role` is correct under the rubric.
- Use CHANGE_GOLD when the reviewer believes `gold_role` should change later.
- Use NEEDS_SECOND_REVIEW when the row needs another reviewer before a decision.
- Use RUBRIC_AMBIGUOUS when the rubric itself does not resolve the row cleanly.