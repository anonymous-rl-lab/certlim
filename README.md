# Finite-Evidence Limits for Causal Safety Certification in Battery Management Systems

**Paper v25 · reproduction bundle v25-R1 · certlim 0.2.1.** This release combines the paper's experiments with the audited Python wheel and source distribution. Run commands below from the repository root. Use Python 3.12 for the reproduction driver. The standalone tool supports Python 3.10–3.13 as tested.

## Verify and install

```sh
python reproduce.py verify
python -m pip install ./packages/certlim-0.2.1-py3-none-any.whl
python reproduce.py verify-tool
```

The first command uses the standard library. It checks the complete distribution file set, SHA-256 digests, and numerical claims in the bundled manuscript and supplement. It reports unlisted, missing and changed files. Git's own metadata is excluded. For a working tree containing generated files, use `verify --working`. That mode permits the documented `raw/` and `replay_runs/` areas and Python bytecode caches. Published evidence tables always remain covered by the manifest. Put virtual environments outside the source tree.

The wheel and the [source distribution](packages/certlim-0.2.1.tar.gz) are the original 0.2.1 artifacts. Their [SHA-256 digests](packages/SHA256SUMS) are pinned. For offline installation in an environment that already provides NumPy and SciPy, use `python -m pip install --no-index --no-deps ./packages/certlim-0.2.1-py3-none-any.whl`. The source distribution includes the tool's project metadata, source, tests, and Chinese quick start.

`verify-tool` checks the installed tool's version and package files against the bundled wheel. It then reads the paper evidence, verifies source digests, recomputes both error bounds and the minimum decision rate of the 24 NASA rules (720 lookup rows), and checks nine CETL, ReLiB and Leaf analysis scopes including their denominators. It prints the measured NASA bounds and each screening workload.

## Reproduce the paper

| Evidence | Starting point | Rebuilt output |
|---|---|---|
| NASA | 389,307 published discharge steps. The ten-column CSV.GZ is included at its paper path. The independent rebuild starts from the original historical Parquet and checks the projection hash. | 57 base result tables, 8 robust-rule tables and 5 measurement/transfer tables. |
| CETL | Original public MAT. Refit, calibrate, freeze, then adjudicate the held-out records. | 7 files, plus a check of the frozen forest. CETL-B decides on 484/1,057 complete and 485/1,400 assigned records. |
| ReLiB | Original 15.5 Ah TAR, and the CETL MAT for the independent scoring check. Seal the blind actions before reading reference discharges. | 6 primary-sample and 5 census files. The census has 5,356 false rejections among 6,907 known qualified records. |
| Leaf | Original C/20 workbook ZIP. Rebuild actions and reference grades by unit and visit. | 8 files. The prior-capacity schedule decides on 31/41 optional visits and 31/88 total visits. The secondary same-visit schedule decides on 65/88. |

```sh
python -m pip install -r requirements-capacity.txt
python -m pip install -r paper_v25/evidence/NASA_chain_v2/requirements.txt
python reproduce.py nasa --work-dir ../tii-replay
python reproduce.py raw --cetl-mat ../raw/CETL-data.mat --relib-tar ../raw/15.5Ah.tar --leaf-zip ../raw/Cby20.zip --work-dir ../tii-replay
```

Both commands use fresh output directories and compare regenerated files byte for byte with their frozen counterparts. Logs and `verification.json` stay in those directories. For one capacity dataset, specify `raw --dataset cetl`, `relib` or `leaf` with the corresponding input arguments. NASA uses PyArrow when available, or pandas/NumPy and Linux `libsnappy.so.1`. Install PyArrow on systems without that library. The paper’s step table can also be used directly at `paper_v25/evidence/NASA_chain_v2/data/nasa_steps.csv.gz`. The command `python reproduce.py prepare-nasa` verifies it or restores it from the original Parquet if missing.

Acquire the capacity inputs as follows. The ReLiB fetcher needs the system `zstd` command. The three raw files occupy about 1.7 GB, with additional space needed during download and replay.

```sh
python paper_v25/evidence/CETL/fetch.py ../raw
python paper_v25/evidence/ReLiB/fetch_relib.py ../raw
python paper_v25/evidence/Leaf/fetch.py ../raw/Cby20.zip
```

## Files and versions

| Location | Use |
|---|---|
| [Paper](paper_v25/TII_MAIN_MANUSCRIPT_v25.md) and [supplement](paper_v25/SUPPLEMENTARY_INFORMATION_v25.md) | The numerical manuscript sources checked here. The separate v25 paper package includes the submission PDFs and complete typesetting assets. |
| `paper_v25/evidence/NASA_chain_v2/`, `review_v21/`, `decision_v22/` | All three are active stages in the **v25** NASA analysis. The suffixes identify when the analyses were introduced. |
| `paper_v25/evidence/CETL/`, `ReLiB/`, `Leaf/` | Protocols, original results, data acquisition and raw replay. The archive hours describe retrospective reference-test workload. |
| `packages/` | Installable certlim 0.2.1 and its matching source distribution. |
| `legacy/` | Historical certlim-repro **0.7.0** inputs and experiments, including ALT, PulseBat, Zhu, Jones and MATR. Use the workspace command below for the original repository entry points and frozen snapshot. |
| [Licenses and data sources](LICENSES.md) | Component-specific notices, software licenses and dataset provenance. |

## Historical reproduction

```sh
python reproduce.py legacy-workspace ../tii-legacy-070
cd ../tii-legacy-070
python -m pip install -r requirements.txt
python reproduce.py --tier verify
```

The export checks all **592** historical files against their original SHA-256 digests before making the workspace available. It recreates 179 frozen reference copies from their matching originals. The PulseBat bootstrap table is supplied as its original 119,960-row CSV in `legacy/experiments/pulsebat_procurement_correction_v02/results/full/soc_menu_samples.csv`. The exported workspace contains both the mutable results and independent frozen files, so the original comparison of numerical, metadata and substantive changes remains available. The compatibility command `python legacy/reproduce.py --tier verify` creates a temporary export automatically. Direct readers of historical file paths and workflows that write results should use the exported tree.

The root [GitHub workflow](.github/workflows/reproduce.yml) verifies a clean checkout, exercises the manifest checker and the bundled tool, rebuilds the NASA tables and checks the exported historical snapshot. The three capacity archives can be replayed separately with the commands above.
