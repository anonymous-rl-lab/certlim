#!/usr/bin/env python3
"""Extract the frozen, lightweight feature table from official raw files."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from severson_gate.raw import extract_batch


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FILES = {
    1: RAW / "MATR_batch_20170512.mat",
    2: RAW / "MATR_batch_20170630.mat",
    3: RAW / "MATR_batch_20180412.mat",
}


def main() -> None:
    start = time.perf_counter()
    records, audits = [], []
    for batch_number, path in FILES.items():
        batch_records, batch_audits = extract_batch(path, batch_number)
        records.extend(batch_records)
        audits.extend(batch_audits)
    frame = pd.DataFrame(records).sort_values(["batch", "cell_id"]).reset_index(drop=True)
    audit = pd.DataFrame(audits).sort_values(["cell_id"]).reset_index(drop=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    frame.to_csv(PROCESSED / "registered_features.csv", index=False)
    audit.to_csv(PROCESSED / "chronology_audit.csv", index=False)
    summary = {
        "runtime_seconds": time.perf_counter() - start,
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "split_counts": frame["split"].value_counts().sort_index().to_dict(),
        "batch_counts": frame["batch"].value_counts().sort_index().to_dict(),
        "duplicate_ids": sorted(frame.loc[frame["cell_id"].duplicated(), "cell_id"].tolist()),
        "cycle_life_min": float(frame["cycle_life"].min()),
        "cycle_life_max": float(frame["cycle_life"].max()),
    }
    (PROCESSED / "extraction_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
