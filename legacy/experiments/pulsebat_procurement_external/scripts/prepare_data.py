#!/usr/bin/env python3
"""Extract the registered compact table from the upstream PulseBat clone."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "LMO10": Path("ProcessedData_adjustable/10Ah LMO/LMO_10Ah_W_5000.xlsx"),
    "LFP35": Path("ProcessedData_adjustable/35Ah LFP/LFP_35Ah_W_5000.xlsx"),
}
COLUMNS = ["ID", "Qn", "Q", "SOH", "SOC", "U1", "U3", "U7", "U11", "U15", "U19", "U21"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream_repository", type=Path)
    args = parser.parse_args()
    frames = []
    for chemistry, relative in SOURCES.items():
        frame = pd.read_excel(args.upstream_repository / relative, sheet_name="SOC ALL", usecols=COLUMNS)
        frame.insert(0, "chemistry", chemistry)
        frames.append(frame)
    out = pd.concat(frames, ignore_index=True)
    target = ROOT / "data" / "processed" / "observations.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(target, index=False, float_format="%.10g")
    print(f"wrote {len(out)} rows from {out.ID.nunique()} batteries to {target}")


if __name__ == "__main__":
    main()

