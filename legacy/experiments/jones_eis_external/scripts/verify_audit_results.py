#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, mean_squared_error, roc_auc_score


PROJECT = Path(__file__).resolve().parents[1]


def maximum_metric_difference(directory: Path, probability_column: str) -> float:
    predictions = pd.read_csv(directory / "predictions.csv")
    metrics = pd.read_csv(directory / "split_metrics.csv")
    rows: list[dict[str, object]] = []
    for (split_index, menu), group in predictions.groupby(["split", "menu"]):
        unsafe = group["under_delivery"].eq(1)
        safe = ~unsafe
        decisive = group["decision"].ne("Alert")
        row: dict[str, object] = {
            "split": split_index,
            "menu": menu,
            "auc": roc_auc_score(group["under_delivery"], group[probability_column]),
            "coverage": decisive.mean(),
            "balanced_decisiveness": min(decisive[unsafe].mean(), decisive[safe].mean()),
            "unsafe_certify_error": group.loc[unsafe, "decision"].eq("Certify").mean(),
            "safe_reject_error": group.loc[safe, "decision"].eq("Reject").mean(),
        }
        if "capacity_prediction" in group:
            row["rmse"] = mean_squared_error(group["soh"], group["capacity_prediction"]) ** 0.5
        else:
            row["brier"] = brier_score_loss(group["under_delivery"], group[probability_column])
        rows.append(row)
    recomputed = pd.DataFrame(rows).sort_values(["split", "menu"]).reset_index(drop=True)
    columns = [column for column in recomputed if column not in {"split", "menu"}]
    frozen = metrics[["split", "menu", *columns]].sort_values(["split", "menu"]).reset_index(drop=True)
    if not recomputed[["split", "menu"]].equals(frozen[["split", "menu"]]):
        raise RuntimeError(f"row identities differ in {directory}")
    return float(
        np.max(
            np.abs(
                recomputed[columns].to_numpy(float)
                - frozen[columns].to_numpy(float)
            )
        )
    )


def verify_nested(directory: Path, tolerance: float) -> None:
    frame = pd.read_csv(directory / "geometry.csv")
    pivot = frame.pivot(index=["seed", "block_length"], columns="menu", values="delta_hat")
    if not (pivot["old_history_eis_nested"] >= pivot["old_history"] - tolerance).all():
        raise RuntimeError("real nested refinement invariant failed")
    if not (
        pivot["old_history_eis_permuted_nested"] >= pivot["old_history"] - tolerance
    ).all():
        raise RuntimeError("permuted nested refinement invariant failed")
    monotone = (
        frame.sort_values("block_length")
        .groupby(["menu", "seed"])["delta_hat"]
        .apply(lambda values: np.all(np.diff(values.to_numpy()) >= -tolerance))
        .all()
    )
    if not monotone:
        raise RuntimeError("block monotonicity failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tolerance", type=float, default=1e-9)
    args = parser.parse_args()
    cross = PROJECT / "results" / "cross_temperature_audit_rerun"
    small = PROJECT / "results" / "small_cubic_audit_rerun"
    nested = PROJECT / "results" / "nested_geometry_audit_rerun"
    cross_difference = maximum_metric_difference(cross, "event_probability")
    small_difference = maximum_metric_difference(small, "probability")
    if cross_difference > args.tolerance or small_difference > args.tolerance:
        raise RuntimeError(
            f"metric mismatch: cross={cross_difference}, small={small_difference}"
        )
    verify_nested(nested, args.tolerance)
    cross_summary = json.loads((cross / "summary.json").read_text())
    small_summary = json.loads((small / "summary.json").read_text())
    nested_summary = json.loads((nested / "summary.json").read_text())
    if cross_summary["status"] != "FAIL" or not cross_summary["formal_run"]:
        raise RuntimeError("unexpected corrected cross-temperature status")
    if not all(cross_summary["integrity_checks"].values()):
        raise RuntimeError("cross-temperature integrity check failed")
    if small_summary["status"] != "FAIL":
        raise RuntimeError("unexpected corrected small-gate status")
    if nested_summary["status"] != "COMPLETE":
        raise RuntimeError("unexpected corrected nested-geometry status")
    print(
        "PASS audit-result semantics "
        f"(cross max diff={cross_difference:.3g}, small max diff={small_difference:.3g})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
