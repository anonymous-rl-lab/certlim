# Jones EIS audit-locked cross-temperature rerun

**Corrected external certification gate: FAIL**

> Method-corrected diagnostic rerun on an already inspected external cohort; not a fresh confirmation.

## Paired effects

Every effect is computed within split before taking the median.

| comparison | rmse_gain_absolute | rmse_gain_fraction | auc_gain | balanced_decisiveness_gain | unsafe_certify_error_change | safe_reject_error_change |
|---|---:|---:|---:|---:|---:|---:|
| eis_actions_vs_actions | 0.0837 | 0.3939 | -0.0447 | -0.4448 | -0.0057 | 0.0847 |
| eis_actions_vs_permuted | 0.0282 | 0.1795 | 0.0020 | 0.1472 | 0.0000 | 0.1171 |
| old_history_eis_vs_old_history | 0.0561 | 0.3202 | -0.0596 | -0.0870 | 0.0029 | 0.3255 |
| old_history_eis_vs_permuted | 0.0227 | 0.1600 | -0.0033 | 0.0758 | -0.0014 | 0.1550 |

## Every registered split

No synthetic median row is interpreted as an observed split.

| split | menu | rmse | auc | alert_rate | unsafe_certify_error | safe_reject_error |
|---|---|---:|---:|---:|---:|---:|
| 0 | actions | 0.2125 | 0.9396 | 0.0620 | 0.0057 | 0.2943 |
| 0 | eis_actions | 0.1288 | 0.8949 | 0.3181 | 0.0000 | 0.3790 |
| 0 | eis_actions_permuted | 0.1570 | 0.8929 | 0.4458 | 0.0000 | 0.2620 |
| 0 | old_history | 0.1753 | 0.9631 | 0.0445 | 0.0000 | 0.2720 |
| 0 | old_history_eis | 0.1192 | 0.9035 | 0.0920 | 0.0029 | 0.5975 |
| 0 | old_history_eis_permuted | 0.1419 | 0.9067 | 0.1415 | 0.0043 | 0.4426 |

## Corrected legacy checks

| Check | Result |
|---|---:|
| eis_actions_rmse_reduction_vs_actions | PASS |
| old_history_eis_rmse_reduction | PASS |
| old_history_eis_auc_gain | FAIL |
| real_eis_beats_permuted_auc | FAIL |
| median_external_side_errors | FAIL |
| strict_all_splits_external_side_errors | FAIL |

## Scope

The balanced-decisiveness gain gate is withdrawn because the legacy baseline was a degenerate two-decision rule. Uncontrolled RMSE gains remain descriptive. Controlled EIS value is evaluated against the paired within-cell permutation arm.
