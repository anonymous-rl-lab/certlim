# Jones EIS small development-gate report

**Overall registered gate: FAIL**

> This is a development result for severe under-delivery, not a field-safety label or a confirmatory causal claim.

> The independent-quantizer delta table is retained for provenance but withdrawn for cross-menu comparison. Use the nested-geometry report.

## Cell-disjoint predictive and three-decision results

Median over five registered 8/4/4 cell splits.

| menu | auc | brier | coverage | balanced_decisiveness | unsafe_certify_error | safe_reject_error |
|---|---:|---:|---:|---:|---:|---:|
| old_history | 0.969 | 0.093 | 0.978 | 0.974 | 0.014 | 0.090 |
| old_history_eis | 0.919 | 0.160 | 0.954 | 0.945 | 0.201 | 0.105 |
| old_history_eis_permuted | 0.943 | 0.159 | 0.953 | 0.903 | 0.123 | 0.076 |
| old_snapshot | 0.975 | 0.086 | 0.958 | 0.953 | 0.014 | 0.105 |

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

## Every split

No synthetic median row is interpreted as an observed split.

| split | menu | auc | brier | coverage | balanced_decisiveness | unsafe_certify_error | safe_reject_error |
|---|---|---:|---:|---:|---:|---:|---:|
| 0 | old_snapshot | 0.975 | 0.068 | 0.973 | 0.954 | 0.132 | 0.034 |
| 0 | old_history | 0.978 | 0.076 | 0.995 | 0.989 | 0.149 | 0.038 |
| 0 | old_history_eis | 0.950 | 0.158 | 0.833 | 0.777 | 0.011 | 0.088 |
| 0 | old_history_eis_permuted | 0.953 | 0.159 | 0.995 | 0.994 | 0.115 | 0.076 |
| 1 | old_snapshot | 0.926 | 0.112 | 0.958 | 0.953 | 0.117 | 0.157 |
| 1 | old_history | 0.926 | 0.110 | 0.978 | 0.974 | 0.123 | 0.154 |
| 1 | old_history_eis | 0.858 | 0.174 | 0.990 | 0.987 | 0.201 | 0.150 |
| 1 | old_history_eis_permuted | 0.891 | 0.172 | 0.895 | 0.866 | 0.123 | 0.169 |
| 2 | old_snapshot | 0.979 | 0.095 | 0.941 | 0.914 | 0.007 | 0.105 |
| 2 | old_history | 0.969 | 0.098 | 0.911 | 0.895 | 0.007 | 0.090 |
| 2 | old_history_eis | 0.920 | 0.160 | 0.993 | 0.980 | 0.331 | 0.105 |
| 2 | old_history_eis_permuted | 0.943 | 0.156 | 0.943 | 0.865 | 0.534 | 0.027 |
| 3 | old_snapshot | 0.982 | 0.086 | 0.938 | 0.908 | 0.007 | 0.103 |
| 3 | old_history | 0.978 | 0.093 | 0.931 | 0.912 | 0.007 | 0.088 |
| 3 | old_history_eis | 0.891 | 0.172 | 0.921 | 0.841 | 0.366 | 0.073 |
| 3 | old_history_eis_permuted | 0.895 | 0.172 | 0.953 | 0.903 | 0.662 | 0.042 |
| 4 | old_snapshot | 0.963 | 0.077 | 0.972 | 0.960 | 0.014 | 0.188 |
| 4 | old_history | 0.968 | 0.080 | 0.990 | 0.988 | 0.014 | 0.168 |
| 4 | old_history_eis | 0.919 | 0.146 | 0.954 | 0.945 | 0.083 | 0.120 |
| 4 | old_history_eis_permuted | 0.955 | 0.141 | 0.995 | 0.986 | 0.041 | 0.108 |

## Corrected scientific checks

| Check | Result |
|---|---:|
| auc_gain_vs_old_history | FAIL |
| brier_reduction_vs_old_history | FAIL |
| new_menu_side_errors | FAIL |
| auc_gain_vs_permuted_eis | FAIL |

## Evidence cost

- Median observed EIS acquisition time: 296.2 s
- 90th percentile: 298.3 s
- These are physical acquisition-time costs only; monetary and operational-integration costs are not in the dataset.
