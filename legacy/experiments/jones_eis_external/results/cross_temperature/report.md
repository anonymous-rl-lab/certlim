# Jones EIS cross-temperature report

**Registered external gate: FAIL**

> Training/calibration uses only 25 °C cells. Every reported prediction below is on the locked 35 °C cohort.

| menu | rmse | mae | r2 | auc | brier | coverage | balanced_decisiveness | unsafe_certify_error | safe_reject_error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| actions | 0.212 | 0.186 | 0.179 | 0.937 | 0.146 | 0.946 | 0.920 | 0.017 | 0.250 |
| eis_actions | 0.103 | 0.084 | 0.806 | 0.732 | 0.226 | 0.916 | 0.887 | 0.700 | 0.070 |
| old_history | 0.166 | 0.149 | 0.494 | 0.967 | 0.119 | 1.000 | 1.000 | 0.010 | 0.234 |
| old_history_eis | 0.095 | 0.079 | 0.835 | 0.850 | 0.194 | 0.923 | 0.846 | 0.521 | 0.028 |
| old_history_eis_permuted | 0.112 | 0.095 | 0.769 | 0.823 | 0.194 | 0.959 | 0.916 | 0.680 | 0.014 |

## Registered checks

| Check | Result |
|---|---:|
| eis_actions_rmse_reduction_vs_actions | PASS |
| old_history_eis_rmse_reduction | PASS |
| old_history_eis_auc_gain | FAIL |
| real_eis_beats_permuted_auc | PASS |
| balanced_decisiveness_gain | FAIL |
| external_side_errors | FAIL |

## Scope

The severe-under-delivery label is an operational capacity endpoint. It is not a thermal-runaway or field-safety label, and this experiment does not identify arbitrary counterfactual policies.
