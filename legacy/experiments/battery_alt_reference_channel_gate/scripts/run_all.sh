#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
RAW="${RAW:-./data/raw/battery_alt_dataset}"
RW_STEPS="${RW_STEPS:-./data/rw_steps.parquet}"
[ -f data/missions.parquet ] || python3 scripts/01_extract_missions.py --raw "$RAW"
python3 scripts/02_build_models.py                      # v01, kept: produces the degenerate result
python3 scripts/03_g0_feasibility.py                    # G0 -> FAIL, recorded
python3 scripts/04_build_reference_experiment.py        # v02 grades + evidence, freeze
python3 scripts/05_gates.py                             # G1-G4, G6, G9
python3 scripts/06_null_and_sensitivity.py              # permutation null + 27-setting sweep
python3 scripts/07_rw_holdout.py --steps "$RW_STEPS"    # G7 on NASA RW
python3 scripts/08_make_report.py
python3 -m pytest tests -q
python3 scripts/build_manifest.py
python3 scripts/verify_manifest.py
