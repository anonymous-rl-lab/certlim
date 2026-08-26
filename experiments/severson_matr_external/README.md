# Severson/MATR external certification gate

This package runs the second external gate for the finite-evidence causal-safety-certification program. It compares charging-policy descriptors, scalar telemetry through cycles 5 and 100, and early discharge-voltage-curve changes on the official three-batch Severson/MATR LFP/graphite dataset.

The protocol was frozen before model fitting. The author-designated training set is used for model fitting, the primary test set for split-conformal calibration, and batch 3 is locked as the sole external test domain.

## Result

The registered overall gate failed. Structured curve evidence improved external point prediction, but 5-cycle evidence did not beat its permutation negative control by the registered margin and source-calibrated uncertainty did not transport to batch 3. See `SEVERSON_EXTERNAL_GATE_REPORT.md`.

## Reproduce

Create the environment and download the three official raw files using `scripts/download_data.sh`, then run:

```bash
PYTHONPATH=src python scripts/run_smoke.py
PYTHONPATH=src python scripts/extract_features.py
PYTHONPATH=src python scripts/run_analysis.py
MPLCONFIGDIR=.mplconfig PYTHONPATH=src python scripts/make_report.py
python -m pytest -q
```

The distributable archive includes the processed feature table and all locked results, but not the 8.2 GB upstream raw files.
