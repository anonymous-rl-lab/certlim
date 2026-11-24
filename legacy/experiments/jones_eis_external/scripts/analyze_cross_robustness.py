#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]


def bootstrap_mean_interval(values: np.ndarray, seed: int, draws: int = 20_000) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    samples = rng.choice(values, size=(draws, len(values)), replace=True).mean(axis=1)
    return {
        "mean": float(values.mean()),
        "ci95_low": float(np.quantile(samples, 0.025)),
        "ci95_high": float(np.quantile(samples, 0.975)),
        "positive_cells": int((values > 0).sum()),
        "n_cells": int(len(values)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--predictions",
        type=Path,
        default=PROJECT / "results" / "cross_temperature" / "predictions.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "results" / "cross_temperature" / "robustness.json",
    )
    args = parser.parse_args()
    predictions = pd.read_csv(args.predictions)
    predictions["squared_error"] = (
        predictions["capacity_prediction"] - predictions["soh"]
    ) ** 2
    per_cell = (
        predictions.groupby(["split", "menu", "cell"])["squared_error"]
        .mean()
        .pow(0.5)
        .rename("rmse")
        .reset_index()
    )
    pivot = per_cell.pivot(index=["split", "cell"], columns="menu", values="rmse")
    comparisons = {
        "eis_actions_vs_actions": pivot["actions"] - pivot["eis_actions"],
        "old_history_eis_vs_old_history": pivot["old_history"] - pivot["old_history_eis"],
        "real_eis_vs_permuted": pivot["old_history_eis_permuted"] - pivot["old_history_eis"],
    }
    summary: dict[str, object] = {}
    for offset, (name, differences) in enumerate(comparisons.items()):
        cell_mean = differences.groupby("cell").mean().to_numpy(float)
        split_mean = differences.groupby("split").mean()
        result = bootstrap_mean_interval(cell_mean, seed=20260825 + offset)
        result["positive_splits"] = int((split_mean > 0).sum())
        result["n_splits"] = int(len(split_mean))
        result["split_mean_differences"] = [float(value) for value in split_mean]
        summary[name] = result
    summary["forecast_robustness_gate"] = "PASS" if all(
        value["ci95_low"] > 0 for value in summary.values() if isinstance(value, dict)
    ) else "FAIL"
    args.output.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
