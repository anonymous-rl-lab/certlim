# Third-party notices

## Jones EIS

The Jones external experiment uses data described in:

> Jones et al., “Impedance-based forecasting of lithium-ion battery performance amid uneven usage,” *Nature Communications* (2022).

- Paper: <https://www.nature.com/articles/s41467-022-32422-w>
- Data: <https://doi.org/10.5281/zenodo.6645536>, CC BY 4.0
- Author code: <https://github.com/PenelopeJones/battery-forecasting>, MIT License

## Severson/MATR

The second external experiment uses data described in:

> Severson et al., “Data-driven prediction of battery cycle life before capacity degradation,” *Nature Energy* (2019).

- Paper: <https://www.nature.com/articles/s41560-019-0356-8>
- Data: <https://data.matr.io/1/>
- Author loading code: <https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation>
- BatteryML cross-check: <https://github.com/microsoft/BatteryML>, MIT License

## Zhu voltage relaxation

The third external experiment uses data described in:

> Zhu et al., “Data-driven capacity estimation of commercial lithium-ion batteries from voltage relaxation,” *Nature Communications* (2022).

- Data: <https://doi.org/10.5281/zenodo.6405084>, CC BY 4.0
- Experiment-specific attribution and archive hashes: `experiments/zhu_relaxation_external/THIRD_PARTY_NOTICES.md` and `data/RAW_MANIFEST.sha256`

## PulseBat

The fourth external experiment uses the PulseBat retired-battery pulse-response dataset:

- Dataset/code: <https://github.com/terencetaothucb/Pulse-Voltage-Response-Generation>, MIT License
- Repository revision: `92aeb9b8a26bc337164401411271fa8eeadf605c`
- Raw-data archive: <https://doi.org/10.5281/zenodo.13360631>
- Associated article: <https://www.nature.com/articles/s41467-024-54454-0>
- Experiment-specific workbook hashes: `experiments/pulsebat_procurement_external/docs/DATA_PROVENANCE.md`

## NASA Randomized Battery Usage

The fifth external experiment uses the NASA PCoE Randomized Battery Usage data:

- Record: <https://doi.org/10.5281/zenodo.15277374>, CC BY 4.0
- NASA catalog: <https://data.nasa.gov/dataset/randomized-battery-usage-1-random-walk>
- Experiment-specific provenance: `experiments/nasa_randomized_usage_gate/docs/DATA_PROVENANCE.md`

## NASA/UCF Accelerated Life Testing

The sixth external experiment uses the NASA/UCF accelerated-life battery dataset described by Fricke, Nascimento and Viana (2023):

- Archive: <https://data.nasa.gov/docs/legacy/battery_alt_dataset.zip>
- Dataset/code terms: MIT License
- Experiment-specific source description: `experiments/battery_alt_reference_channel_gate/README.md` and `docs/FROZEN_PROTOCOL.md`
- Imported notice discrepancy: `docs/certification_limits_evidence_bundle_v01/IMPORT_PROVENANCE.md`

The Jones source archives, MATR raw MATLAB files, Zhu raw CSV archives, PulseBat source workbooks, NASA raw archives and upstream repositories are not redistributed in `repo_v6.zip`. This bundle contains clean-room experiment implementations, frozen configurations, lightweight derived outputs and results necessary to review the reported gates. Upstream data terms remain applicable.
