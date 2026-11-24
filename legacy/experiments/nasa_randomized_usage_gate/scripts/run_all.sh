#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src
python3 scripts/02_build_models.py
MAX_N="${MAX_N:-20}" python3 scripts/03_run_L1_L2.py
python3 scripts/04_run_L3_naive.py
python3 scripts/05_run_L3_adversarial.py
python3 scripts/06_null_and_sensitivity.py
python3 scripts/07_make_report.py
python3 scripts/08_make_claim_status.py
python3 -m unittest discover -s tests
python3 scripts/build_manifest.py
python3 scripts/verify_manifest.py
