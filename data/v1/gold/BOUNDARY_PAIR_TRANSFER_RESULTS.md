# Boundary-Pair Transfer Results

## Boundary-Pair Internal Test

- Setting A best accuracy without boundary training: 0.625
- Setting B best accuracy with boundary training: 0.950
- Improvement: +0.325

## Fresh Adjudicated Transfer

| taxonomy | best setting | best model | accuracy | previous best | delta |
|---|---|---|---:|---:|---:|
| fine_8 | base_plus_boundary_train | centroid | 0.532 | 0.456 | +0.076 |
| coarse_5 | base_plus_boundary_train | centroid | 0.620 | 0.582 | +0.038 |
| coarse_4 | base_plus_boundary_train | centroid | 0.696 | 0.633 | +0.063 |
| coarse_3 | base_plus_boundary_train | word_unigram_bigram_nb | 0.823 | 0.810 | +0.013 |

## Full Extraction Transfer

| metric | before | after | delta |
|---|---:|---:|---:|
| role_accuracy | 0.329 | 0.532 | +0.203 |
| strict_full_row_accuracy | 0.000 | 0.000 | +0.000 |
| relaxed_full_row_accuracy | 0.025 | 0.089 | +0.063 |

## Interpretation

Boundary-pair training improves role transfer on the locked fresh adjudicated test, so targeted boundary examples help beyond the boundary-pair internal test.
Entity extraction remains a separate bottleneck because entity predictions were not changed by this role-only transfer experiment.