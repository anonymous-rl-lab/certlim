# Audit-locked Jones cross-temperature rerun

Status: **locked before the corrected rerun on 2026-08-26**.

This is a method-corrected diagnostic rerun, not a fresh preregistered confirmation. The 35 °C labels were already inspected in the legacy run. No feature, model hyperparameter, split, endpoint, or numerical success threshold is tuned in this amendment.

## Corrections fixed before rerunning

1. All menu comparisons are paired by registered split: compute the within-split effect first, then summarize the five effects.
2. Both EIS menus receive a within-cell, cycle-permuted EIS control.
   Each real/permuted pair uses the same fitted-model random seed; seed offsets are fixed by menu name rather than iteration order.
3. When source-calibrated one-sided thresholds cross, they are conservatively ordered into a genuine Alert interval. They are never collapsed to a point.
4. The impossible balanced-decisiveness-gain gate is withdrawn and retained in provenance as a legacy design error.
5. Every split is printed. No row is described as a "median split".
6. Predictions, decision counts, paired effects, configuration snapshot, input hashes, software versions, and a numerical manifest are frozen together.

## Interpretation discipline

- Uncontrolled actions-to-EIS improvements are descriptive only.
- The controlled forecast effect is real EIS versus within-cell permuted EIS.
- The certification verdict is governed by transported unsafe-to-Certify and safe-to-Reject errors.
- The rerun may diagnose the already-seen Jones cohort; it cannot restore confirmation status.
