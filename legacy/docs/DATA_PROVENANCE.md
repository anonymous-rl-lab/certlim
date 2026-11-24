# Data provenance and reconstruction

## Jones EIS external data

- Record: <https://doi.org/10.5281/zenodo.6645536>
- License: CC BY 4.0
- `chemistry2-25C.zip`: 252,266,321 bytes; MD5 `08b0b29d7d74bb51d1c82baf5a7191f9`
- `chemistry2-35C.zip`: 137,996,820 bytes; MD5 `6738937229d9343ede313a4895dc4312`
- Author repository revision audited: `b5c865e25c4a08991e2826d928b30d6d808bf858`

Place downloaded files at:

```text
experiments/jones_eis_external/data/downloads/chemistry2-25C.zip
experiments/jones_eis_external/data/downloads/chemistry2-35C.zip
```

Extract only the `chemistry2-25C/` and `chemistry2-35C/` trees beneath `data/raw/`. Do not treat the `__MACOSX` metadata tree as data. Commands and frozen configurations are in `experiments/jones_eis_external/docs/`.

## Severson/MATR external data

- Paper: Severson et al., “Data-driven prediction of battery cycle life before capacity degradation,” *Nature Energy* 4, 383–391 (2019), DOI `10.1038/s41560-019-0356-8`.
- Official landing page: <https://data.matr.io/1/>
- Official project: <https://data.matr.io/1/projects/5c48dd2bc625d700019f3204>
- Author loading repository audited at commit `1ef13d27c66dc3d73affdaa008fbeba5687b2ea4`.
- BatteryML cross-check audited at commit `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd`.

Official raw inputs used for the frozen run:

| File | Bytes | SHA-256 |
|---|---:|---|
| `MATR_batch_20170512.mat` | 3,025,320,241 | `9d928ab978f0e3c70b31cb833a749fedd35094d01af76475d69b40aa3497f5ba` |
| `MATR_batch_20170630.mat` | 2,007,331,155 | `63ab200d09ecb237fee5ef3a5c5db76e3212e3206a0bd92f769e1427fed338b8` |
| `MATR_batch_20180412.mat` | 3,236,690,412 | `62c30e413b63e6144720e016deed3661fac8468641794a5807b123fe84717998` |

Download commands with immutable file identifiers are provided at:

```text
experiments/severson_matr_external/scripts/download_data.sh
```

Place the files beneath `experiments/severson_matr_external/data/raw/`, then run smoke, extraction and analysis in the order specified in that experiment's README. The compact total package includes `registered_features.csv`, chronology audit, predictions, permutation results and figures, but intentionally omits the 8.2 GB raw files.

No explicit raw-data license was inferred beyond the upstream publication/data availability statements; users remain responsible for upstream terms. The compact package therefore does not redistribute those raw MATLAB files.

## Synthetic gates

The synthetic SCM data are generated analytically by the included code. No external dataset is required. The frozen configuration hash is:

```text
62be13f80dba48f464b53dec8a92865eb6a070acce666b70b33538f927afa9b4
```

The Monte Carlo portion uses 20 frozen seeds, 2,000 simulations per seed, 120 registered parameter/sample-size conditions, and CPU only.

## Zhu voltage-relaxation external data

- Record: <https://doi.org/10.5281/zenodo.6405084>
- License: CC BY 4.0
- Study: Zhu et al., “Data-driven capacity estimation of commercial lithium-ion batteries from voltage relaxation,” *Nature Communications* (2022).

The experiment uses the NCA and NCM subsets whose post-charge relaxation protocol is common across 25/35/45 °C (1,680 s, 15 points, 120 s spacing). The NCM+NCA subset is excluded because its relaxation protocol differs; three truncated NCA cells are also excluded. The compact package contains 118-cell derived features, exclusion records, registered/corrected results and raw-archive SHA-256 values, but not the 5.3 GB extracted raw CSV tree.

Download and verification instructions are in:

```text
experiments/zhu_relaxation_external/scripts/download_data.sh
experiments/zhu_relaxation_external/docs/DATA_PROVENANCE.md
experiments/zhu_relaxation_external/docs/REPRODUCIBILITY.md
```

The v01.1 module retains the frozen protocol/config hashes, the legacy v01 outputs and a separate errata ledger. Its registered verdict is `NOT_ESTABLISHED`; corrected analyses are explicitly `DIAGNOSTIC_ONLY`.

## PulseBat retired-battery pulse-response data

- Upstream repository: <https://github.com/terencetaothucb/Pulse-Voltage-Response-Generation>
- Audited revision: `92aeb9b8a26bc337164401411271fa8eeadf605c`
- Raw-data archive: <https://doi.org/10.5281/zenodo.13360631>
- Associated article: <https://www.nature.com/articles/s41467-024-54454-0>
- Upstream repository license: MIT

Registered source workbooks:

| File | SHA-256 |
|---|---|
| `LMO_10Ah_W_5000.xlsx` | `70820b404b712a3764781e6c6dab1999ea884b0f60028b34ffe11bae1c3db9ba` |
| `LFP_35Ah_W_5000.xlsx` | `3acc96033ba5474171ff8ddd0eef159e37e10034473e33814fd8aa398e4d7538` |

The compact repository includes `experiments/pulsebat_procurement_external/data/processed/observations.csv`, a mechanical 151-battery table with capacity truth, SOC and registered voltage turning points. Source workbooks are not redistributed. Rebuild the table from a clone of the upstream repository with:

```text
cd experiments/pulsebat_procurement_external
python scripts/prepare_data.py PATH_TO_CLONED_PULSEBAT_REPOSITORY
```

The experiment preserves its own 28-entry manifest, frozen protocol, 999-permutation and 2000-bootstrap outputs, and an independent LP reimplementation audit.

`experiments/pulsebat_procurement_correction_v02/` is a non-destructive
interpretation overlay built only from the same included 151-battery processed
table. It adds the complete 40-point SOC×menu audit, pairwise-versus-hull and
leave-one-out diagnostics, and paired whole-battery uncertainty. It does not
introduce another upstream dataset or alter the frozen PulseBat files.

## NASA PCoE Randomized Battery Usage data

- Record: <https://doi.org/10.5281/zenodo.15277374>
- License: CC BY 4.0
- Citation: Bole, Kulkarni and Daigle, “Adaptation of an Electrochemistry-based Li-Ion Battery Model to Account for Deterioration Observed Under Randomized Use,” PHM Society (2014).
- Seven registered subsets, 28 cells, approximately 5 GB extracted raw data.

The source archives are not redistributed. `experiments/nasa_randomized_usage_gate/data/steps.parquet` contains 389,307 derived randomized-discharge steps and permits offline reproduction from model construction onward. Full extraction and propensity checks are documented in:

```text
experiments/nasa_randomized_usage_gate/docs/DATA_PROVENANCE.md
experiments/nasa_randomized_usage_gate/scripts/00_download_and_extract.sh
```

## NASA/UCF Accelerated Life Testing data

- Archive: <https://data.nasa.gov/docs/legacy/battery_alt_dataset.zip>
- Study: Fricke, Nascimento and Viana, “An Accelerated Life Testing Dataset for Lithium-Ion Batteries with Constant and Variable Loading Conditions,” v0.0.1 (2023).
- License: MIT, as stated by the experiment package.
- Raw archive approximately 540 MB; extracted data approximately 3.4 GB.

The raw archive is not redistributed. The compact experiment includes 9,133 extracted missions from 26 packs, the registered 16-pack reference-channel table, model tables, null results and all frozen gate outputs. Rebuild commands are in `experiments/battery_alt_reference_channel_gate/scripts/00_download_and_extract.sh` and its README.
