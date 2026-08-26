# Finite-Evidence Causal Safety Certification for Battery Management Systems

Reproduction repository for the paper. It contains the frozen evidence chain
behind every number, table, and figure in the manuscript and its Supplementary
Information: registered configurations, analysis code, results, protocol and
errata ledgers, and a byte-level manifest for each experiment.

The certification kernel itself is packaged separately:

```bash
pip install certlim
```

## One command

```bash
pip install -r requirements.txt
python3 reproduce.py                 # verify:  manifests, contract tests, every paper number
python3 reproduce.py --tier core     # recompute every result the paper reports
python3 reproduce.py --tier full     # core, plus raw download and feature extraction
python3 reproduce.py --list          # show the stages without running them
```

`make verify`, `make core`, `make full` and `make list` are equivalent.

**`verify` (seconds, no recomputation).** Checks that the released artifacts are
byte-for-byte what the manifests record, that the repository contract tests pass,
and that all 25 headline numbers in the paper still read out of the artifacts they
came from. Run this first: if it fails, recomputation cannot help.

**`core` (recomputation from the processed data in this repository).** Re-runs
every analysis the paper reports, then verifies. It overwrites files under each
experiment's `results/`, so run it on a clean checkout and read `git diff` — an
empty diff is the reproduction claim. Stages are independent, and a failing stage
is reported without stopping the others.

The NASA frontier stage dominates the `core` wall clock, because it solves two
independent linear programs at every block length up to 20 over 1,266 registered
models. `MAX_N=5 python3 reproduce.py --tier core` caps it at five and reproduces
the first rows of Table I in a few minutes; the manifest check then reports the
frontier file as changed, which is expected under a capped run.

**`full`.** Adds the upstream downloads and feature extraction. This needs tens of
gigabytes and the upstream archives, and is the only tier that touches the network.

## What "reproduces" means here

A rerun on another machine legitimately rewrites what each experiment records
*about* the run: its timestamp, its wall clock, and the library versions it ran
under. `scripts/check_reproduction.py` separates those from results that actually
moved, and only the second kind fails the check:

| bucket | meaning |
|---|---|
| `provenance` | timestamps, wall clock, library versions |
| `numeric` | agrees to floating-point tolerance (1e-8 relative) |
| `shortened` | a capped run (`MAX_N`) wrote a prefix of the frozen table |
| `substantive` | a result moved — this is the only failing bucket |

A `core` run of this repository under Python 3.11 / numpy 2.4 / pandas 3.0 /
scipy 1.17, against artifacts frozen under Python 3.12 / numpy 2.3 / pandas 2.2,
leaves 394 of 411 tracked files byte-identical and classifies all 17 that moved as
provenance, numeric, or shortened. No scientific value changed.

`scripts/verify_manifest.py` still answers the strict byte-for-byte question, which
is the right one for a fresh clone that has not recomputed anything.

## Measured stage times

One commodity cloud core, `core` tier, to fix orders of magnitude:

| stage | uncapped | `MAX_N=3` |
|---|---:|---:|
| NASA frontier (Table I, S3) | 555 s | 1 s |
| NASA adversarial collision (27) | 79 s | 79 s |
| Battery ALT null and sweep | 145 s | 145 s |
| adversarial channel laws | 78 s | 78 s |
| PulseBat 40-point grid | 52 s | 52 s |
| everything else | under 40 s each | |

## What is checked

`scripts/check_paper_numbers.py` names each headline claim, the artifact it comes
from, and how the value is read out of it — so a number drifting in the paper and
a number drifting in the artifacts both fail:

```
where     claim                                          paper      artifact
Table I   Delta(1), NASA frontier                       0.1494      0.149419  ok
(27)      adversarial decisiveness                         0.1           0.1  ok
(28)      ALT Delta_{K=2}(1) is zero                      True          True  ok
(30)      diagnostic SOC 10%, OCV                       0.6273      0.627273  ok
S9.1      cohort certificate non-vacuous                  True          True  ok
S9.5      sensitivity prediction S3 rejected             False         False  ok
```

## Layout

| Path | What it holds |
|---|---|
| `experiments/synthetic_gates` | Registered synthetic companion: collision, policy reversal, data-processing control, LP primal--dual agreement |
| `experiments/nasa_randomized_usage_gate` | Primary causal-policy experiment; the frontier of Table I, the adversarial collision of (27) |
| `experiments/battery_alt_reference_channel_gate` | NASA/UCF accelerated life; the finite-order gate closure of (28) |
| `experiments/pulsebat_procurement_external` | PulseBat registered SOC=5% frontier |
| `experiments/pulsebat_procurement_correction_v02` | PulseBat 40-point SOC x menu grid and cohort audit |
| `experiments/zhu_relaxation_external` | Zhu relaxation: pairwise versus composite geometry, pipeline controls |
| `experiments/jones_eis_external` | Jones EIS transport audit |
| `experiments/severson_matr_external` | Severson/MATR transport audit |
| `experiments/nasa_confidence_and_baselines` | Confidence certificate, natural-collision census, baseline comparison, sensitivity |
| `docs/` | Data provenance, claim status, and the frozen verdict ledger |
| `scripts/` | Manifest build and verification, paper-number check |

Every experiment directory is self-contained: its own `config/` (registered before
computation), `docs/` (frozen protocol and errata), `results/`, `tests/`, and
`MANIFEST.sha256`.

## Analysis layers

Every reported quantity carries exactly one label, and the labels bind:

- **frozen confirmatory** — endpoint, units, model classes, evidence menu, quantizer
  and gate fixed before the corresponding computation;
- **corrected diagnostic** — a documented implementation or protocol defect repaired
  without overwriting the frozen output; a corrected result cannot reverse a
  registered verdict;
- **constructive stress test** — optimization deliberately searching for a collision
  or least-favourable mechanism; it establishes existence, not prevalence.

Corrected analyses are stored beside the frozen ones rather than in place of them,
which is why some directories carry both a result and its erratum.
`docs/FROZEN_CONCLUSIONS.zh.md` is the verdict-by-verdict ledger.

## Data

All six cohorts are public and are **not** redistributed here in raw form. The
repository ships the processed tables the analyses actually consume, and each
experiment's `docs/DATA_PROVENANCE.md` records the upstream source, the retrieval
script, and the checksums.

| Cohort | Reference |
|---|---|
| NASA PCoE Randomized Battery Usage | [25] |
| NASA/UCF accelerated life | [26] |
| PulseBat | [27] |
| Zhu voltage relaxation | [28] |
| Jones EIS | [29] |
| Severson/MATR | [2] |

See `THIRD_PARTY_NOTICES.md` for upstream licences.

## Notes for readers of the frozen configurations

Some registered configuration files record their input path under an earlier
repository name (`repo_v6`). Those strings are part of the preregistration record
and are left byte-identical; the analysis scripts resolve the same artifacts at
their current in-repository location.

## Licence

MIT for the code in this repository (see `LICENSE`). The battery datasets remain
under their upstream licences.
