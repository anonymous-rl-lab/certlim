# Frozen protocol

## Status and scope

This protocol was locked after a feasibility probe.  It is not represented as a
preregistration.  The probe identified the dataset, independent sampling unit,
SOH thresholds, lowest-cost SOC point, and a label-free quantization correction.
No result produced by the released formal pipeline is used to change a gate.

The study is confined to lithium-ion battery management and second-life
qualification.  The sampling unit is a physical retired battery, never a row or
a time point.

## Registered population and truth

The main composite class contains independent retired batteries from two
chemistry/service cohorts:

- 10 Ah LMO pouch cells from HEV use;
- 35 Ah LFP prismatic cells from HEV use.

The gold-standard capacity `Q` is measured by a full CCCV charge followed by CC
discharge.  `SOH=Q/Qn`.  For the registered high-retained-capacity service:

- `Theta_S`: SOH at least 0.90;
- `Theta_U`: SOH at most 0.80;
- buffer: SOH strictly between 0.80 and 0.90.

This is a task-specific qualification margin, not a universal claim that every
cell below 80% SOH is unsafe for every second-life application.

## Evidence menus

The diagnostic operating point is 5% SOC, the first and least costly SOC point
in the released pulse protocol.

- `nameplate`: chemistry, nominal capacity, format and historical-use cohort.
  Safe and unsafe composite classes contain the same two cohort labels, so their
  convex hulls are identical for every sample size.
- `ocv`: passive open-circuit voltage `U1` after the registered rest.
- `pulse_0p5C`: response span `U3-U7` across the positive and negative 0.5C
  pulses.
- `pulse_1C`: response span `U11-U15`.
- `pulse_1p5C`: positive-pulse/relaxation span `U19-U21`.

Within each chemistry and menu, four thresholds are defined by the three
quartiles over **all available physical batteries**, including the buffer band.
SOH and grade labels are never used in quantizer calibration.  Cohort PMFs use a
Jeffreys pseudocount of 0.5 per symbol.

An evidence sample is one independently drawn retired battery from a registered
cohort.  Block size `n` is therefore the number of batteries purchased for
diagnostic sampling—not the number of telemetry rows.

## Physical procurement cost

Cost is frozen in physical units from the released experimental protocol:

- active-test elapsed time per sampled battery;
- maximum applied C-rate;
- number `n` of independently sampled batteries.

At 5% SOC, conditioning requires 3 minutes at 1C and a 10-minute rest.  Each
complete 5-second positive/rest/negative/rest pulse pair adds 160 seconds.  The
reported cumulative elapsed times are 780 seconds for OCV, 940 seconds through
the 0.5C pair, 1100 seconds through the 1C pair, and 1180 seconds through the
positive 1.5C response used here.  No dollar price is assumed.

## Exact estimands

For every menu and `n`, linear programs compute:

- `Delta_E(n)`, the minimum total-variation distance between the safe and
  unsafe convex hulls;
- `D_E(n)`, the optimal worst-cohort probability of a decisive output among all
  randomized Certify/Alert/Reject rules under alpha=beta=0.05.

The uncertainty analysis holds quantizer thresholds fixed, permutes grade labels
within chemistry, and bootstraps whole batteries within chemistry-by-grade
strata.  No row-level bootstrap is permitted.

