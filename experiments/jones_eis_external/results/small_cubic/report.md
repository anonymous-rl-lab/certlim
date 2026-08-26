# Jones EIS small development-gate report

**Overall registered gate: FAIL**

> This is a development result for severe under-delivery, not a field-safety label or a confirmatory causal claim.

> **Method correction:** the independent-quantizer delta table below is retained for provenance but withdrawn for cross-menu comparison because it does not preserve evidence nesting. Use `results/nested_geometry/summary.json` instead.

## Cell-disjoint predictive and three-decision results

Median over five registered 8/4/4 cell splits.

| menu | auc | brier | coverage | balanced_decisiveness | unsafe_certify_error | safe_reject_error |
|---|---:|---:|---:|---:|---:|---:|
| old_history | 0.969 | 0.093 | 1.000 | 1.000 | 0.014 | 0.148 |
| old_history_eis | 0.919 | 0.160 | 0.954 | 0.945 | 0.201 | 0.105 |
| old_history_eis_permuted | 0.942 | 0.154 | 0.941 | 0.929 | 0.149 | 0.067 |
| old_snapshot | 0.975 | 0.086 | 1.000 | 1.000 | 0.021 | 0.157 |

## Empirical convex-hull separation

| menu | n | median delta | min | max |
|---|---:|---:|---:|---:|
| old_history | 1 | 0.260 | 0.245 | 0.265 |
| old_history | 2 | 0.436 | 0.412 | 0.442 |
| old_history | 3 | 0.526 | 0.504 | 0.538 |
| old_history_eis | 1 | 0.000 | 0.000 | 0.022 |
| old_history_eis | 2 | 0.000 | 0.000 | 0.077 |
| old_history_eis | 3 | 0.000 | 0.000 | 0.090 |
| old_history_eis_permuted | 1 | 0.004 | 0.000 | 0.004 |
| old_history_eis_permuted | 2 | 0.060 | 0.007 | 0.060 |
| old_history_eis_permuted | 3 | 0.089 | 0.016 | 0.089 |

## Registered checks

| Check | Result |
|---|---:|
| auc_gain_vs_old_history | FAIL |
| brier_reduction_vs_old_history | FAIL |
| balanced_decisiveness_gain_vs_old_history | FAIL |
| new_menu_side_errors | FAIL |
| auc_gain_vs_permuted_eis | FAIL |
| delta2_gain_vs_old_history | FAIL |
| delta_monotonicity | PASS |

## Evidence cost

- Median observed EIS acquisition time: 296.2 s
- 90th percentile: 298.3 s
- These are physical acquisition-time costs only; monetary and operational-integration costs are not in the dataset.
