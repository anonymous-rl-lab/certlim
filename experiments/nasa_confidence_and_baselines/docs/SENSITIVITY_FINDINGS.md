# Sensitivity findings

Diagnostic layer. Five predictions S1-S5 hashed before the run.

| | statement | verdict |
|---|---|---|
| S1 | cohort registration non-vacuous under every inequality and eta | **holds** |
| S2 | unit registration vacuous under every inequality and eta | **holds** (checked with the exact LP, not the slack bound) |
| S3 | slack bound and exact LP agree within 0.01 | **rejected** |
| S4 | no leave-one-cell-out refit turns the certificate vacuous | **holds** |
| S5 | minimum cross-grade pairwise TV stays above 0.05 at every threshold pair | **holds** |

## S1: the positive certificate is not an artefact of the bound

Cohort registration, nine combinations of inequality and eta:

| | eta=0.01 | eta=0.05 | eta=0.10 |
|---|---|---|---|
| Bretagnolle-Huber-Carol | 0.4788 | 0.4799 | 0.4804 |
| Weissman | 0.4793 | 0.4805 | 0.4810 |
| parametric bootstrap (not a bound) | 0.4812 | 0.4830 | 0.4837 |

Spread 0.0049 across every choice, against a plug-in Delta of 0.4918. The certificate
does not depend on which concentration inequality is used, and the bounds give away
little at this registration: the empirical bootstrap radius is only about 40 per cent
smaller than the analytic one.

## S2: and the negative one is not an artefact of a loose bound

At the unit registration the certificate is vacuous under all nine combinations, and
this was checked by solving the exact linear program over 9,594 expanded generators
per side rather than by the slack bound. Even the bootstrap radius, which is an
empirical quantile and not a guarantee, leaves it vacuous.

## S3 rejected: the conservative relaxation is very conservative

| registration | inequality | eta | slack bound | exact LP | ratio |
|---|---|---|---|---|---|
| cell | BHC | 0.01 | 0.0000 | 0.0506 | vacuous -> non-vacuous |
| cell | Weissman | 0.01 | 0.0000 | 0.0604 | vacuous -> non-vacuous |
| cell | BHC | 0.05 | 0.0070 | 0.0700 | 10.0x |
| cell | Weissman | 0.05 | 0.0176 | 0.0805 | 4.6x |

The bound `Delta - max rho_S - max rho_U` understates the confidence-protected
distance by up to a factor of ten, and in two cases reports a live certificate as
vacuous. A reported certificate must therefore say which of the two it used. The
Supplementary Information already describes the relaxation as conservative; this
puts a number on it.

## S4: not driven by one cell

Twenty-eight leave-one-cell-out refits at the cohort registration: minimum 0.4649,
median 0.4802, maximum 0.4956. All non-vacuous.

## S5: no natural near-collision at any threshold

| thresholds | safe | unsafe | min pairwise TV | hull Delta(1) |
|---|---|---|---|---|
| [0.15, 0.35] registered | 738 | 528 | 0.152644 | 0.149419 |
| [0.10, 0.40] | 595 | 472 | 0.305311 | 0.294420 |
| [0.20, 0.30] | 822 | 583 | 0.086752 | 0.068925 |
| [0.125, 0.375] | 675 | 497 | 0.207051 | 0.207051 |

Narrowing the buffer moves the classes closer, as it must, but the nearest cross-grade
pair stays two orders of magnitude away from collision.

One further observation, not registered in advance: at [0.125, 0.375] the hull distance
equals the minimum pairwise distance exactly, so the class is pairwise-degenerate there,
whereas at the registered thresholds the hull distance is strictly smaller
(0.149419 < 0.152644). Whether the composite geometry is non-trivial is itself a
function of where the buffer is cut.
