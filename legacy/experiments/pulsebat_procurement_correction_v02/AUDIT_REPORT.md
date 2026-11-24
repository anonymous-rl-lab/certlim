# PulseBat corrective audit v01

## Verdict

The released numerical results at the registered point are correct, but the
paper-level interpretation was too broad.  Three changes are mandatory:

1. PulseBat must not be presented as a nontrivial convex-hull experiment;
2. the “nameplate/history” arm must be renamed a chemistry-label-only
   constructive negative control;
3. SOC must enter the procurement decision, and the paper must withdraw the
   global active-pulse and physical-Pareto claims.

The frozen `repo_v5` was not edited.  This overlay independently recomputes the
geometry and adds a 40-point SOC×menu uncertainty audit.

## Reproduction and structural audit

- The released experiment manifest passes 28/28 files.
- The corrective implementation reproduces the registered SOC=5%, 0.5C result:
  Δ(1)=0.5272727, permutation (p=0.001), whole-battery bootstrap 95% CI
  [0.3454545, 0.7227273].
- A specialized exact two-block hull solver was checked against the general LP
  on 500 random four-law problems; maximum absolute error was below
  (9\times10^{-16}).
- At the released point estimates, convex-hull Δ equals the minimum
  chemistry-specific pairwise TV for every menu and every registered (n).
  The maximum numerical LP difference is (5.40\times10^{-9}).  Hence PulseBat
  does not test the nontrivial mixture geometry demonstrated by Battery ALT and
  audited by Zhu.
- The registered pulse result is load-bearing on LFP35's 17 decisive batteries
  (9 qualified, 8 unqualified).  Deleting any decisive LMO10 battery leaves
  Δ(1) exactly unchanged; deleting one LFP35 battery yields 0.5000–0.6162.

## Full operating-condition audit

All ten SOC values and four measured menus were recomputed with 999
chemistry-stratified permutations and 2000 whole-battery stratified bootstrap
replicates per point.  Twenty-five of 40 points have permutation (p\le0.01).
The largest point estimate is SOC=10% OCV:

| Experiment | Δ(1) | permutation p | bootstrap 95% CI |
|---|---:|---:|---:|
| SOC=5%, OCV | 0.1455 | 0.572 | [0.0773, 0.5364] |
| SOC=5%, 0.5C pulse | 0.5273 | 0.001 | [0.3455, 0.7227] |
| SOC=10%, OCV | **0.6273** | **0.001** | **[0.4455, 0.7980]** |

The point estimate for SOC=10% OCV is 0.1000 above the registered pulse point,
but a paired whole-battery bootstrap gives a 95% interval
[−0.1864, 0.3773] for the difference.  The data therefore invalidate global
active-pulse superiority but do not prove that SOC=10% OCV has a larger
population Δ than the SOC=5% pulse.

## Cost audit

The frozen cost ledger is valid only for comparisons that share the registered
SOC=5% conditioning path.  It cannot support a cross-SOC Pareto frontier:

- time and maximum C-rate are stored by menu, not by SOC;
- the protocol text counts 1C conditioning in elapsed time;
- the table nevertheless records OCV peak C-rate as zero.

Consequently, the fixed-SOC result remains usable: at SOC=5%, 0.5C has the same
frontier as 1C and 1.5C and lower incremental pulse time/amplitude.  A global
menu×SOC physical Pareto claim is withdrawn until conditioning time, energy,
peak stress, and initial-state assumptions are registered consistently.

## Corrected scientific role

PulseBat remains a positive third experiment, but its role changes from
“active pulse breaks history collision and is globally Pareto-optimal” to:

> Certification information is a property of the complete experiment—sensor,
> excitation, and operating point.  At SOC=5%, active pulses produce a
> significant positive frontier while passive OCV does not; across SOC,
> passive OCV can be equally or more informative.  Higher diagnostic stress is
> therefore neither necessary nor monotonically beneficial.

The chemistry-only arm supplies a constructive exact-collision control.  It is
not empirical evidence about format or use history, and PulseBat does not carry
the paper's nontrivial composite-hull claim.

## Files

- `scripts/audit_pulsebat.py`: deterministic corrective analysis;
- `results/full/soc_menu_uncertainty.csv`: 40-point estimates and certificates;
- `results/full/pairwise_hull_audit.csv`: hull-versus-pairwise audit;
- `results/full/leave_one_out.csv`: load-bearing cohort audit;
- `results/full/paired_contrast_samples.csv`: paired SOC10 OCV minus SOC5 pulse bootstrap;
- `docs/CLAIM_CORRECTIONS.md`: paper-level claim replacements.
