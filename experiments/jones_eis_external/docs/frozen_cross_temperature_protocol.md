# Frozen cross-temperature Jones protocol

Status: **frozen before downloading the 25 °C archive and before fitting any cross-temperature model** on 2026-08-25.

## Why this protocol exists

The released Jones experiment trains on chemistry-2 variable-use cells and deploys `eis-actions` on a separate 35 °C cohort. The preceding 35 °C-only small gate answered a different question—whether raw EIS adds to an already strong within-domain telemetry history—and failed. That failure remains unchanged.

This protocol restores the authors' cross-temperature scientific question while adding the evidence-menu and three-decision comparisons required by the v04 framework.

## Domains and leakage barrier

- Training/calibration: all 32 chemistry2-25C cells, split by cell into 24 training and 8 calibration cells.
- Locked external test: all 16 chemistry2-35C cells.
- No 35 °C record is used to select features, thresholds, or model parameters.
- Five registered 25 °C train/calibration partitions are used; the external cohort is evaluated unchanged each time.

## Outcomes

The primary outcome is normalized delivered capacity, \(Q/Q_0\), evaluated by RMSE, MAE, and \(R^2\). The secondary operational event is \(\mathbf 1\{Q/Q_0<0.50\}\), evaluated by AUC and the registered Certify/Alert/Reject errors. Neither outcome is labeled as thermal or field safety.

## Evidence menus

The decisive comparisons are `actions` versus `eis_actions`, and `old_history` versus `old_history_eis`. A within-cell EIS permutation is the negative control. Fixed models, seeds, and numerical gates are recorded in `config/cross_temperature.json`; no hyperparameter search is allowed after the 25 °C archive is inspected.

## Interpretation

Passing shows that this measured pre-action channel improves cross-temperature operational certification under the Jones randomized-use protocol. It does not establish proxy validity in arbitrary SCMs, nor turn observational battery records into a causal ground truth. Failure is retained and reported without retuning.
