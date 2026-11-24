#!/usr/bin/env python3
"""Ten-minute parser, chronology, and split-integrity smoke gate."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from severson_gate.raw import extract_batch


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RESULTS = ROOT / "results" / "smoke"
FILES = {
    1: RAW / "MATR_batch_20170512.mat",
    2: RAW / "MATR_batch_20170630.mat",
    3: RAW / "MATR_batch_20180412.mat",
}


def main() -> None:
    start = time.perf_counter()
    records, audits = [], []
    for batch_number, path in FILES.items():
        batch_records, batch_audits = extract_batch(path, batch_number, smoke_limit=2)
        records.extend(batch_records)
        audits.extend(batch_audits)
    frame = pd.DataFrame(records)
    audit = pd.DataFrame(audits)
    feature_columns = [
        column for column in frame.columns
        if column.startswith(("protocol_", "s5_", "s100_", "curve5_", "curve100_"))
    ]
    chronology_ok = bool(
        (audit[["q4_points", "q5_points", "q10_points", "q100_points"]] == 1000).all().all()
        and (audit["cycle_min"] <= 1).all()
        and (audit["cycle_max"] >= 100).all()
    )
    summary = {
        "status": "PASS" if chronology_ok and len(frame) >= 6 else "FAIL",
        "runtime_seconds": time.perf_counter() - start,
        "cells_parsed": int(len(frame)),
        "split_counts": frame["split"].value_counts().sort_index().to_dict(),
        "feature_count": len(feature_columns),
        "nonfinite_feature_values": int((~pd.notna(frame[feature_columns])).sum().sum()),
        "chronology_ok": chronology_ok,
        "physical_cycle_to_raw_index": {"4": 3, "5": 4, "10": 9, "100": 99},
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RESULTS / "sample_features.csv", index=False)
    audit.to_csv(RESULTS / "chronology_audit.csv", index=False)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
