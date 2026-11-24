# Jones EIS audit-locked cross-temperature rerun

**Corrected external certification gate: FAIL**

> Method-corrected diagnostic rerun on an already inspected external cohort; not a fresh confirmation.

## Paired effects

Every effect is computed within split before taking the median.

| comparison | rmse_gain_absolute | rmse_gain_fraction | auc_gain | balanced_decisiveness_gain | unsafe_certify_error_change | safe_reject_error_change |
|---|---:|---:|---:|---:|---:|---:|
| eis_actions_vs_actions | 0.1084 | 0.5120 | -0.2017 | 0.0009 | 0.6957 | -0.1371 |
| eis_actions_vs_permuted | 0.0090 | 0.0821 | -0.0006 | 0.0843 | -0.0757 | 0.0602 |
| old_history_eis_vs_old_history | 0.0650 | 0.4071 | -0.1172 | -0.1052 | 0.5086 | -0.1271 |
| old_history_eis_vs_permuted | 0.0148 | 0.1307 | 0.0237 | -0.0186 | -0.0171 | 0.0022 |

## Every registered split

No synthetic median row is interpreted as an observed split.

| split | menu | rmse | auc | alert_rate | unsafe_certify_error | safe_reject_error |
|---|---|---:|---:|---:|---:|---:|
| 0 | actions | 0.2130 | 0.9436 | 0.0557 | 0.0057 | 0.2999 |
| 0 | eis_actions | 0.1284 | 0.9366 | 0.3381 | 0.0000 | 0.3278 |
| 0 | eis_actions_permuted | 0.1546 | 0.9424 | 0.4233 | 0.0000 | 0.2297 |
| 0 | old_history | 0.1753 | 0.9721 | 0.0495 | 0.0000 | 0.2876 |
| 0 | old_history_eis | 0.1192 | 0.9258 | 0.1371 | 0.0000 | 0.6823 |
| 0 | old_history_eis_permuted | 0.1425 | 0.9289 | 0.1453 | 0.0000 | 0.4738 |
| 1 | actions | 0.2103 | 0.9376 | 0.0438 | 0.0043 | 0.3946 |
| 1 | eis_actions | 0.0989 | 0.8024 | 0.1115 | 0.7000 | 0.0100 |
| 1 | eis_actions_permuted | 0.1065 | 0.7751 | 0.0952 | 0.7757 | 0.0000 |
| 1 | old_history | 0.1597 | 0.9673 | 0.0307 | 0.0000 | 0.3188 |
| 1 | old_history_eis | 0.0947 | 0.8501 | 0.1547 | 0.4729 | 0.0111 |
| 1 | old_history_eis_permuted | 0.1063 | 0.8376 | 0.1641 | 0.4900 | 0.0089 |
| 2 | actions | 0.2106 | 0.9332 | 0.0764 | 0.0200 | 0.2029 |
| 2 | eis_actions | 0.1029 | 0.7315 | 0.0839 | 0.7257 | 0.0312 |
| 2 | eis_actions_permuted | 0.0999 | 0.7867 | 0.0570 | 0.8014 | 0.0033 |
| 2 | old_history | 0.1538 | 0.9598 | 0.0432 | 0.0729 | 0.1338 |
| 2 | old_history_eis | 0.0917 | 0.8219 | 0.0770 | 0.6786 | 0.0067 |
| 2 | old_history_eis_permuted | 0.0939 | 0.7961 | 0.0426 | 0.6800 | 0.0145 |
| 3 | actions | 0.2118 | 0.9369 | 0.0520 | 0.0186 | 0.2497 |
| 3 | eis_actions | 0.1034 | 0.7223 | 0.0513 | 0.6671 | 0.1148 |
| 3 | eis_actions_permuted | 0.1133 | 0.7229 | 0.0983 | 0.7671 | 0.0011 |
| 3 | old_history | 0.1660 | 0.9607 | 0.0877 | 0.0129 | 0.1583 |
| 3 | old_history_eis | 0.0982 | 0.8541 | 0.0632 | 0.5214 | 0.0390 |
| 3 | old_history_eis_permuted | 0.1130 | 0.8246 | 0.0445 | 0.6814 | 0.0167 |
| 4 | actions | 0.2116 | 0.9367 | 0.0539 | 0.0171 | 0.2074 |
| 4 | eis_actions | 0.1010 | 0.7210 | 0.0006 | 0.7614 | 0.0702 |
| 4 | eis_actions_permuted | 0.1100 | 0.7081 | 0.0626 | 0.8029 | 0.0100 |
| 4 | old_history | 0.1665 | 0.9728 | 0.0958 | 0.0043 | 0.1550 |
| 4 | old_history_eis | 0.0925 | 0.8230 | 0.0858 | 0.5800 | 0.0212 |
| 4 | old_history_eis_permuted | 0.1150 | 0.7993 | 0.0031 | 0.7671 | 0.0190 |

## Corrected legacy checks

| Check | Result |
|---|---:|
| eis_actions_rmse_reduction_vs_actions | PASS |
| old_history_eis_rmse_reduction | PASS |
| old_history_eis_auc_gain | FAIL |
| real_eis_beats_permuted_auc | PASS |
| median_external_side_errors | FAIL |
| strict_all_splits_external_side_errors | FAIL |

## Scope

The balanced-decisiveness gain gate is withdrawn because the legacy baseline was a degenerate two-decision rule. Uncontrolled RMSE gains remain descriptive. Controlled EIS value is evaluated against the paired within-cell permutation arm.
