#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    brier_score_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline


PROJECT = Path(__file__).resolve().parents[1]


def add_history(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values(["cell", "cycle"]).copy()
    groups = frame.groupby("cell", sort=False)
    for lag in range(1, 6):
        frame[f"capacity_soh_lag{lag}"] = groups["soh"].shift(lag)
    for column in ("charge_stage1_ma", "charge_stage2_ma", "discharge_current_ma"):
        for lag in range(1, 4):
            frame[f"{column}_lag{lag}"] = groups[column].shift(lag)
    frame["under_delivery"] = (frame["soh"] < 0.50).astype(int)
    return frame


def feature_menus(frame: pd.DataFrame) -> dict[str, list[str]]:
    actions = ["charge_stage1_ma", "charge_stage2_ma", "discharge_current_ma"]
    history = [
        "cycle",
        "previous_soh",
        "cumulative_throughput_mah",
        "ocv_v",
    ] + actions
    history += [f"capacity_soh_lag{lag}" for lag in range(1, 6)]
    history += [
        f"{column}_lag{lag}"
        for column in actions
        for lag in range(1, 4)
    ]
    eis = sorted(
        column for column in frame if column.startswith("eis_re_") or column.startswith("eis_neg_im_")
    )
    return {
        "actions": actions,
        "eis_actions": actions + eis,
        "old_history": history,
        "old_history_eis": history + eis,
        "old_history_eis_permuted": history + eis,
    }


def permute_eis(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    result = frame.copy()
    columns = sorted(
        column for column in frame if column.startswith("eis_re_") or column.startswith("eis_neg_im_")
    )
    rng = np.random.default_rng(seed)
    for _, indices in frame.groupby("cell").groups.items():
        indices = np.asarray(list(indices))
        donors = rng.permutation(indices)
        result.loc[indices, columns] = frame.loc[donors, columns].to_numpy()
    return result


def calibrated_thresholds(y: np.ndarray, probability: np.ndarray, alpha: float, beta: float) -> tuple[float, float]:
    unsafe = np.sort(probability[y == 1])
    safe = np.sort(probability[y == 0])
    if len(unsafe) == 0 or len(safe) == 0:
        raise RuntimeError("calibration domain lacks one endpoint class")
    allowed_low = int(np.floor(alpha * len(unsafe)))
    low = (
        float(np.nextafter(unsafe[0], -np.inf))
        if allowed_low == 0
        else float((unsafe[allowed_low - 1] + unsafe[allowed_low]) / 2)
    )
    allowed_high = int(np.floor(beta * len(safe)))
    high = (
        float(np.nextafter(safe[-1], np.inf))
        if allowed_high == 0
        else float((safe[-allowed_high - 1] + safe[-allowed_high]) / 2)
    )
    if low >= high:
        midpoint = (low + high) / 2
        low = float(np.nextafter(midpoint, -np.inf))
        high = float(np.nextafter(midpoint, np.inf))
    return low, high


def decision_metrics(y: np.ndarray, probability: np.ndarray, low: float, high: float) -> dict[str, float]:
    certify = probability <= low
    reject = probability >= high
    decisive = certify | reject
    unsafe = y == 1
    safe = y == 0
    return {
        "auc": float(roc_auc_score(y, probability)),
        "brier": float(brier_score_loss(y, probability)),
        "coverage": float(decisive.mean()),
        "balanced_decisiveness": float(min(decisive[unsafe].mean(), decisive[safe].mean())),
        "unsafe_certify_error": float(certify[unsafe].mean()),
        "safe_reject_error": float(reject[safe].mean()),
        "threshold_certify": low,
        "threshold_reject": high,
    }


def partitions(cells: list[str], repetitions: int, seed: int) -> list[tuple[list[str], list[str]]]:
    rng = np.random.default_rng(seed)
    return [
        (list(order[:24]), list(order[24:32]))
        for order in (rng.permutation(cells) for _ in range(repetitions))
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-cycles", type=Path, default=PROJECT / "results" / "smoke25" / "cycles.csv")
    parser.add_argument("--test-cycles", type=Path, default=PROJECT / "results" / "smoke35_cubic" / "cycles.csv")
    parser.add_argument("--config", type=Path, default=PROJECT / "config" / "cross_temperature.json")
    parser.add_argument("--output", type=Path, default=PROJECT / "results" / "cross_temperature")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if config["status"] != "FROZEN_BEFORE_25C_DOWNLOAD_AND_MODEL_FIT":
        raise RuntimeError("cross-temperature protocol is not frozen")
    args.output.mkdir(parents=True, exist_ok=True)

    train = add_history(pd.read_csv(args.train_cycles))
    test = add_history(pd.read_csv(args.test_cycles))
    menus = feature_menus(train)
    train_frames = {name: train for name in menus}
    test_frames = {name: test for name in menus}
    permutation_seed = config["split"]["seed"] + 991
    train_frames["old_history_eis_permuted"] = permute_eis(train, permutation_seed)
    test_frames["old_history_eis_permuted"] = permute_eis(test, permutation_seed + 1)

    training_cells = sorted(train["cell"].unique())
    external_cells = sorted(test["cell"].unique())
    expected = config["split"]
    if len(training_cells) != expected["training_cells"] + expected["calibration_cells"]:
        raise RuntimeError(f"expected 32 training-domain cells, found {len(training_cells)}")
    if len(external_cells) != expected["external_test_cells"]:
        raise RuntimeError(f"expected 16 external cells, found {len(external_cells)}")

    result_rows: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []
    splits = partitions(training_cells, expected["calibration_repetitions"], expected["seed"])
    for split_index, (fit_cells, calibration_cells) in enumerate(splits):
        for menu_index, (menu, columns) in enumerate(menus.items()):
            train_frame = train_frames[menu]
            test_frame = test_frames[menu]
            fit = train_frame[train_frame["cell"].isin(fit_cells)]
            calibration = train_frame[train_frame["cell"].isin(calibration_cells)]
            seed = expected["seed"] + 100 * split_index + menu_index

            regressor_config = config["regressor"]
            regressor = make_pipeline(
                SimpleImputer(strategy="median"),
                ExtraTreesRegressor(
                    n_estimators=regressor_config["n_estimators"],
                    max_features=regressor_config["max_features"],
                    min_samples_leaf=regressor_config["min_samples_leaf"],
                    n_jobs=-1,
                    random_state=seed,
                ),
            )
            regressor.fit(fit[columns], fit["soh"])
            capacity_prediction = regressor.predict(test_frame[columns])

            classifier_config = config["classifier"]
            classifier = make_pipeline(
                SimpleImputer(strategy="median"),
                RandomForestClassifier(
                    n_estimators=classifier_config["n_estimators"],
                    max_depth=classifier_config["max_depth"],
                    min_samples_leaf=classifier_config["min_samples_leaf"],
                    class_weight=classifier_config["class_weight"],
                    max_features="sqrt",
                    n_jobs=-1,
                    random_state=seed + 50_000,
                ),
            )
            classifier.fit(fit[columns], fit["under_delivery"])
            calibration_probability = classifier.predict_proba(calibration[columns])[:, 1]
            external_probability = classifier.predict_proba(test_frame[columns])[:, 1]
            low, high = calibrated_thresholds(
                calibration["under_delivery"].to_numpy(),
                calibration_probability,
                config["three_decision"]["alpha"],
                config["three_decision"]["beta"],
            )

            metrics = {
                "split": split_index,
                "menu": menu,
                "fit_cells": ",".join(fit_cells),
                "calibration_cells": ",".join(calibration_cells),
                "external_cells": ",".join(external_cells),
                "rmse": float(mean_squared_error(test_frame["soh"], capacity_prediction) ** 0.5),
                "mae": float(mean_absolute_error(test_frame["soh"], capacity_prediction)),
                "r2": float(r2_score(test_frame["soh"], capacity_prediction)),
            }
            metrics.update(
                decision_metrics(
                    test_frame["under_delivery"].to_numpy(), external_probability, low, high
                )
            )
            result_rows.append(metrics)

            prediction = test_frame.loc[:, ["cell", "cycle", "soh", "under_delivery"]].copy()
            prediction["capacity_prediction"] = capacity_prediction
            prediction["event_probability"] = external_probability
            prediction["decision"] = np.where(
                external_probability <= low,
                "Certify",
                np.where(external_probability >= high, "Reject", "Alert"),
            )
            prediction["split"] = split_index
            prediction["menu"] = menu
            prediction_rows.append(prediction)

    metrics = pd.DataFrame(result_rows)
    predictions = pd.concat(prediction_rows, ignore_index=True)
    metrics.to_csv(args.output / "split_metrics.csv", index=False)
    predictions.to_csv(args.output / "predictions.csv", index=False)
    numeric = [
        "rmse",
        "mae",
        "r2",
        "auc",
        "brier",
        "coverage",
        "balanced_decisiveness",
        "unsafe_certify_error",
        "safe_reject_error",
    ]
    medians = metrics.groupby("menu")[numeric].median().reset_index()
    medians.to_csv(args.output / "median_metrics.csv", index=False)
    lookup = medians.set_index("menu")
    actions = lookup.loc["actions"]
    eis_actions = lookup.loc["eis_actions"]
    old = lookup.loc["old_history"]
    new = lookup.loc["old_history_eis"]
    permuted = lookup.loc["old_history_eis_permuted"]
    gates = config["development_success_gates"]
    checks = {
        "eis_actions_rmse_reduction_vs_actions": bool(
            (actions.rmse - eis_actions.rmse) / actions.rmse
            >= gates["eis_actions_rmse_reduction_vs_actions_fraction"]
        ),
        "old_history_eis_rmse_reduction": bool(
            (old.rmse - new.rmse) / old.rmse
            >= gates["old_history_eis_rmse_reduction_vs_old_history_fraction"]
        ),
        "old_history_eis_auc_gain": bool(
            new.auc - old.auc >= gates["old_history_eis_auc_gain_vs_old_history"]
        ),
        "real_eis_beats_permuted_auc": bool(
            new.auc - permuted.auc >= gates["old_history_eis_auc_gain_vs_permuted"]
        ),
        "balanced_decisiveness_gain": bool(
            new.balanced_decisiveness - old.balanced_decisiveness
            >= gates["balanced_decisiveness_gain_vs_old_history"]
        ),
        "external_side_errors": bool(
            new.unsafe_certify_error <= gates["maximum_external_side_error"]
            and new.safe_reject_error <= gates["maximum_external_side_error"]
        ),
    }
    summary = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "interpretation": "cross-temperature development gate; 35C was never used for fitting or calibration",
        "training_rows": len(train),
        "training_cells": len(training_cells),
        "external_rows": len(test),
        "external_cells": len(external_cells),
        "training_endpoint_prevalence": float(train["under_delivery"].mean()),
        "external_endpoint_prevalence": float(test["under_delivery"].mean()),
        "median_metrics": medians.set_index("menu").to_dict(orient="index"),
        "checks": checks,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    display = medians.copy()
    for column in display.columns[1:]:
        display[column] = display[column].map(lambda value: f"{value:.3f}")
    lines = [
        "# Jones EIS cross-temperature report",
        "",
        f"**Registered external gate: {summary['status']}**",
        "",
        "> Training/calibration uses only 25 °C cells. Every reported prediction below is on the locked 35 °C cohort.",
        "",
        "| " + " | ".join(display.columns) + " |",
        "|" + "|".join(["---"] + ["---:"] * (len(display.columns) - 1)) + "|",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in display.to_numpy())
    lines.extend(["", "## Registered checks", "", "| Check | Result |", "|---|---:|"])
    lines.extend(f"| {key} | {'PASS' if value else 'FAIL'} |" for key, value in checks.items())
    lines.extend(
        [
            "",
            "## Scope",
            "",
            "The severe-under-delivery label is an operational capacity endpoint. It is not a thermal-runaway or field-safety label, and this experiment does not identify arbitrary counterfactual policies.",
        ]
    )
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
