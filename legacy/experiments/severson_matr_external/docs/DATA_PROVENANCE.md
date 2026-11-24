# Data and code provenance

## Primary dataset

Severson, K. A., Attia, P. M., Jin, N. et al. “Data-driven prediction of battery cycle life before capacity degradation.” *Nature Energy* 4, 383–391 (2019). DOI: 10.1038/s41560-019-0356-8.

- Official landing page: <https://data.matr.io/1/>
- Official project: <https://data.matr.io/1/projects/5c48dd2bc625d700019f3204>
- Raw files are downloaded by immutable file identifiers in `scripts/download_data.sh`.
- Raw files are not redistributed in the compact experiment archive. Upstream terms and attribution remain applicable.

## Author code

- Repository: <https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life-before-capacity-degradation>
- Audited commit: `1ef13d27c66dc3d73affdaa008fbeba5687b2ea4`
- Used to verify the continuation-cell merges, removed channels, raw field layout, and author train/test indices. No author modeling code was copied.

## Independent implementation cross-check

- BatteryML repository: <https://github.com/microsoft/BatteryML>
- Audited commit: `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd`
- Used to cross-check official download file identifiers and explicit split lists. BatteryML is MIT licensed.

## Leakage controls

- One row per physical cell.
- Continuation cells are represented only by their batch-1 identity and corrected cycle life.
- All fit, imputation, scaling, ridge selection, and conformal calibration occur before the locked batch-3 evaluation.
- `Q5-Q4` and `Q100-Q10` use only registered early cycles. No target-derived or post-horizon feature is included.
