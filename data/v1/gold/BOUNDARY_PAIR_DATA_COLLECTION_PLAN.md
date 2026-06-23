# Boundary-Pair Data Collection Plan

## Goal

Collect targeted labelled rows for the role boundaries that dominate fresh adjudicated errors. Use no explicit route headings. Keep fine labels balanced and preserve both easy and adversarial cases.

Minimum target: 25 examples per boundary pair, 200 new rows total minimum.

## CLAIM vs DEFINE

Why hard: both can mention terms and systems; definitions often look like assertions.

Decision rule: DEFINE gives the meaning, boundary, identity, or naming function of a term. CLAIM argues what is true or why it matters.

Prompts:

- Write a sentence defining "route provenance" without using "is defined as".
- Write a thesis about why route provenance matters for answer support.
- Write a sentence naming what "consent boundary" covers.
- Write a claim about consent boundaries failing in downstream tool use.
- Write a definition of "audit trail" and a separate thesis about audit reliability.

Target: 25 new examples.

## RESULT vs CLAIM

Why hard: reported outcomes can sound like general principles.

Decision rule: RESULT reports what a run, evaluation, test, document, benchmark, score, or extractor produced/shows. CLAIM is a general assertion not tied to a produced/evaluated outcome.

Prompts:

- Write a sentence reporting what an evaluation run recovered.
- Write a general claim about why evaluation traceability matters.
- Write a sentence about what a mismatch review revealed.
- Write a sentence stating a principle about mismatch reviews.
- Write an observed outcome from a release-board review.

Target: 25 new examples.

## BACKGROUND vs CLAIM

Why hard: source context can contain risk, policy, or evaluation words that look substantive.

Decision rule: BACKGROUND describes a source, document, project, page, report, benchmark package, README, briefing, or context. CLAIM asserts a reusable thesis that could directly support an answer.

Prompts:

- Write a source-context sentence about a policy overview.
- Write a substantive claim using similar policy terms.
- Write a README context sentence about agent memory.
- Write a claim about agent memory risk.
- Write a benchmark package context sentence that mentions gold labels.

Target: 25 new examples.

## BACKGROUND vs EXAMPLE

Why hard: source descriptions can mention example collections or scenarios.

Decision rule: BACKGROUND frames a document or dataset; EXAMPLE gives a concrete instance or scenario.

Prompts:

- Write a background sentence about a document containing examples.
- Write a concrete scenario involving a reviewer and a release packet.
- Write a source note that mentions example cases.
- Write a scenario involving a support chatbot and permission boundary.
- Write a benchmark appendix context row that names example categories.

Target: 25 new examples.

## BACKGROUND vs RESULT

Why hard: background pages can "show" or "summarize" material without reporting an evaluated outcome.

Decision rule: BACKGROUND describes source context; RESULT reports an observed/evaluated output.

Prompts:

- Write a background sentence about a documentation page introducing diagrams.
- Write a result sentence about a test run recovering passages.
- Write a source note summarizing evaluation topics.
- Write an observed outcome from an error analysis.
- Write a report-context sentence that is not itself a result.

Target: 25 new examples.

## METHOD vs EXAMPLE

Why hard: examples can contain procedural verbs, and methods can mention concrete artifacts.

Decision rule: METHOD tells what to do or describes a reusable procedure. EXAMPLE gives a concrete scenario, user case, model case, or illustrative row.

Prompts:

- Write a procedure for logging tool calls.
- Write a concrete plugin scenario involving calendar and email tools.
- Write a review workflow sentence using evidence selection.
- Write a hospital triage scenario using consent evidence.
- Write a benchmark row that looks procedural but is explicitly illustrative.

Target: 25 new examples.

## RESULT vs METHOD

Why hard: reports of what reviewers did can sound like instructions.

Decision rule: RESULT reports what happened or what was observed. METHOD describes what to do.

Prompts:

- Write a sentence reporting that reviewers agreed more often after seeing rejected evidence.
- Write a procedure telling reviewers to inspect rejected evidence.
- Write a result from audit trail inspection.
- Write an audit procedure for storing support evidence.
- Write a benchmark outcome that mentions examples and procedures.

Target: 25 new examples.

## CLAIM vs METHOD

Why hard: claims often include "should" or action words but function as theses.

Decision rule: CLAIM asserts a broader thesis; METHOD recommends or describes a reusable action.

Prompts:

- Write a claim about human review adding value only under traceability.
- Write a procedure for routing uncertain answers to human review.
- Write a thesis about controls needing to travel with evidence.
- Write a method for collecting release evidence.
- Write a claim using permission-check vocabulary without giving a procedure.

Target: 25 new examples.
