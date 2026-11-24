#!/usr/bin/env python3
"""Run the frozen external experiment and evaluate all registered gates."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd

from severson_gate.evaluate import evaluate_all, evaluate_gates


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "full"


def main() -> None:
    start = time.perf_counter()
    config = json.loads((ROOT / "config" / "registered.json").read_text(encoding="utf-8"))
    data = pd.read_csv(ROOT / "data" / "processed" / "registered_features.csv")
    audit = pd.read_csv(ROOT / "data" / "processed" / "chronology_audit.csv")
    reject_max = config["target"]["reject_max_cycles"]
    certify_min = config["target"]["certify_min_cycles"]
    external = data[data["split"] == "external"]
    integrity = {
        "split_counts": data["split"].value_counts().sort_index().to_dict(),
        "duplicate_ids": sorted(data.loc[data["cell_id"].duplicated(), "cell_id"].tolist()),
        "external_unsafe_n": int((external["cycle_life"] <= reject_max).sum()),
        "external_safe_n": int((external["cycle_life"] >= certify_min).sum()),
        "chronology_ok": bool(
            (audit[["q4_points", "q5_points", "q10_points", "q100_points"]] == 1000).all().all()
            and (audit["cycle_max"] >= 100).all()
        ),
    }
    metrics, predictions, permutations = evaluate_all(data, config)
    gates = evaluate_gates(metrics, permutations, config, integrity)
    summary = {
        "experiment": config["experiment"],
        "runtime_seconds": time.perf_counter() - start,
        "integrity": integrity,
        "gates": gates,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(RESULTS / "menu_metrics.csv", index=False)
    predictions.to_csv(RESULTS / "external_predictions.csv", index=False)
    permutations.to_csv(RESULTS / "negative_control_permutations.csv", index=False)
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
