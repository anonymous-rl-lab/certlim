# Policy-specific certification and matched controls

This retrospective extension uses the NASA stage-policy interval tables and whole-cell grade file from the accompanying reconstruction. It fits rules on a registered family of laws. The 14-cell physical holdout is evaluated separately in Supplementary Section S9.

Run `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run.py` to rebuild the eight output tables and `python verify.py` to independently verify every delivered stage-policy lookup. Package requirements are listed in `../NASA_chain_v2/requirements.txt`.

| Output | Meaning |
|---|---|
| registration.csv | Models and contributing cells per grade under missing-only and simultaneous rate uncertainty. |
| cutoff.csv | Binomial cutoff-only lower and upper optima at one and five observations. |
| comparison.csv | Feasible lower value, stationary-grid upper value and both worst-case side errors for every matched method. Values are probabilities. |
| lookups.csv | Probabilities of Certify, Reject and Alert conditional on four count components, grouped by analysis, policy, block length and method. |
| dependence.csv | Pooled five-draw optima and errors with the allowed common-symbol mixture weight ranging from zero to the indicated cap. |
| cell_policy_grades.csv | Equal-stage-weight joint-mass bounds and grades for 84 cell-policy models under each uncertainty definition. |
| cell_policy_summary.csv | Whole cell-policy grade counts and five-draw optimality bounds wherever both grades are represented. |
| rank_resolution.csv | Classwise physical calibration counts and the smallest possible nonrandomized conformal p-value using all available training cells. |

Lower values come from a rule feasible on every tensor Bernstein coefficient vector. Upper values optimize over stationary grid laws inside each rectangle. The solver checks every constraint after each fit, then scales inward to address floating-point tolerance. `verify.py` checks the delivered probabilities by using binomial and hypergeometric probabilities to construct the coefficient evaluations independently. Supplementary Section S11 gives the estimands, baseline definitions and interpretation.
