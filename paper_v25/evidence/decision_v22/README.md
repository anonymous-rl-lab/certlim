# Acquisition, transfer and sensitivity calculations

Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python evidence/decision_v22/run_audit.py` from the package root after rebuilding the two earlier evidence layers. Inputs and outputs are all included. These are retrospective analyses on the existing NASA cohort.

| Output | Interpretation |
|---|---|
| procurement.csv | Eight five-draw protocol/uncertainty combinations. The upper end of cutoff-only decisiveness and the feasible lower end for current plus cutoff delimit the acquisition window. Gains and residual gaps are in percentage points. Other numerical probability fields and the recovered fraction are on the 0–1 scale. Empty fields indicate an absent grade, an unfitted comparator, or an uncertified nonnegative recovered fraction. |
| transfer.csv | One-reading whole-cell source and target distances, grade-specific symmetric Hausdorff shifts, geometric lower margin and held-out worst-case bounds of the frozen source rule. Distances and probabilities use the 0–1 scale. |
| deletion.csv | Remove each individual cell and its stages from the fixed-rate high-current registry; refit both channel rules on that reduced registry. This is a sensitivity of the design optimum. |
| timing.csv | On common eligible records, keep target voltage weights fixed and re-estimate strata, grades and both rules for each context proxy. Here retained_steps counts matched records before the stage eligibility threshold. |
| grade_example.csv | The high-current stage with the smallest simultaneous upper risk bound. Risk endpoints on the 0–1 scale. |

The shared confidence-graded registry includes 276 stage-policy objects. The physical target contains 14 different held-out cells, including eight graded safe and two graded unsafe. The identifiers for the two error statistics that round to about 5.63% are whole_cell_certificate.csv (test14_frozen, unsafe_to_certify) and the maximum held-out unsafe-stage average of the four-reading exploratory tie-broken rule (Supplement S9.2). Statistical coverage is subject to the sampling assumptions in S5 and S11.

## Independent validation status

The step-level sensitivities reuse NASA cells and target weights. ALT tests a thermal endpoint and PulseBat tests a different measurement menu. An additional same-protocol cell batch with independently gradeable safe and unsafe classes, paired cutoff and current measurements and matched observation horizon was not established for this release. For a future test of high-current measurement value, lock the physical action, pre-action context, endpoint/horizon, reference/evaluation split by cell, grading region, both 5% error limits and useful decisiveness target before opening the evaluation outcomes. Report an interval for the gain on the same target class and the number of distinct cells per grade. If assessing deployment of a source lookup instead, freeze its probabilities before evaluating the target's error bounds.
