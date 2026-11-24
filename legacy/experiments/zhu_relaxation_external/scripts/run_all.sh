#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH=src

# The release manifest is immutable during a reproduction run.
python3 scripts/verify_manifest.py
python3 scripts/02_run_gates.py
python3 scripts/03_make_report.py
python3 scripts/04_make_claim_status.py
python3 -m unittest discover -s tests -v
python3 scripts/verify_manifest.py
