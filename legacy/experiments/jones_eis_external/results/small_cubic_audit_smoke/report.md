# Jones EIS small development-gate report

**Overall registered gate: FAIL**

> This is a development result for severe under-delivery, not a field-safety label or a confirmatory causal claim.

> The independent-quantizer delta table is retained for provenance but withdrawn for cross-menu comparison. Use the nested-geometry report.

## Cell-disjoint predictive and three-decision results

Median over five registered 8/4/4 cell splits.

| menu | auc | brier | coverage | balanced_decisiveness | unsafe_certify_error | safe_reject_error |
|---|---:|---:|---:|---:|---:|---:|
| old_history | 0.974 | 0.076 | 0.968 | 0.948 | 0.115 | 0.029 |
| old_history_eis | 0.960 | 0.140 | 0.833 | 0.735 | 0.006 | 0.139 |
| old_history_eis_permuted | 0.944 | 0.152 | 0.932 | 0.931 | 0.098 | 0.080 |
| old_snapshot | 0.972 | 0.069 | 0.971 | 0.960 | 0.121 | 0.034 |

## Empirical convex-hull separation

| menu | n | median delta | min | max |
|---|---:|---:|---:|---:|
| old_history | 1 | 0.188 | 0.188 | 0.188 |
| old_history_eis | 1 | 0.000 | 0.000 | 0.000 |
| old_history_eis_permuted | 1 | 0.000 | 0.000 | 0.000 |

## Every split

No synthetic median row is interpreted as an observed split.

| split | menu | auc | brier | coverage | balanced_decisiveness | unsafe_certify_error | safe_reject_error |
|---|---|---:|---:|---:|---:|---:|---:|
| 0 | old_snapshot | 0.972 | 0.069 | 0.971 | 0.960 | 0.121 | 0.034 |
| 0 | old_history | 0.974 | 0.076 | 0.968 | 0.948 | 0.115 | 0.029 |
| 0 | old_history_eis | 0.960 | 0.140 | 0.833 | 0.735 | 0.006 | 0.139 |
| 0 | old_history_eis_permuted | 0.944 | 0.152 | 0.932 | 0.931 | 0.098 | 0.080 |

## Corrected scientific checks

| Check | Result |
|---|---:|
| auc_gain_vs_old_history | FAIL |
| brier_reduction_vs_old_history | FAIL |
| new_menu_side_errors | PASS |
| auc_gain_vs_permuted_eis | FAIL |

## Evidence cost

- Median observed EIS acquisition time: 296.2 s
- 90th percentile: 298.3 s
- These are physical acquisition-time costs only; monetary and operational-integration costs are not in the dataset.
