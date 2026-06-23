# Role Pair Error Analysis

- Prediction column: `pred_centroid`

## Confusion Pairs

| gold_role | pred_role | count | likely_rubric_boundary |
|---|---|---:|---|
| CLAIM | DEFINE | 3 | CLAIM_DEFINE_BOUNDARY |
| RESULT | CLAIM | 3 | RESULT_CLAIM_BOUNDARY |
| BACKGROUND | CLAIM | 2 | BACKGROUND_CLAIM_BOUNDARY |
| BACKGROUND | EXAMPLE | 2 | MULTIWAY_AMBIGUOUS |
| BACKGROUND | RESULT | 2 | MULTIWAY_AMBIGUOUS |
| DEFINE | CLAIM | 2 | CLAIM_DEFINE_BOUNDARY |
| METHOD | DEFINE | 2 | MULTIWAY_AMBIGUOUS |
| METHOD | CLAIM | 2 | MULTIWAY_AMBIGUOUS |
| RESULT | METHOD | 2 | RESULT_METHOD_BOUNDARY |
| LIMITATION | METHOD | 2 | MULTIWAY_AMBIGUOUS |
| EXAMPLE | METHOD | 2 | METHOD_EXAMPLE_BOUNDARY |
| BACKGROUND | NEXT_STEP | 1 | MULTIWAY_AMBIGUOUS |
| BACKGROUND | LIMITATION | 1 | MULTIWAY_AMBIGUOUS |
| CLAIM | LIMITATION | 1 | LIMITATION_CLAIM_BOUNDARY |
| CLAIM | BACKGROUND | 1 | BACKGROUND_CLAIM_BOUNDARY |
| CLAIM | METHOD | 1 | MULTIWAY_AMBIGUOUS |
| DEFINE | METHOD | 1 | MULTIWAY_AMBIGUOUS |
| METHOD | EXAMPLE | 1 | METHOD_EXAMPLE_BOUNDARY |
| METHOD | RESULT | 1 | RESULT_METHOD_BOUNDARY |
| RESULT | DEFINE | 1 | MULTIWAY_AMBIGUOUS |
| RESULT | EXAMPLE | 1 | MULTIWAY_AMBIGUOUS |
| RESULT | BACKGROUND | 1 | MULTIWAY_AMBIGUOUS |
| LIMITATION | EXAMPLE | 1 | MULTIWAY_AMBIGUOUS |
| LIMITATION | CLAIM | 1 | LIMITATION_CLAIM_BOUNDARY |
| NEXT_STEP | BACKGROUND | 1 | MULTIWAY_AMBIGUOUS |
| NEXT_STEP | CLAIM | 1 | MULTIWAY_AMBIGUOUS |
| NEXT_STEP | METHOD | 1 | NEXT_STEP_METHOD_BOUNDARY |
| NEXT_STEP | RESULT | 1 | MULTIWAY_AMBIGUOUS |
| NEXT_STEP | DEFINE | 1 | MULTIWAY_AMBIGUOUS |
| EXAMPLE | DEFINE | 1 | MULTIWAY_AMBIGUOUS |

## Examples By Top Pair

### CLAIM -> DEFINE (3)

- `HELDOUT2_S0014`: A retrieval trace matters because answer support depends on the path, not merely on a cited passage.
- `HELDOUT2_S0015`: Agent memory can amplify stale assumptions when route provenance is absent from recall.
- `HELDOUT2_S0020`: An audit trail without answer support is evidence of activity rather than evidence of reliability.

### RESULT -> CLAIM (3)

- `HELDOUT2_S0042`: Release reviewers resolved blocked decisions faster when caveats appeared beside the evidence packet.
- `HELDOUT2_S0044`: Memory routing returned older but more relevant context for tasks with hidden state dependencies.
- `HELDOUT2_S0048`: Audit trail inspection showed that answer support was present in seven of nine release decisions.

### BACKGROUND -> CLAIM (2)

- `HELDOUT2_S0001`: A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise.
- `HELDOUT2_S0009`: A model release governance catalog summarizes approval roles, audit trails, and release-board terminology.

### BACKGROUND -> EXAMPLE (2)

- `HELDOUT2_S0002`: The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats.
- `HELDOUT2_S0006`: The tool-use security note records common permission-check vocabulary used by incident responders.

### BACKGROUND -> RESULT (2)

- `HELDOUT2_S0004`: A documentation page introduces retrieval trace diagrams for teams that have never used route labels.
- `HELDOUT2_S0008`: The evidence selection primer explains how policy context can affect which passages are useful to reviewers.

### DEFINE -> CLAIM (2)

- `HELDOUT2_S0024`: Model release governance denotes the approval practice linking evaluation findings to launch decisions.
- `HELDOUT2_S0029`: Control surface labels the places where safeguards can change model, tool, or data behaviour.

### METHOD -> DEFINE (2)

- `HELDOUT2_S0033`: Map consent records to permission checks before selecting evidence for a privacy-sensitive answer.
- `HELDOUT2_S0039`: Store audit trail entries beside answer support so later reviewers can reproduce the decision.

### METHOD -> CLAIM (2)

- `HELDOUT2_S0034`: Rank memory candidates by route dependency, source age, and whether the task needs hidden state.
- `HELDOUT2_S0036`: During an incident review, connect symptoms to retrieval traces and then to the control that failed.

### RESULT -> METHOD (2)

- `HELDOUT2_S0045`: Tool-use security review found that missing permission logs explained most rejected actions.
- `HELDOUT2_S0047`: Human reviewers agreed more often when the retrieval trace displayed rejected evidence as well as accepted evidence.

### LIMITATION -> METHOD (2)

- `HELDOUT2_S0056`: Permission checks are not enough when the tool output can leak private data through a later route.
- `HELDOUT2_S0057`: Human review is constrained when audit trails omit rejected evidence and reviewer rationale.
