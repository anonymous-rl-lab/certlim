# NASA confidence certificate and baseline comparison

Three registered analyses on the frozen NASA randomized-usage artifacts, plus a
diagnostic sensitivity study. Nothing here re-derives the released frontier: the
one quantity shared with it, `Delta(1) = 0.1494191627`, is reproduced by an
independent hull-distance implementation to 3.3e-16 and is used only as a check.

## What is here

| | question | layer |
|---|---|---|
| E1 | is the simultaneous-confidence certificate non-vacuous, and at which registration granularity? | frozen confirmatory |
| E2 | how close does the registered class come to a cross-grade collision without one being constructed? | frozen confirmatory |
| E3 | do conventional methods notice when a channel cannot support a bilateral decision? | frozen confirmatory |
| SENS | how much of E1 and E2 survives changing one assumption at a time? | corrected diagnostic |

Each protocol was hashed before any outcome it governs was computed. `config/`
holds them; `config/erratum_*.json` holds the two corrections E3 required.

## Headline numbers

E1, confidence-protected distance by registration granularity (BHC, eta = 0.05):

| registration | models | median n | max TV radius | Delta(1) | Delta_lower(1) | verdict |
|---|---:|---:|---:|---:|---:|---|
| unit (cell, stage, policy) | 1266 | 590 | 0.2116 | 0.1494 | 0.0000 | vacuous |
| cell (cell, policy) | 92 | 10516 | 0.1901 | 0.2811 | 0.0700 | non-vacuous |
| cohort (policy) | 6 | 152219 | 0.0075 | 0.4918 | 0.4799 | non-vacuous |

Delta rises as the registration coarsens, so pooling gains on both terms at once:
the radius falls and the distance the radius has to be smaller than grows.

E2, over 389,664 cross-grade pairs: minimum pairwise total variation 0.152644,
against a hull distance of 0.149419. The hull distance is strictly smaller, so the
composite geometry of this class is not pairwise-degenerate, and nothing in the
registered class comes near a collision.

E3: on the adversarial channel, where the theorem caps decisiveness at 0.1035 for
n = 5, a likelihood-ratio rule tuned on its own objective reaches 0.943 balanced
accuracy while certifying the worst registered unsafe model 74.7 per cent of the
time. Tuned instead to control that error it drives safe-to-Reject to 1.000. The
conformal selective rule reaches zero side error only by abstaining completely.

A finding outside the registered questions: the constructed collision is exact only
at one unit. Delta(2) = 4.5e-4 and the minimum cross-grade pairwise distance on
that channel is 6.7e-3, so by Theorem 1(3) it cannot be permanent and n_star = 2.
The adversary suppressed one-shot certification but could not make it permanent.

## Running

    python3 scripts/run_e1_e2.py
    python3 scripts/05_dump_adversarial.py     # regenerates the adversarial laws
    python3 scripts/run_e3.py
    python3 scripts/run_sensitivity.py

`scripts/05_dump_adversarial.py` is the released `05_run_L3_adversarial.py` with its
output redirected to a parquet of per-model laws; it is a copy, and the original in
`nasa_randomized_usage_gate/` is untouched. It reproduces the released
`delta_adversarial_min = 0` to 1e-9 under the frozen seed.

## What these results do not say

- E1's non-vacuous certificate is a statement about the cohort registration, not
  about individual cells. Coarsening is a different and weaker claim, and it must be
  justified physically rather than chosen for the certificate it produces.
- E2 is an extremal statement about the registered empirical class. It is not an
  estimate of collision prevalence in any fleet.
- E3 does not show that the baselines are poor predictors. It shows that a predictor
  tuned on its own criterion carries no bilateral guarantee.
- The sensitivity study is diagnostic and cannot reverse E1 or E2.
