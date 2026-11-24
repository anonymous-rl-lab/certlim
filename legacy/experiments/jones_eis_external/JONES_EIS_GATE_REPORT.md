# Jones EIS audit-corrected external gate report

Date: 2026-08-26  
Status: **method-corrected diagnostic rerun; not a new preregistered confirmation**

## Executive verdict

The corrected Jones experiment remains **FAIL** for transported three-decision certification.

Real EIS retains a modest controlled cross-temperature forecasting value, but it does not provide transported safety-critical error control. The strongest external observation is a reversal: EIS materially improves RMSE while degrading binary ranking and increasing unsafe-to-Certify error relative to old history.

| Object | Corrected result |
|---|---:|
| Input and split integrity | PASS |
| 25→35 °C controlled forecast value | Supported diagnostically |
| Real EIS AUC over permuted EIS | Narrow/menu-dependent; not confirmatory |
| Transported three-decision certification | **FAIL** |
| 35 °C within-domain incremental EIS | **FAIL** |
| Nested-geometry execution | COMPLETE; dominance checks are structural invariants |

## 1. Audit corrections

The rerun fixes six defects before model execution:

1. Effects are computed within each of the five registered splits and only then summarized by their median.
2. Both EIS menus receive within-cell cycle-permuted EIS controls.
3. Each real/permuted pair uses the same model random seed.
4. Crossed source-calibration boundaries are conservatively ordered into a genuine Alert interval instead of being collapsed to a point.
5. The impossible balanced-decisiveness-gain gate is withdrawn.
6. Every split, decision count, configuration snapshot, input hash, and software environment is frozen.

The 35 °C labels had already been inspected in the legacy run. Consequently, corrected results are diagnostic and cannot restore untouched-confirmation status.

## 2. Data integrity

The formal inputs are the previously parsed 25 °C and 35 °C cycle tables. Both raw extracted directories were independently re-parsed during this audit:

| Domain | Cells | Complete cycles | Explicit errors | Maximum difference from frozen cycle table |
|---|---:|---:|---:|---:|
| chemistry2-25C | 32 | 3,521 | 57 | \(1.82\times10^{-12}\) |
| chemistry2-35C | 16 | 1,597 | 91 | \(1.82\times10^{-12}\) |

The current workspace copy of the 25 °C ZIP is an incomplete download and was not used in the rerun. This does not alter the model input: the intact extracted raw directory reproduces the frozen table to floating-point tolerance. The input-table SHA-256 values are enforced by the audit configuration.

## 3. Corrected cross-temperature forecast result

Median metric values summarize menus only; no such row is interpreted as an observed "median split."

| Evidence menu | RMSE | AUC | Alert rate | Unsafe→Certify | Safe→Reject |
|---|---:|---:|---:|---:|---:|
| Actions | 0.2116 | 0.9369 | 0.0539 | 0.0171 | 0.2497 |
| EIS + actions | **0.1029** | 0.7315 | 0.0839 | **0.7000** | 0.0702 |
| Permuted EIS + actions | 0.1100 | 0.7751 | 0.0952 | 0.7757 | 0.0033 |
| Old history | 0.1660 | **0.9673** | 0.0495 | **0.0043** | 0.1583 |
| Old history + EIS | **0.0947** | 0.8501 | 0.0858 | **0.5214** | 0.0212 |
| Old history + permuted EIS | 0.1130 | 0.8246 | 0.0445 | 0.6800 | 0.0167 |

### Paired split effects

| Comparison | Median RMSE reduction | Median AUC change |
|---|---:|---:|
| EIS+actions vs actions | 51.20% | −0.2017 |
| EIS+actions vs permuted EIS+actions | **8.21%** | −0.0006 |
| Old-history+EIS vs old history | 40.71% | −0.1172 |
| Old-history+EIS vs permuted EIS | **13.07%** | +0.0237 |

The 51.20% and 40.71% comparisons are uncontrolled descriptions. The controlled EIS effects are 8.21% and 13.07%.

### External-cell bootstrap

| Controlled comparison | Mean absolute RMSE gain | 95% cell-bootstrap CI | Positive cells | Positive splits |
|---|---:|---:|---:|---:|
| EIS+actions over permuted EIS+actions | 0.00938 | [0.00186, 0.01628] | 12/16 | 4/5 |
| Old-history+EIS over permuted EIS | 0.01356 | [0.00632, 0.02004] | 13/16 | 5/5 |

Thus real EIS has nonzero controlled forecasting value, but the effect is much smaller than the former 51.4% headline.

## 4. Certification verdict

The conservative threshold repair removes the degenerate two-decision baseline:

- old-history now produces 490 Alerts across 7,985 split-replicated external predictions;
- all 30 source-calibration menu/split rules retain both one-sided errors at or below 0.10;
- all Certify thresholds are strictly below Reject thresholds.

The external failure nevertheless persists. For old-history+EIS, the median unsafe-to-Certify error is 52.14%, versus the 15% ceiling. Across the five splits it is 0.0000, 0.4729, 0.6786, 0.5214, and 0.5800. Split 0 instead has a 68.23% safe-to-Reject error. The error direction therefore reverses across source partitions.

This is not a threshold-collapse artifact. It is a transport failure.

## 5. Within-domain 35 °C gate

The corrected within-domain cell-disjoint experiment also remains FAIL:

| Menu | AUC | Brier | Unsafe→Certify | Safe→Reject |
|---|---:|---:|---:|---:|
| Old history | 0.9694 | 0.0930 | 0.0138 | 0.0898 |
| Old history + EIS | 0.9191 | 0.1604 | 0.2013 | 0.1055 |
| Old history + permuted EIS | 0.9425 | 0.1592 | 0.1234 | 0.0756 |

The paired median AUC changes are −0.0494 versus old history and −0.0226 versus permuted EIS.

## 6. Nested empirical geometry

Nested dominance is now labeled correctly as a structural invariant. The empirical object is the real-minus-permuted contrast:

| Block length | Median real−permuted \(\widehat\Delta\) | Range | Positive seeds |
|---:|---:|---:|---:|
| 1 | −0.0098 | [−0.0139, 0.0127] | 1/5 |
| 2 | +0.0427 | [0.0293, 0.0692] | 5/5 |
| 3 | +0.0587 | [0.0422, 0.0939] | 5/5 |

Cycle-aligned EIS therefore has no robust single-sample plug-in geometry advantage, but a positive real-versus-permuted advantage emerges for two- and three-sample blocks. This diagnostic is exploratory and is not a population estimate of \(\Delta_E(n)\).

## 7. Scientific conclusion

The audit-corrected result supports the following statement:

> A roughly five-minute EIS channel carries modest cross-temperature capacity-forecast information beyond a within-cell permutation control, but prediction improvement and safety certification move in opposite directions. Better RMSE neither preserves binary ranking nor transports bilateral Certify/Reject error control.

It does not support EIS as a universally valid causal proxy, a successful transported safety certificate, or a fresh confirmatory external PASS.
