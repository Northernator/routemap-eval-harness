# HYBRID_ENTITY_FIELD_DEV_EVAL_V1_REPORT

ABLATION / DEV EVAL. Parameters were selected only on model_train_dev_role.csv seed_train rows, then frozen for heldout_v1_dev and true-blind reads. Locked test files, frozen true-blind files, production ontology, production evaluator, and prior ablations were not modified.

## Frozen Config

```json
{
  "cluster_unlinked": false,
  "k": 6,
  "max_entities_per_seg": 10,
  "selection_metric": "train soft_f1 using M3_fuzzy_difflib@0.6",
  "t_cluster": 0.72,
  "t_link_embed": 0.5,
  "t_link_fuzzy": 0.7
}
```

## Transfer Matrix

| strategy | in_domain_exact_jaccard | in_domain_exact_f1 | in_domain_soft_f1_difflib_0_6 | out_domain_soft_f1_difflib_0_6 | out_domain_soft_f1_embedding_0_5 | in_domain_mean_preds_per_seg | out_domain_mean_preds_per_seg |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ontology_v1 | 0.452083 | 0.523125 | 0.535625 | 0.032507 | 0.033664 | 1.637500 | 0.263889 |
| pure_extractive | 0.023958 | 0.042576 | 0.126022 | 0.467148 | 0.537401 | 8.000000 | 8.000000 |
| hybrid_v1 | 0.102128 | 0.161260 | 0.210754 | 0.223445 | 0.322842 | 5.112500 | 6.277778 |

## Verdicts

| hybrid_keeps_in_domain | hybrid_strict_viable | hybrid_transfers | clustering_run |
| --- | --- | --- | --- |
| false | false | false | false |

## Recommendation

Hybrid_v1 does not yet validate the transfer tradeoff; keep ontology_v1 as default and develop a stronger open-span layer on train/dev.

## Train Sweep

| k | t_link_fuzzy | soft_f1 | soft_precision | soft_recall | soft_jaccard |
| --- | --- | --- | --- | --- | --- |
| 6.000000 | 0.700000 | 0.188379 | 0.152718 | 0.303030 | 0.118373 |
| 6.000000 | 0.600000 | 0.185804 | 0.151583 | 0.300842 | 0.113648 |
| 6.000000 | 0.800000 | 0.181765 | 0.146032 | 0.294613 | 0.113258 |
| 8.000000 | 0.700000 | 0.177913 | 0.135943 | 0.320539 | 0.107754 |
| 10.000000 | 0.700000 | 0.177913 | 0.135943 | 0.320539 | 0.107754 |
| 8.000000 | 0.600000 | 0.176600 | 0.137370 | 0.318855 | 0.106249 |
| 10.000000 | 0.600000 | 0.176600 | 0.137370 | 0.318855 | 0.106249 |
| 8.000000 | 0.800000 | 0.175348 | 0.132107 | 0.319192 | 0.106019 |
| 10.000000 | 0.800000 | 0.175348 | 0.132107 | 0.319192 | 0.106019 |