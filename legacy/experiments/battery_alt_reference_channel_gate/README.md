# battery_alt_reference_channel_gate — v02

An independent replication substrate for the safety-certification limit theorem, on the
NASA/UCF **Accelerated Life Testing** battery dataset (Fricke, Nascimento & Viana, 2023,
MIT licence, 26 packs), plus a held-out-arm test (**G7**) on NASA **Randomised Walk**.

Everything here is reported as run. The two headline items are a **failed feasibility
gate** and a **null result**; both are kept, and neither was repaired by retuning.

## What is in here

| | |
|---|---|
| **G0** | The registered v01 design (policy axis over five current bins) is **not estimable** on this dataset. Loads are assigned per pack, never per mission. Recorded, not repaired. |
| **v02** | A different experiment on the same data: grade a pack by its hazard rate under its own operational load, and certify it from its **standardised 2.52 A reference discharge**. This is the paper's own OTA setting — cheap bench probe, field hazard. |
| **G1–G4, G6, G9** | All pass, exactly, on 16 packs and 30 (K, n) points. |
| **Permanent obstruction** | Hull intersection at n = 1 without a pairwise collision, closing at a finite n⋆ — the direct empirical instance of the distinction the theory chapter draws. |
| **Null** | The reference channel does **not** separate grades better than a permuted-label null (p = 0.206). Reported as a negative result. |
| **G7** | Fails the registered criterion on NASA RW, and the package shows why the failure cannot be attributed to policy transport in that dataset. |

Read `results/GATE_REPORT.md` first, then `docs/ERRATA.md`.

## Layout

```
config/registered.json            v01, frozen, G0 FAILED (kept)
config/registered_v02.json        v02, frozen
config/errata_corrections.json    four corrections to the v02 gate text, hashed
config/rw_registered.json         the NASA RW package's frozen config, used by G7
docs/FROZEN_PROTOCOL.md           v01 protocol (kept)
docs/PROTOCOL_v02.md              v02 protocol
docs/ERRATA.md                    every deviation, including my own errors
src/alt_gate/core.py              exact hull TV, exact max-min decisiveness, Sion gap
scripts/01..08                    pipeline, in order
tests/test_core.py                regression tests, incl. the two bugs from earlier packages
results/                          every number quoted anywhere in the package
```

## Reproduce

```bash
pip install -r requirements.txt
bash scripts/00_download_and_extract.sh ./data/raw
RW_STEPS=/path/to/rw_steps.parquet bash scripts/run_all.sh
```

`scripts/build_manifest.py` / `verify_manifest.py` check byte reproducibility. Wall-clock
timings are deliberately kept out of every hashed file.

## Data

- Battery ALT: <https://data.nasa.gov/docs/legacy/battery_alt_dataset.zip>, MIT.
  K. Fricke, R. G. Nascimento, F. A. C. Viana, *An accelerated Life Testing Dataset for
  Lithium-Ion Batteries with Constant and Variable Loading Conditions*, v0.0.1, 2023.
- NASA Randomised Walk: see the `nasa_randomized_usage_gate` package.
