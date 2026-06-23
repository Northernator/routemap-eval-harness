# Role Baseline Comparison: Fresh Held-Out v2

## Summary

- Rule v2 role accuracy: 0.325
- Naive Bayes role accuracy: 0.425
- Rule-only wins: 15
- Naive-Bayes-only wins: 23
- Shared failures: 31

## Per-Role Comparison

| role | support | rule_correct | rule_recall | nb_correct | nb_recall |
|---|---:|---:|---:|---:|---:|
| BACKGROUND | 10 | 2 | 0.200 | 2 | 0.200 |
| CLAIM | 10 | 7 | 0.700 | 3 | 0.300 |
| DEFINE | 10 | 2 | 0.200 | 6 | 0.600 |
| METHOD | 10 | 2 | 0.200 | 3 | 0.300 |
| RESULT | 10 | 2 | 0.200 | 3 | 0.300 |
| LIMITATION | 10 | 5 | 0.500 | 6 | 0.600 |
| NEXT_STEP | 10 | 4 | 0.400 | 5 | 0.500 |
| EXAMPLE | 10 | 2 | 0.200 | 6 | 0.600 |

## Where Rule Wins

| segment_id | gold_role | rule_pred | nb_pred | text |
|---|---|---|---|---|
| HELDOUT2_S0004 | BACKGROUND | BACKGROUND | RESULT | A documentation page introduces retrieval trace diagrams for teams that have never used route labels. |
| HELDOUT2_S0010 | BACKGROUND | BACKGROUND | LIMITATION | An incident response playbook provides background on escalation records without recommending a new classifier. |
| HELDOUT2_S0014 | CLAIM | CLAIM | DEFINE | A retrieval trace matters because answer support depends on the path, not merely on a cited passage. |
| HELDOUT2_S0015 | CLAIM | CLAIM | DEFINE | Agent memory can amplify stale assumptions when route provenance is absent from recall. |
| HELDOUT2_S0016 | CLAIM | CLAIM | METHOD | Controls that never travel with retrieved evidence rarely change practical review behaviour. |
| HELDOUT2_S0018 | CLAIM | CLAIM | METHOD | Human review adds value only if reviewers can inspect the evidence selection path. |
| HELDOUT2_S0033 | METHOD | METHOD | DEFINE | Map consent records to permission checks before selecting evidence for a privacy-sensitive answer. |
| HELDOUT2_S0037 | METHOD | METHOD | RESULT | Sample benchmark rows from policy context, operational procedures, examples, and caveats in equal measure. |
| HELDOUT2_S0045 | RESULT | RESULT | METHOD | Tool-use security review found that missing permission logs explained most rejected actions. |
| HELDOUT2_S0048 | RESULT | RESULT | CLAIM | Audit trail inspection showed that answer support was present in seven of nine release decisions. |

## Where Naive Bayes Wins

| segment_id | gold_role | rule_pred | nb_pred | text |
|---|---|---|---|---|
| HELDOUT2_S0005 | BACKGROUND | CLAIM | BACKGROUND | An agent memory briefing mentions risk, benchmark drift, and long-context failures while setting document scope. |
| HELDOUT2_S0007 | BACKGROUND | CLAIM | BACKGROUND | A benchmark design appendix lists source context, gold labels, and mismatch review artifacts for auditors. |
| HELDOUT2_S0021 | DEFINE | CLAIM | DEFINE | Route provenance: the documented lineage connecting source context, selected evidence, and answer support. |
| HELDOUT2_S0022 | DEFINE | CLAIM | DEFINE | Retrieval trace names the visible sequence from question intent through evidence selection to final response. |
| HELDOUT2_S0023 | DEFINE | CLAIM | DEFINE | Consent boundary covers the point at which a permission grant stops applying to a new use. |
| HELDOUT2_S0025 | DEFINE | CLAIM | DEFINE | Agent memory routing describes choosing stored context by dependency rather than by freshness alone. |
| HELDOUT2_S0031 | METHOD | CLAIM | METHOD | Compare each generated answer against its retrieval trace, then flag unsupported assertions for review. |
| HELDOUT2_S0038 | METHOD | CLAIM | METHOD | Route uncertain answers to human review when evidence selection conflicts with the final answer. |
| HELDOUT2_S0040 | METHOD | CLAIM | METHOD | Label the passage role first, record relation evidence second, and adjudicate entity boundaries last. |
| HELDOUT2_S0041 | RESULT | METHOD | RESULT | The evaluation run recovered more answer-support passages after route provenance was kept with the snippets. |

## Shared Failures

| segment_id | gold_role | rule_pred | nb_pred | text |
|---|---|---|---|---|
| HELDOUT2_S0001 | BACKGROUND | CLAIM | CLAIM | A policy overview frames AI safety evaluation as part of institutional risk governance rather than a standalone metric e |
| HELDOUT2_S0002 | BACKGROUND | CLAIM | EXAMPLE | The release archive describes why model approval packets include evidence logs, reviewer notes, and unresolved caveats. |
| HELDOUT2_S0003 | BACKGROUND | CLAIM | NEXT_STEP | The privacy handbook gives consent examples before turning to any RouteMap annotation task. |
| HELDOUT2_S0006 | BACKGROUND | CLAIM | EXAMPLE | The tool-use security note records common permission-check vocabulary used by incident responders. |
| HELDOUT2_S0008 | BACKGROUND | CLAIM | LIMITATION | The evidence selection primer explains how policy context can affect which passages are useful to reviewers. |
| HELDOUT2_S0009 | BACKGROUND | CLAIM | CLAIM | A model release governance catalog summarizes approval roles, audit trails, and release-board terminology. |
| HELDOUT2_S0013 | CLAIM | METHOD | LIMITATION | Consent boundaries lose force when downstream permission checks are invisible to the answer composer. |
| HELDOUT2_S0017 | CLAIM | LIMITATION | BACKGROUND | Benchmark design is weaker when easy source context outnumbers adversarial route segments. |
| HELDOUT2_S0020 | CLAIM | LIMITATION | DEFINE | An audit trail without answer support is evidence of activity rather than evidence of reliability. |
| HELDOUT2_S0024 | DEFINE | CLAIM | CLAIM | Model release governance denotes the approval practice linking evaluation findings to launch decisions. |

## Top Rule Confusions

| gold_role | pred_role | count |
|---|---|---:|
| BACKGROUND | CLAIM | 8 |
| DEFINE | CLAIM | 8 |
| METHOD | CLAIM | 8 |
| EXAMPLE | CLAIM | 8 |
| RESULT | CLAIM | 5 |
| NEXT_STEP | CLAIM | 4 |
| RESULT | METHOD | 3 |
| LIMITATION | CLAIM | 3 |
| CLAIM | LIMITATION | 2 |
| CLAIM | METHOD | 1 |

## Top Naive Bayes Confusions

| gold_role | pred_role | count |
|---|---|---:|
| CLAIM | DEFINE | 3 |
| DEFINE | CLAIM | 3 |
| METHOD | EXAMPLE | 3 |
| RESULT | CLAIM | 3 |
| BACKGROUND | CLAIM | 2 |
| BACKGROUND | EXAMPLE | 2 |
| BACKGROUND | LIMITATION | 2 |
| CLAIM | METHOD | 2 |
| METHOD | DEFINE | 2 |
| RESULT | METHOD | 2 |

## Interpretation

The Naive Bayes baseline is trained only on the existing development data and the earlier held-out v1 gold. It does not use the fresh held-out v2 gold for training. If it beats the rule extractor, the result suggests that even a simple learned bag-of-words baseline generalises better than the tuned rule set. If it fails in similar places, the training data is likely too small or lexically narrow for this role inventory.
