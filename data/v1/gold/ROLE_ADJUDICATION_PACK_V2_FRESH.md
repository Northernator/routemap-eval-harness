# Role Adjudication Pack: Fresh Held-Out v2

## Summary

- Total rows: 80
- Rows needing review: 75
- Purpose: support human adjudication of ambiguous role labels without changing gold labels automatically.

## Agreement Patterns

| agreement_pattern | count |
|---|---:|
| all_wrong_different | 21 |
| nb_only_correct | 15 |
| rule_and_hybrid_correct | 14 |
| all_correct | 11 |
| all_wrong_same | 10 |
| nb_and_hybrid_correct | 8 |
| rule_only_correct | 1 |

## Likely Ambiguity Types

| likely_ambiguity_type | count |
|---|---:|
| low_ambiguity | 31 |
| claim_vs_define | 13 |
| background_vs_claim | 9 |
| claim_vs_method | 9 |
| result_vs_claim | 6 |
| method_vs_example | 5 |
| result_vs_method | 5 |
| background_vs_limitation | 1 |
| multiway_ambiguous | 1 |

## Top 15 Rows To Review First

| segment_id | gold | rule | nb | hybrid | pattern | ambiguity | question | text |
|---|---|---|---|---|---|---|---|---|
| HELDOUT2_S0001 | BACKGROUND | CLAIM | CLAIM | CLAIM | all_wrong_same | background_vs_claim | Is this source context, or a substantive claim? | A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise. |
| HELDOUT2_S0009 | BACKGROUND | CLAIM | CLAIM | CLAIM | all_wrong_same | background_vs_claim | Is this source context, or a substantive claim? | A model release governance catalog summarizes approval roles, audit trails, and release-board terminology. |
| HELDOUT2_S0024 | DEFINE | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Model release governance denotes the approval practice linking evaluation findings to launch decisions. |
| HELDOUT2_S0028 | DEFINE | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Audit trail, in this setting, names records that let reviewers reconstruct a release or retrieval decision. |
| HELDOUT2_S0029 | DEFINE | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Control surface labels the places where safeguards can change model, tool, or data behaviour. |
| HELDOUT2_S0034 | METHOD | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Rank memory candidates by route dependency, source age, and whether the task needs hidden state. |
| HELDOUT2_S0042 | RESULT | CLAIM | CLAIM | CLAIM | all_wrong_same | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | Release reviewers resolved blocked decisions faster when caveats appeared beside the evidence packet. |
| HELDOUT2_S0044 | RESULT | CLAIM | CLAIM | CLAIM | all_wrong_same | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | Memory routing returned older but more relevant context for tasks with hidden state dependencies. |
| HELDOUT2_S0056 | LIMITATION | METHOD | METHOD | METHOD | all_wrong_same | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Permission checks are not enough when the tool output can leak private data through a later route. |
| HELDOUT2_S0065 | NEXT_STEP | CLAIM | CLAIM | CLAIM | all_wrong_same | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Run an agent-memory benchmark where old context competes with newer but less relevant evidence. |
| HELDOUT2_S0002 | BACKGROUND | CLAIM | EXAMPLE | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats. |
| HELDOUT2_S0003 | BACKGROUND | CLAIM | NEXT_STEP | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The privacy handbook gives consent examples before turning to any RouteMap annotation task. |
| HELDOUT2_S0006 | BACKGROUND | CLAIM | EXAMPLE | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The tool-use security note records common permission-check vocabulary used by incident responders. |
| HELDOUT2_S0008 | BACKGROUND | CLAIM | LIMITATION | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The evidence selection primer explains how policy context can affect which passages are useful to reviewers. |
| HELDOUT2_S0013 | CLAIM | METHOD | LIMITATION | METHOD | all_wrong_different | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Consent boundaries lose force when downstream permission checks are invisible to the answer composer. |

## All Rows Needing Review

| segment_id | gold | rule | nb | hybrid | pattern | ambiguity | question | text |
|---|---|---|---|---|---|---|---|---|
| HELDOUT2_S0001 | BACKGROUND | CLAIM | CLAIM | CLAIM | all_wrong_same | background_vs_claim | Is this source context, or a substantive claim? | A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric exercise. |
| HELDOUT2_S0002 | BACKGROUND | CLAIM | EXAMPLE | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats. |
| HELDOUT2_S0003 | BACKGROUND | CLAIM | NEXT_STEP | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The privacy handbook gives consent examples before turning to any RouteMap annotation task. |
| HELDOUT2_S0004 | BACKGROUND | BACKGROUND | RESULT | BACKGROUND | rule_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | A documentation page introduces retrieval trace diagrams for teams that have never used route labels. |
| HELDOUT2_S0005 | BACKGROUND | CLAIM | BACKGROUND | BACKGROUND | nb_and_hybrid_correct | background_vs_claim | Is this source context, or a substantive claim? | An agent memory briefing mentions risk, benchmark drift, and long-context failures while setting document scope. |
| HELDOUT2_S0006 | BACKGROUND | CLAIM | EXAMPLE | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The tool-use security note records common permission-check vocabulary used by incident responders. |
| HELDOUT2_S0007 | BACKGROUND | CLAIM | BACKGROUND | BACKGROUND | nb_and_hybrid_correct | background_vs_claim | Is this source context, or a substantive claim? | A benchmark design appendix lists source context, gold labels, and mismatch review artifacts for auditors. |
| HELDOUT2_S0008 | BACKGROUND | CLAIM | LIMITATION | CLAIM | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | The evidence selection primer explains how policy context can affect which passages are useful to reviewers. |
| HELDOUT2_S0009 | BACKGROUND | CLAIM | CLAIM | CLAIM | all_wrong_same | background_vs_claim | Is this source context, or a substantive claim? | A model release governance catalog summarizes approval roles, audit trails, and release-board terminology. |
| HELDOUT2_S0010 | BACKGROUND | BACKGROUND | LIMITATION | BACKGROUND | rule_and_hybrid_correct | background_vs_limitation | Is this a caveat/constraint, or merely background context? | An incident response playbook provides background on escalation records without recommending a new classifier. |
| HELDOUT2_S0011 | CLAIM | CLAIM | CLAIM | CLAIM | all_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | AI safety evaluation becomes more credible when disagreement remains traceable instead of hidden behind an average. |
| HELDOUT2_S0012 | CLAIM | CLAIM | CLAIM | CLAIM | all_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Model release governance should treat missing evidence as a decision risk, not as harmless paperwork. |
| HELDOUT2_S0013 | CLAIM | METHOD | LIMITATION | METHOD | all_wrong_different | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Consent boundaries lose force when downstream permission checks are invisible to the answer composer. |
| HELDOUT2_S0014 | CLAIM | CLAIM | DEFINE | CLAIM | rule_and_hybrid_correct | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | A retrieval trace matters because answer support depends on the path, not merely on a cited passage. |
| HELDOUT2_S0015 | CLAIM | CLAIM | DEFINE | CLAIM | rule_and_hybrid_correct | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Agent memory can amplify stale assumptions when route provenance is absent from recall. |
| HELDOUT2_S0016 | CLAIM | CLAIM | METHOD | CLAIM | rule_and_hybrid_correct | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Controls that never travel with retrieved evidence rarely change practical review behaviour. |
| HELDOUT2_S0017 | CLAIM | LIMITATION | BACKGROUND | LIMITATION | all_wrong_different | background_vs_claim | Is this source context, or a substantive claim? | Benchmark design is weaker when easy source context outnumbers adversarial route segments. |
| HELDOUT2_S0018 | CLAIM | CLAIM | METHOD | METHOD | rule_only_correct | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Human review adds value only if reviewers can inspect the evidence selection path. |
| HELDOUT2_S0019 | CLAIM | CLAIM | CLAIM | CLAIM | all_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Tool-use security depends on permission boundaries being checked at the moment of action. |
| HELDOUT2_S0020 | CLAIM | LIMITATION | DEFINE | LIMITATION | all_wrong_different | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | An audit trail without answer support is evidence of activity rather than evidence of reliability. |
| HELDOUT2_S0021 | DEFINE | CLAIM | DEFINE | CLAIM | nb_only_correct | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Route provenance: the documented lineage connecting source context, selected evidence, and answer support. |
| HELDOUT2_S0022 | DEFINE | CLAIM | DEFINE | CLAIM | nb_only_correct | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Retrieval trace names the visible sequence from question intent through evidence selection to final response. |
| HELDOUT2_S0023 | DEFINE | CLAIM | DEFINE | CLAIM | nb_only_correct | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Consent boundary covers the point at which a permission grant stops applying to a new use. |
| HELDOUT2_S0024 | DEFINE | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Model release governance denotes the approval practice linking evaluation findings to launch decisions. |
| HELDOUT2_S0025 | DEFINE | CLAIM | DEFINE | CLAIM | nb_only_correct | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Agent memory routing describes choosing stored context by dependency rather than by freshness alone. |
| HELDOUT2_S0026 | DEFINE | DEFINE | DEFINE | DEFINE | all_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | A route segment label marks the job a passage performs inside a larger retrieval chain. |
| HELDOUT2_S0027 | DEFINE | DEFINE | DEFINE | DEFINE | all_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Answer support refers to evidence that directly justifies a response rather than merely sharing keywords. |
| HELDOUT2_S0028 | DEFINE | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Audit trail, in this setting, names records that let reviewers reconstruct a release or retrieval decision. |
| HELDOUT2_S0029 | DEFINE | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Control surface labels the places where safeguards can change model, tool, or data behaviour. |
| HELDOUT2_S0030 | DEFINE | CLAIM | METHOD | CLAIM | all_wrong_different | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Human-review checkpoint names a decision point where automated evidence must be inspected before action. |
| HELDOUT2_S0031 | METHOD | CLAIM | METHOD | METHOD | nb_and_hybrid_correct | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Compare each generated answer against its retrieval trace, then flag unsupported assertions for review. |
| HELDOUT2_S0032 | METHOD | CLAIM | EXAMPLE | CLAIM | all_wrong_different | method_vs_example | Is this a procedure to perform, or a concrete example of a procedure? | Before launch, collect release evidence, unresolved limitations, and reviewer sign-off in one packet. |
| HELDOUT2_S0033 | METHOD | METHOD | DEFINE | METHOD | rule_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Map consent records to permission checks before selecting evidence for a privacy-sensitive answer. |
| HELDOUT2_S0034 | METHOD | CLAIM | CLAIM | CLAIM | all_wrong_same | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Rank memory candidates by route dependency, source age, and whether the task needs hidden state. |
| HELDOUT2_S0035 | METHOD | CLAIM | EXAMPLE | CLAIM | all_wrong_different | method_vs_example | Is this a procedure to perform, or a concrete example of a procedure? | Log tool calls with permission scope, selected route segment, and the reason the action was allowed. |
| HELDOUT2_S0036 | METHOD | CLAIM | EXAMPLE | CLAIM | all_wrong_different | method_vs_example | Is this a procedure to perform, or a concrete example of a procedure? | During an incident review, connect symptoms to retrieval traces and then to the control that failed. |
| HELDOUT2_S0037 | METHOD | METHOD | RESULT | METHOD | rule_and_hybrid_correct | result_vs_method | Is this reporting what happened, or describing what to do? | Sample benchmark rows from policy context, operational procedures, examples, and caveats in equal measure. |
| HELDOUT2_S0038 | METHOD | CLAIM | METHOD | CLAIM | nb_only_correct | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Route uncertain answers to human review when evidence selection conflicts with the final answer. |
| HELDOUT2_S0039 | METHOD | CLAIM | DEFINE | CLAIM | all_wrong_different | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | Store audit trail entries beside answer support so later reviewers can reproduce the decision. |
| HELDOUT2_S0040 | METHOD | CLAIM | METHOD | METHOD | nb_and_hybrid_correct | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Label the passage role first, record relation evidence second, and adjudicate entity boundaries last. |
| HELDOUT2_S0041 | RESULT | METHOD | RESULT | METHOD | nb_only_correct | result_vs_method | Is this reporting what happened, or describing what to do? | The evaluation run recovered more answer-support passages after route provenance was kept with the snippets. |
| HELDOUT2_S0042 | RESULT | CLAIM | CLAIM | CLAIM | all_wrong_same | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | Release reviewers resolved blocked decisions faster when caveats appeared beside the evidence packet. |
| HELDOUT2_S0043 | RESULT | METHOD | NEXT_STEP | METHOD | all_wrong_different | result_vs_method | Is this reporting what happened, or describing what to do? | The consent-boundary cases produced fewer false positives once permission checks were separated from general privacy text. |
| HELDOUT2_S0044 | RESULT | CLAIM | CLAIM | CLAIM | all_wrong_same | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | Memory routing returned older but more relevant context for tasks with hidden state dependencies. |
| HELDOUT2_S0045 | RESULT | RESULT | METHOD | RESULT | rule_and_hybrid_correct | result_vs_method | Is this reporting what happened, or describing what to do? | Tool-use security review found that missing permission logs explained most rejected actions. |
| HELDOUT2_S0046 | RESULT | METHOD | RESULT | METHOD | nb_only_correct | result_vs_method | Is this reporting what happened, or describing what to do? | A mixed benchmark split exposed brittle behaviour on examples that looked like procedures. |
| HELDOUT2_S0047 | RESULT | CLAIM | METHOD | METHOD | all_wrong_different | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | Human reviewers agreed more often when the retrieval trace displayed rejected evidence as well as accepted evidence. |
| HELDOUT2_S0048 | RESULT | RESULT | CLAIM | RESULT | rule_and_hybrid_correct | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | Audit trail inspection showed that answer support was present in seven of nine release decisions. |
| HELDOUT2_S0049 | RESULT | CLAIM | BACKGROUND | CLAIM | all_wrong_different | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | Evidence selection improved after source context was grouped by route segment instead of document order. |
| HELDOUT2_S0050 | RESULT | CLAIM | RESULT | RESULT | nb_and_hybrid_correct | result_vs_claim | Is this reporting an evaluation outcome, or making a general claim? | The mismatch review revealed that policy-context rows were often confused with broad claims. |
| HELDOUT2_S0051 | LIMITATION | NEXT_STEP | LIMITATION | NEXT_STEP | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Future benchmark rounds may still overstate generalisation if they reuse the same policy vocabulary. |
| HELDOUT2_S0053 | LIMITATION | CLAIM | LIMITATION | CLAIM | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Consent records can be too stale to justify a fresh tool action even when the interface looks authorized. |
| HELDOUT2_S0054 | LIMITATION | LIMITATION | EXAMPLE | LIMITATION | rule_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Retrieval traces may miss reasoning steps that occur after evidence enters the prompt. |
| HELDOUT2_S0055 | LIMITATION | LIMITATION | CLAIM | LIMITATION | rule_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Agent memory can preserve obsolete source context unless review processes remove or downgrade it. |
| HELDOUT2_S0056 | LIMITATION | METHOD | METHOD | METHOD | all_wrong_same | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Permission checks are not enough when the tool output can leak private data through a later route. |
| HELDOUT2_S0057 | LIMITATION | CLAIM | METHOD | METHOD | all_wrong_different | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Human review is constrained when audit trails omit rejected evidence and reviewer rationale. |
| HELDOUT2_S0060 | LIMITATION | CLAIM | LIMITATION | CLAIM | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Answer support is fragile if relation labels are right but entity boundaries drift across passages. |
| HELDOUT2_S0061 | NEXT_STEP | CLAIM | NEXT_STEP | NEXT_STEP | nb_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Next, assemble a second fresh split from incident reports and release-board minutes. |
| HELDOUT2_S0062 | NEXT_STEP | NEXT_STEP | BACKGROUND | NEXT_STEP | rule_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Future evaluation should compare model release governance rows with ordinary project-management notes. |
| HELDOUT2_S0063 | NEXT_STEP | METHOD | NEXT_STEP | METHOD | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Add consent-boundary examples that mix permission checks with unrelated privacy background. |
| HELDOUT2_S0065 | NEXT_STEP | CLAIM | CLAIM | CLAIM | all_wrong_same | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Run an agent-memory benchmark where old context competes with newer but less relevant evidence. |
| HELDOUT2_S0066 | NEXT_STEP | NEXT_STEP | METHOD | NEXT_STEP | rule_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | A follow-up tool-use security set should include plugins, command execution, and delegated agents. |
| HELDOUT2_S0067 | NEXT_STEP | CLAIM | METHOD | METHOD | all_wrong_different | claim_vs_method | Is this recommending an action, or asserting a broader thesis? | Evaluate whether human review changes final answers when rejected evidence is shown. |
| HELDOUT2_S0068 | NEXT_STEP | CLAIM | NEXT_STEP | CLAIM | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | Build noisy benchmark rows that contain definitions, caveats, and examples in a single paragraph. |
| HELDOUT2_S0070 | NEXT_STEP | LIMITATION | DEFINE | LIMITATION | all_wrong_different | multiway_ambiguous | Which single role best captures the sentence's main job in the route? | Create answer-support cases where the cited passage is relevant but the relation path is wrong. |
| HELDOUT2_S0071 | EXAMPLE | CLAIM | EXAMPLE | EXAMPLE | nb_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | In a hospital triage review, consent evidence and safety evaluation notes can point to different routes. |
| HELDOUT2_S0072 | EXAMPLE | CLAIM | METHOD | CLAIM | all_wrong_different | method_vs_example | Is this a procedure to perform, or a concrete example of a procedure? | Suppose a release board blocks launch because the audit trail lacks reviewer rationale. |
| HELDOUT2_S0073 | EXAMPLE | CLAIM | EXAMPLE | CLAIM | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | When a support chatbot requests a refund-tool call, the permission boundary may depend on account history. |
| HELDOUT2_S0074 | EXAMPLE | CLAIM | EXAMPLE | CLAIM | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | One coding task may need last week's migration note rather than the newest design comment. |
| HELDOUT2_S0075 | EXAMPLE | EXAMPLE | NEXT_STEP | EXAMPLE | rule_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | For instance, a cited paragraph can mention privacy while failing to support the answer's consent claim. |
| HELDOUT2_S0076 | EXAMPLE | CLAIM | METHOD | CLAIM | all_wrong_different | method_vs_example | Is this a procedure to perform, or a concrete example of a procedure? | A plugin that reads calendars and sends email illustrates why tool-use security needs separate route checks. |
| HELDOUT2_S0077 | EXAMPLE | CLAIM | EXAMPLE | CLAIM | nb_only_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | During an incident, an operator might trace a harmful answer through retrieval logs and a stale memory entry. |
| HELDOUT2_S0078 | EXAMPLE | CLAIM | EXAMPLE | EXAMPLE | nb_and_hybrid_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | A synthetic benchmark row could look procedural while actually describing a concrete reviewer scenario. |
| HELDOUT2_S0079 | EXAMPLE | EXAMPLE | EXAMPLE | EXAMPLE | all_correct | low_ambiguity | Do the label and predictions reflect the sentence's main route role? | An auditor comparing two release packets may follow evidence selection differences before reading conclusions. |
| HELDOUT2_S0080 | EXAMPLE | CLAIM | DEFINE | CLAIM | all_wrong_different | claim_vs_define | Is this sentence defining a term, or asserting a thesis about it? | A final answer that cites policy context but omits the controlling route segment shows a support failure. |