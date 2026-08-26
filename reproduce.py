#!/usr/bin/env python3
"""Reproduce the paper's core results from the released artifacts.

    python3 reproduce.py                 # verify only: manifests + paper numbers (seconds)
    python3 reproduce.py --tier core     # recompute every result the paper reports
    python3 reproduce.py --tier full     # core, plus feature extraction from raw downloads
    python3 reproduce.py --list          # show the stages without running them

The default tier recomputes nothing. It checks that the released artifacts are
byte-for-byte what the manifests record, that the repository contract tests pass,
and that every headline number in the paper still reads out of the artifact it
came from. That is the check to run first: if it fails, recomputation cannot help.

The `core` tier re-runs the analysis scripts against the processed data shipped
with the repository. It overwrites files under each experiment's `results/`, so
run it on a clean checkout and use `git diff` (or the manifest verification the
run ends with) to see whether anything moved. Raw-data download and feature
extraction are the `full` tier only; they need tens of gigabytes and the upstream
archives.

The NASA frontier stage dominates the `core` wall clock. It honours MAX_N, so
`MAX_N=5 python3 reproduce.py --tier core` caps the block length and finishes in
minutes at the cost of a shortened Table I.

Stages are independent. A failing stage is reported and the run continues, so one
broken dependency does not hide the state of everything else.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "experiments"

# (tier, label, working directory, command)
STAGES: list[tuple[str, str, Path, list[str]]] = [
    # ---- recomputation from the processed data in this repository -------------
    ("core", "synthetic proof companion", EXP / "synthetic_gates",
     ["python3", "scripts/run_gates.py", "small"]),
    ("core", "NASA frontier (Table I, S3)", EXP / "nasa_randomized_usage_gate",
     ["python3", "scripts/03_run_L1_L2.py"]),
    ("core", "NASA natural confounding", EXP / "nasa_randomized_usage_gate",
     ["python3", "scripts/04_run_L3_naive.py"]),
    ("core", "NASA adversarial collision (27)", EXP / "nasa_randomized_usage_gate",
     ["python3", "scripts/05_run_L3_adversarial.py"]),
    ("core", "NASA permutation calibration", EXP / "nasa_randomized_usage_gate",
     ["python3", "scripts/06_null_and_sensitivity.py"]),
    ("core", "Battery ALT gates (28, S4)", EXP / "battery_alt_reference_channel_gate",
     ["python3", "scripts/05_gates.py"]),
    ("core", "Battery ALT null and sweep", EXP / "battery_alt_reference_channel_gate",
     ["python3", "scripts/06_null_and_sensitivity.py"]),
    ("core", "PulseBat registered frontier", EXP / "pulsebat_procurement_external",
     ["python3", "scripts/run_all.py"]),
    ("core", "PulseBat 40-point grid (S5, S6)", EXP / "pulsebat_procurement_correction_v02",
     ["python3", "scripts/audit_pulsebat.py"]),
    ("core", "Zhu geometry audit", EXP / "zhu_relaxation_external",
     ["python3", "scripts/02_run_gates.py"]),
    ("core", "MATR transport audit", EXP / "severson_matr_external",
     ["python3", "scripts/run_analysis.py"]),
    ("core", "Jones transport audit (verify released)", EXP / "jones_eis_external",
     ["python3", "scripts/verify_audit_results.py"]),
    ("core", "adversarial channel laws", EXP / "nasa_confidence_and_baselines",
     ["python3", "scripts/05_dump_adversarial.py"]),
    ("core", "E1/E2 certificate and census (S9.1, S9.2)", EXP / "nasa_confidence_and_baselines",
     ["python3", "scripts/run_e1_e2.py"]),
    ("core", "E3 baseline comparison (S11)", EXP / "nasa_confidence_and_baselines",
     ["python3", "scripts/run_e3.py"]),
    ("core", "certificate sensitivity (S9.5)", EXP / "nasa_confidence_and_baselines",
     ["python3", "scripts/run_sensitivity.py"]),
    # ---- raw data: downloads and feature extraction ---------------------------
    ("full", "download NASA randomized usage", EXP / "nasa_randomized_usage_gate",
     ["bash", "scripts/00_download_and_extract.sh"]),
    ("full", "extract NASA steps and models", EXP / "nasa_randomized_usage_gate",
     ["python3", "scripts/01_extract_steps.py"]),
    ("full", "download Battery ALT", EXP / "battery_alt_reference_channel_gate",
     ["bash", "scripts/00_download_and_extract.sh"]),
    ("full", "extract ALT missions and models", EXP / "battery_alt_reference_channel_gate",
     ["python3", "scripts/01_extract_missions.py"]),
    ("full", "download Zhu relaxation", EXP / "zhu_relaxation_external",
     ["bash", "scripts/download_data.sh"]),
    ("full", "extract Zhu features", EXP / "zhu_relaxation_external",
     ["python3", "scripts/01_extract_features.py"]),
    ("full", "download Severson/MATR", EXP / "severson_matr_external",
     ["bash", "scripts/download_data.sh"]),
    ("full", "extract MATR features", EXP / "severson_matr_external",
     ["python3", "scripts/extract_features.py"]),
    ("full", "download Jones EIS", EXP / "jones_eis_external",
     ["bash", "-c", "test -f data/raw/chemistry2-25C-cycles.csv || "
                    "echo 'see experiments/jones_eis_external/README.md for the retrieval steps'"]),
    ("full", "Jones cross-temperature audit", EXP / "jones_eis_external",
     ["python3", "scripts/run_cross_temperature_audit.py",
      "--train-cycles", "data/raw/chemistry2-25C-cycles.csv",
      "--test-cycles", "data/raw/chemistry2-35C-cycles.csv"]),
    # ---- verification: always runs, last ------------------------------------
    ("verify", "repository contract tests", ROOT,
     ["python3", "-m", "unittest", "discover", "-s", "tests", "-q"]),
    ("verify", "artifact manifests", ROOT, ["python3", "scripts/check_reproduction.py"]),
    ("verify", "paper headline numbers", ROOT, ["python3", "scripts/check_paper_numbers.py"]),
]

TIERS = {"verify": ["verify"], "core": ["core", "verify"], "full": ["core", "full", "verify"]}


def run(stage, echo: bool) -> tuple[bool, float]:
    tier, label, cwd, cmd = stage
    env = dict(os.environ, PYTHONPATH="src", MPLBACKEND="Agg")
    started = time.time()
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=not echo, text=True)
    elapsed = time.time() - started
    if proc.returncode and not echo:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-6:]
        for line in tail:
            print(f"        | {line}")
    return proc.returncode == 0, elapsed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier", choices=sorted(TIERS), default="verify")
    ap.add_argument("--list", action="store_true", help="print the stages and exit")
    ap.add_argument("--echo", action="store_true", help="stream each stage's own output")
    args = ap.parse_args()

    wanted = TIERS[args.tier]
    stages = [s for s in STAGES if s[0] in wanted]

    if args.list:
        for tier, label, cwd, cmd in STAGES:
            mark = "*" if tier in wanted else " "
            print(f" {mark} [{tier:6}] {label:44} {cwd.name}: {' '.join(cmd[1:])}")
        return 0

    print(f"tier: {args.tier}   stages: {len(stages)}\n")
    failed = []
    for stage in stages:
        tier, label, cwd, _ = stage
        print(f"  [{tier:6}] {label:44} ", end="", flush=True)
        ok, elapsed = run(stage, args.echo)
        print(f"{'ok' if ok else 'FAILED':>8}  {elapsed:6.1f}s")
        if not ok:
            failed.append(label)

    print()
    if failed:
        print(f"{len(failed)} of {len(stages)} stages failed:")
        for label in failed:
            print(f"  - {label}")
        return 1
    print(f"all {len(stages)} stages passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
