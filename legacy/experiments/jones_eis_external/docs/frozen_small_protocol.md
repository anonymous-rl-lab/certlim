# Frozen small protocol: Jones EIS, 35 °C development domain

Status: **frozen before any predictive or geometric model fit** on 2026-08-25.

## Scope

This is a development-stage external-data gate. It tests whether a pre-action EIS channel adds finite-sample information beyond an extended history of old telemetry. It does **not** claim that Jones contains direct labels for field safety, that a single future outcome is a causal risk parameter, or that repeated cycles from one cell are independent experimental units.

The 25 °C chemistry-2 archive remains untouched and is reserved for a later confirmation gate.

## Registered chronology and endpoint

For every record, evidence is acquired in the order

1. pre-charge EIS;
2. realized two-stage randomized charge action;
3. discharge action and capacity outcome.

The operational event is

\[
Y=\mathbf 1\{Q_{\mathrm{discharge}}/Q_{0}<0.50\}.
\]

This is called *severe under-delivery*, not a battery-safety event.

## Evidence menus

- `old_snapshot`: cycle index, previous delivered capacity, cumulative throughput, open-circuit voltage, and the current charge/discharge action.
- `old_history`: `old_snapshot` plus five prior capacities and three prior action triplets.
- `old_history_eis`: `old_history` plus the 200-dimensional real/negative-imaginary EIS spectrum measured before the action.
- `old_history_eis_permuted`: the same dimensions, with EIS permuted across cycles within each cell before splitting.

No hyperparameter search is permitted. The fixed model and all thresholds are in `config/small.json`.

## Evaluation

All train/calibration/test partitions are cell-disjoint: 8/4/4 cells, repeated five times from the registered seed. Calibration sets determine the Certify/Alert/Reject thresholds with nominal \(\alpha=\beta=0.10\). Test reporting includes AUC, Brier score, balanced decisiveness, and both directional errors.

The geometry diagnostic forms environments from cell × 20-cycle windows. Windows with at least ten observations are graded Safe when empirical event risk is at most 0.30 and Unsafe when it is at least 0.70; the rest are buffer environments. An eight-bin label-free quantizer and an exact linear program estimate the discrete plug-in \(\widehat\Delta_E(n)\) for \(n=1,2,3\). This diagnostic is exploratory because grades and evidence distributions come from the same finite development domain.

## Interpretation rule

A failed gate is a scientific result and is not repaired by retuning. Passing the development gate licenses downloading and running the untouched 25 °C confirmation domain; it does not by itself validate the causal-certification theorem.
