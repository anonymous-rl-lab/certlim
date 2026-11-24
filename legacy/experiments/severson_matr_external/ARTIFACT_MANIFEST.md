# Artifact manifest

## Frozen design

- `docs/FROZEN_PROTOCOL.md`: pre-fit scientific question, split, thresholds, evidence menus, metrics, gates, seeds, and budgets.
- `config/registered.json`: machine-readable registration.
- `docs/DATA_PROVENANCE.md`: primary data, author-code, and independent implementation provenance.
- `data/RAW_MANIFEST.sha256`: official URLs, exact byte counts, and SHA-256 digests for the omitted raw inputs.

## Code

- `src/severson_gate/raw.py`: MATLAB v7.3 extraction, cell exclusions/continuations, physical-cycle reconciliation, and frozen features.
- `src/severson_gate/evaluate.py`: ridge fitting, split-conformal intervals, three-decision rule, negative controls, and registered gates.
- `scripts/run_smoke.py`: parser/chronology smoke gate.
- `scripts/extract_features.py`: full 124-cell feature extraction.
- `scripts/run_analysis.py`: locked external evaluation.
- `scripts/make_report.py`: report, post-registration diagnostics, and audit figure.
- `tests/test_core.py`: deterministic unit tests.

## Derived data and results

- `data/processed/registered_features.csv`: 124-cell lightweight feature table.
- `data/processed/chronology_audit.csv`: per-cell cycle and Q(V) audit.
- `results/smoke/`: smoke-stage outputs.
- `results/full/menu_metrics.csv`: primary external metrics.
- `results/full/external_predictions.csv`: all locked external predictions, intervals, and decisions.
- `results/full/negative_control_permutations.csv`: all 400 registered permutation runs (200 per curve horizon).
- `results/full/summary.json`: gate results.
- `results/full/posthoc_diagnostics.json`: clearly labeled diagnostics that do not alter gates.
- `results/full/evidence_gate_audit.png` and `.pdf`: publication-style result figure.
- `SEVERSON_EXTERNAL_GATE_REPORT.md`: Chinese scientific audit and interpretation.

## Deliberately excluded

- Official raw MATLAB files (8.2 GB total).
- Local virtual environments, caches, bytecode, and downloaded papers.
