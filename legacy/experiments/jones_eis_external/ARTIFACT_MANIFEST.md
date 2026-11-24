# Artifact manifest

The reproducibility bundle intentionally excludes the two licensed source archives, their extracted raw files, and the large parsed cycle tables. Obtain the archives from <https://doi.org/10.5281/zenodo.6645536> and verify the MD5 values in `config/smoke.json` and `config/smoke25.json`.

Included:

- audit-corrected gate report, legacy frozen protocols, and audit-locked rerun protocols;
- parser, smoke, legacy model, corrected model, and nested-geometry scripts;
- fixed JSON configurations;
- audit summaries and explicit error tables;
- legacy and audit-corrected cross-temperature metrics and predictions;
- paired effects, decision counts, software environments, configuration snapshots, and input hashes;
- audit-corrected within-domain and nested-geometry results;
- parser smoke test.

The legacy `small_cubic` independent-quantizer delta table is retained only for provenance and withdrawn for cross-menu interpretation. In the audit rerun, nested dominance is labeled as a structural invariant; the real-versus-permuted contrast is the empirical diagnostic.

The primary execution order is:

1. `scripts/run_smoke.py` for each domain;
2. `scripts/run_small.py` for the 35 °C within-domain development gate;
3. `scripts/run_cross_temperature_audit.py` for the corrected 25→35 °C diagnostic gate;
4. `scripts/run_small.py` with `config/small_audit_rerun.json`;
5. `scripts/run_nested_geometry.py` with `config/nested_geometry_audit_rerun.json`.
