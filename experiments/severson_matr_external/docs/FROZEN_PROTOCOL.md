# Frozen protocol: Severson/MATR external certification gate

Frozen at 2026-08-26 before any model was fitted to the downloaded cell records.

## Scientific question

Can an evidence channel with the right structure - an early discharge-voltage-curve change - support externally transported lifetime certification more effectively than a larger amount of scalar cycling telemetry?

This is an evidence-value benchmark, not a causal-effect estimate for charging policy. Charging policy is treated as a registered action descriptor; random assignment is not assumed.

## Units, chronology, and split

- Experimental unit: one physical LFP/graphite cell. Cycles are repeated measurements, never independent samples.
- Outcome: observed cycle life to the dataset endpoint.
- Source fit set: the 41 author-designated training cells from batches 1 and 2.
- Source calibration set: all 43 author-designated primary-test cells from batches 1 and 2, including the reported short-life outlier.
- Locked external set: the 40 author-designated valid cells from batch 3 (2018-04-12).
- The five batch-1 cells continued in batch 2 are merged once and the batch-2 continuation records are removed. The six author-identified noisy/incomplete batch-3 channels are excluded.
- No external-set feature or outcome may be used for fitting, scaling, imputation, model selection, or conformal calibration.

## Three-decision target

- `Reject`: true cycle life at most 800 cycles.
- Buffer band: true cycle life strictly between 800 and 1000 cycles.
- `Certify`: true cycle life at least 1000 cycles.

The 200-cycle band is an explicit benchmark indifference region. No safety guarantee is claimed for cells whose truth lies in the buffer.

## Evidence menus

All cycle-number references use physical cycle numbers after reconciling the raw file index.

1. `protocol`: the two charging C-rates and the state-of-charge switch point.
2. `scalar5`: `protocol` plus fixed scalar summaries of discharge capacity, internal resistance, mean/min/max temperature, and charge time through cycle 5.
3. `scalar100`: `protocol` plus the same scalar channels summarized through cycle 100. This is the registered "more old telemetry" comparator.
4. `curve5`: `scalar5` plus the log absolute minimum and log variance of `Q5(V)-Q4(V)`.
5. `curve100`: `scalar100` plus the same two features from `Q100(V)-Q10(V)`.
6. `curve5_permuted` and `curve100_permuted`: negative controls produced by permuting only the two curve-derived columns within each split with frozen seeds.

Scalar-channel summaries are fixed as start, end, mean, standard deviation, slope, minimum, maximum, and end-minus-start over the registered window. Missing or non-finite values are imputed with source-fit medians only.

## Predictor and uncertainty rule

- Target transformation: `log10(cycle_life)`.
- Predictor: standardized ridge regression.
- Ridge grid: 33 log-spaced values from `1e-4` through `1e4`; alpha is selected by leave-one-out generalized cross-validation on the source fit set only.
- Interval: split-conformal absolute-residual interval calibrated on the primary-test set at nominal 80% marginal coverage. The finite-sample quantile is `ceil((n_cal+1)*0.8)/n_cal` with `higher` interpolation.
- Decision: `Certify` if the lower interval endpoint is at least 1000; `Reject` if the upper interval endpoint is at most 800; otherwise `Alert`.

## Frozen metrics

Regression metrics on the locked external batch:

- RMSE and MAE in cycles;
- mean absolute percentage error (MAPE);
- coefficient of determination;
- 80% interval coverage and mean interval width.

Certification metrics:

- unsafe false-certification rate: `P(Certify | life <= 800)`;
- safe false-rejection rate: `P(Reject | life >= 1000)`;
- unsafe and safe decisiveness separately;
- balanced decisiveness: the mean of those two decisiveness rates;
- buffer-band decision counts, reported without a guarantee.

Exact Clopper-Pearson 95% intervals accompany both conditional side-error rates. These intervals are descriptive under external shift, not a proof of transportability.

## Frozen success gates

- **G0 integrity:** exact split identities, no duplicated physical cell across splits, at least five external unsafe cells and ten external safe cells, and no feature dated after the registered horizon.
- **G1 evidence ordering:** external MAPE for `curve5` is at least 10% lower than external MAPE for `scalar100`.
- **G2 negative control:** `curve5` external MAPE is at least 5% lower than the median MAPE of 200 registered curve-column permutations.
- **G3 non-vacuous certification:** at least one real curve menu has both external conditional side-error rates at most 0.20 and balanced decisiveness at least 0.25.
- **G4 transport calibration:** that same menu has external marginal interval coverage of at least 0.75.

The external gate passes only if G0-G4 all pass. Failed gates are reported as failures; thresholds and evidence menus will not be retuned in this run.

## Compute freeze

- Master seed: `20260826`.
- Negative-control permutations: 200.
- Smoke stage: at most 10 minutes; fixed small subsets are used only for parser and chronology checks.
- Full run: at most one hour on CPU; all 124 registered cells are used once their assigned roles are fixed.
- No GPU and no paid external compute.

## Scope limits

This experiment tests externally transported prediction and three-decision certification. It does not identify the causal effect of a charging protocol, does not prove that the voltage curve is a valid causal proxy in every deployment, and does not convert empirical error control under batch shift into a distribution-free guarantee.
