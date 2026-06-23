# Role Label Rubric v2

Use this rubric when adjudicating fresh held-out v2 role labels. Assign the role that best describes the sentence's main job in a route, not every possible secondary function.

## Role Definitions

- BACKGROUND: source, document, project, policy, or dataset context. It frames where information comes from or why it exists.
- CLAIM: a substantive thesis, principle, or assertion about a system, risk, method, evidence, or governance practice.
- DEFINE: a term/category explanation. It names what something means, covers, denotes, or is called.
- METHOD: an action, procedure, workflow, or implementation step to perform.
- RESULT: an observed or reported outcome from evaluation, review, benchmark, test, inspection, or document output.
- LIMITATION: a caveat, insufficiency, constraint, boundary, failure mode, or warning.
- NEXT_STEP: proposed future work, future evaluation, future dataset construction, or follow-up testing.
- EXAMPLE: a concrete instance, scenario, case, or illustrative situation.

## Common Confusions

### CLAIM vs DEFINE

- DEFINE names what a term/category means.
- CLAIM argues something about a system, risk, method, or principle.

Examples:

- HELDOUT2_S0021 DEFINE: `Route provenance: the documented lineage connecting source context, selected evidence, and answer support.`
- HELDOUT2_S0014 CLAIM: `A retrieval trace matters because answer support depends on the path, not merely on a cited passage.`
- HELDOUT2_S0029 DEFINE: `Control surface labels the places where safeguards can change model, tool, or data behaviour.`

### METHOD vs EXAMPLE

- METHOD says what to do or how to do it.
- EXAMPLE gives a concrete instance/scenario.

Examples:

- HELDOUT2_S0031 METHOD: `Compare each generated answer against its retrieval trace, then flag unsupported assertions for review.`
- HELDOUT2_S0076 EXAMPLE: `A plugin that reads calendars and sends email illustrates why tool-use security needs separate route checks.`
- HELDOUT2_S0078 EXAMPLE: `A synthetic benchmark row could look procedural while actually describing a concrete reviewer scenario.`

### RESULT vs CLAIM

- RESULT reports an observed/evaluated outcome or expected output of a document/test.
- CLAIM states a thesis or principle.

Examples:

- HELDOUT2_S0041 RESULT: `The evaluation run recovered more answer-support passages after route provenance was kept with the snippets.`
- HELDOUT2_S0011 CLAIM: `AI safety evaluation becomes more credible when disagreement remains traceable instead of hidden behind an average.`
- HELDOUT2_S0050 RESULT: `The mismatch review revealed that policy-context rows were often confused with broad claims.`

### BACKGROUND vs CLAIM

- BACKGROUND gives source/project context.
- CLAIM gives a substantive assertion that can support an answer.

Examples:

- HELDOUT2_S0001 BACKGROUND: `A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise.`
- HELDOUT2_S0007 BACKGROUND: `A benchmark design appendix lists source context, gold labels, and mismatch review artifacts for auditors.`
- HELDOUT2_S0017 CLAIM: `Benchmark design is weaker when easy source context outnumbers adversarial route segments.`

### LIMITATION vs CLAIM

- LIMITATION states a caveat, insufficiency, boundary, or failure mode.
- CLAIM is broader and not mainly about insufficiency.

Examples:

- HELDOUT2_S0052 LIMITATION: `A complete release packet does not prove that the deployed model will behave safely after integration.`
- HELDOUT2_S0058 LIMITATION: `A route benchmark remains incomplete without operational incidents, adversarial examples, and noisy documentation.`
- HELDOUT2_S0012 CLAIM: `Model release governance should treat missing evidence as a decision risk, not as harmless paperwork.`

### NEXT_STEP vs METHOD

- NEXT_STEP proposes future work/evaluation.
- METHOD describes an action or procedure inside the current system.

Examples:

- HELDOUT2_S0064 NEXT_STEP: `The next retrieval test should hide titles and require the extractor to infer route provenance from text alone.`
- HELDOUT2_S0067 NEXT_STEP: `Evaluate whether human review changes final answers when rejected evidence is shown.`
- HELDOUT2_S0038 METHOD: `Route uncertain answers to human review when evidence selection conflicts with the final answer.`

## Adjudication Notes

- Prefer the sentence's main communicative function over isolated trigger words.
- If a sentence contains both a scenario and a recommendation, choose EXAMPLE only when the concrete scenario is the main point.
- If a sentence contains future-looking words but mainly warns about insufficiency, choose LIMITATION.
- Do not change labels automatically from model disagreement alone; use disagreement to prioritize human review.