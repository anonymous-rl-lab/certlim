#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_history(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values(["cell", "cycle"]).copy()
    groups = frame.groupby("cell", sort=False)
    for lag in range(1, 6):
        frame[f"capacity_soh_lag{lag}"] = groups["soh"].shift(lag)
    actions = ("charge_stage1_ma", "charge_stage2_ma", "discharge_current_ma")
    for column in actions:
        for lag in range(1, 4):
            frame[f"{column}_lag{lag}"] = groups[column].shift(lag)
    frame["under_delivery"] = (frame["soh"] < 0.50).astype(int)
    return frame


def feature_menus(frame: pd.DataFrame) -> dict[str, list[str]]:
    actions = ["charge_stage1_ma", "charge_stage2_ma", "discharge_current_ma"]
    history = ["cycle", "previous_soh", "cumulative_throughput_mah", "ocv_v"] + actions
    history += [f"capacity_soh_lag{lag}" for lag in range(1, 6)]
    history += [f"{column}_lag{lag}" for column in actions for lag in range(1, 4)]
    eis = sorted(
        column
        for column in frame
        if column.startswith("eis_re_") or column.startswith("eis_neg_im_")
    )
    return {
        "actions": actions,
        "eis_actions": actions + eis,
        "eis_actions_permuted": actions + eis,
        "old_history": history,
        "old_history_eis": history + eis,
        "old_history_eis_permuted": history + eis,
    }


def permute_eis(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    result = frame.copy()
    columns = sorted(
        column
        for column in frame
        if column.startswith("eis_re_") or column.startswith("eis_neg_im_")
    )
    rng = np.random.default_rng(seed)
    for indices in frame.groupby("cell").groups.values():
        indices = np.asarray(list(indices))
        result.loc[indices, columns] = frame.loc[rng.permutation(indices), columns].to_numpy()
    return result


def one_sided_boundary(
    values: np.ndarray, allowed_fraction: float, lower_tail: bool
) -> float:
    ordered = np.sort(values)
    allowed = int(np.floor(allowed_fraction * len(ordered)))
    if lower_tail:
        if allowed == 0:
            return float(np.nextafter(ordered[0], -np.inf))
        if allowed >= len(ordered):
            return float(np.nextafter(ordered[-1], np.inf))
        return float((ordered[allowed - 1] + ordered[allowed]) / 2)
    if allowed == 0:
        return float(np.nextafter(ordered[-1], np.inf))
    if allowed >= len(ordered):
        return float(np.nextafter(ordered[0], -np.inf))
    boundary = len(ordered) - allowed
    return float((ordered[boundary - 1] + ordered[boundary]) / 2)


def calibrated_thresholds(
    y: np.ndarray, probability: np.ndarray, alpha: float, beta: float
) -> tuple[float, float, dict[str, object]]:
    unsafe = probability[y == 1]
    safe = probability[y == 0]
    if len(unsafe) == 0 or len(safe) == 0:
        raise RuntimeError("calibration domain lacks one endpoint class")
    raw_certify = one_sided_boundary(unsafe, alpha, lower_tail=True)
    raw_reject = one_sided_boundary(safe, beta, lower_tail=False)
    crossed = raw_certify >= raw_reject
    low = min(raw_certify, raw_reject)
    high = max(raw_certify, raw_reject)
    if low == high:
        low = float(np.nextafter(low, -np.inf))
        high = float(np.nextafter(high, np.inf))
    metadata = {
        "raw_certify_boundary": raw_certify,
        "raw_reject_boundary": raw_reject,
        "crossed_before_conservative_ordering": bool(crossed),
        "threshold_width": float(high - low),
    }
    return low, high, metadata


def decision_metrics(
    y: np.ndarray, probability: np.ndarray, low: float, high: float
) -> dict[str, float]:
    certify = probability <= low
    reject = probability >= high
    decisive = certify | reject
    unsafe = y == 1
    safe = y == 0
    return {
        "auc": float(roc_auc_score(y, probability)),
        "brier": float(brier_score_loss(y, probability)),
        "coverage": float(decisive.mean()),
        "alert_rate": float((~decisive).mean()),
        "unsafe_coverage": float(decisive[unsafe].mean()),
        "safe_coverage": float(decisive[safe].mean()),
        "balanced_decisiveness": float(
            min(decisive[unsafe].mean(), decisive[safe].mean())
        ),
        "unsafe_certify_error": float(certify[unsafe].mean()),
        "safe_reject_error": float(reject[safe].mean()),
        "threshold_certify": float(low),
        "threshold_reject": float(high),
    }


def partitions(
    cells: list[str], repetitions: int, seed: int
) -> list[tuple[list[str], list[str]]]:
    rng = np.random.default_rng(seed)
    return [
        (list(order[:24]), list(order[24:32]))
        for order in (rng.permutation(cells) for _ in range(repetitions))
    ]


def paired_effects(metrics: pd.DataFrame) -> pd.DataFrame:
    comparisons = {
        "eis_actions_vs_actions": ("eis_actions", "actions"),
        "eis_actions_vs_permuted": ("eis_actions", "eis_actions_permuted"),
        "old_history_eis_vs_old_history": ("old_history_eis", "old_history"),
        "old_history_eis_vs_permuted": (
            "old_history_eis",
            "old_history_eis_permuted",
        ),
    }
    lookup = metrics.set_index(["split", "menu"])
    rows: list[dict[str, object]] = []
    for split in sorted(metrics["split"].unique()):
        for name, (target_name, baseline_name) in comparisons.items():
            target = lookup.loc[(split, target_name)]
            baseline = lookup.loc[(split, baseline_name)]
            rows.append(
                {
                    "split": int(split),
                    "comparison": name,
                    "target_menu": target_name,
                    "baseline_menu": baseline_name,
                    "target_rmse": float(target.rmse),
                    "baseline_rmse": float(baseline.rmse),
                    "rmse_gain_absolute": float(baseline.rmse - target.rmse),
                    "rmse_gain_fraction": float((baseline.rmse - target.rmse) / baseline.rmse),
                    "auc_gain": float(target.auc - baseline.auc),
                    "balanced_decisiveness_gain": float(
                        target.balanced_decisiveness - baseline.balanced_decisiveness
                    ),
                    "unsafe_certify_error_change": float(
                        target.unsafe_certify_error - baseline.unsafe_certify_error
                    ),
                    "safe_reject_error_change": float(
                        target.safe_reject_error - baseline.safe_reject_error
                    ),
                }
            )
    return pd.DataFrame(rows)


def paired_summary(effects: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        "rmse_gain_absolute",
        "rmse_gain_fraction",
        "auc_gain",
        "balanced_decisiveness_gain",
        "unsafe_certify_error_change",
        "safe_reject_error_change",
    ]
    return effects.groupby("comparison")[numeric].median().reset_index()


def bootstrap_cell_comparisons(
    predictions: pd.DataFrame, seed: int, draws: int
) -> dict[str, object]:
    table = predictions.copy()
    table["squared_error"] = (table["capacity_prediction"] - table["soh"]) ** 2
    per_cell = (
        table.groupby(["split", "menu", "cell"])["squared_error"]
        .mean()
        .pow(0.5)
        .rename("rmse")
        .reset_index()
    )
    pivot = per_cell.pivot(index=["split", "cell"], columns="menu", values="rmse")
    comparisons = {
        "eis_actions_vs_actions": pivot["actions"] - pivot["eis_actions"],
        "eis_actions_vs_permuted": pivot["eis_actions_permuted"] - pivot["eis_actions"],
        "old_history_eis_vs_old_history": pivot["old_history"] - pivot["old_history_eis"],
        "old_history_eis_vs_permuted": (
            pivot["old_history_eis_permuted"] - pivot["old_history_eis"]
        ),
    }
    rng = np.random.default_rng(seed)
    output: dict[str, object] = {}
    for name, differences in comparisons.items():
        cell_values = differences.groupby("cell").mean().to_numpy(float)
        sampled = rng.choice(cell_values, size=(draws, len(cell_values)), replace=True).mean(axis=1)
        split_values = differences.groupby("split").mean()
        output[name] = {
            "mean_absolute_rmse_gain": float(cell_values.mean()),
            "ci95_low": float(np.quantile(sampled, 0.025)),
            "ci95_high": float(np.quantile(sampled, 0.975)),
            "positive_cells": int((cell_values > 0).sum()),
            "n_cells": int(len(cell_values)),
            "positive_splits": int((split_values > 0).sum()),
            "n_splits": int(len(split_values)),
            "split_mean_gains": [float(value) for value in split_values],
        }
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-cycles", type=Path, required=True)
    parser.add_argument("--test-cycles", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT / "config" / "cross_temperature_audit_rerun.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT / "results" / "cross_temperature_audit_rerun",
    )
    parser.add_argument("--max-splits", type=int)
    parser.add_argument("--estimator-limit", type=int)
    args = parser.parse_args()

    config = json.loads(args.config.read_text())
    if config["status"] != "AUDIT_LOCKED_BEFORE_CORRECTED_RERUN":
        raise RuntimeError("audit rerun protocol is not locked")
    observed_hashes = {
        "chemistry2-25C": sha256(args.train_cycles),
        "chemistry2-35C": sha256(args.test_cycles),
    }
    if observed_hashes != config["input_cycle_sha256"]:
        raise RuntimeError(f"cycle-table hash mismatch: {observed_hashes}")
    args.output.mkdir(parents=True, exist_ok=True)

    train = add_history(pd.read_csv(args.train_cycles))
    test = add_history(pd.read_csv(args.test_cycles))
    menus = feature_menus(train)
    if set(menus) != set(config["evidence_menus"]):
        raise RuntimeError("implemented evidence menus differ from the locked protocol")
    permutation_seed = config["split"]["seed"] + 991
    train_permuted = permute_eis(train, permutation_seed)
    test_permuted = permute_eis(test, permutation_seed + 1)
    train_frames = {name: train for name in menus}
    test_frames = {name: test for name in menus}
    for name in ("eis_actions_permuted", "old_history_eis_permuted"):
        train_frames[name] = train_permuted
        test_frames[name] = test_permuted

    training_cells = sorted(train["cell"].unique())
    external_cells = sorted(test["cell"].unique())
    expected = config["split"]
    if len(training_cells) != expected["training_cells"] + expected["calibration_cells"]:
        raise RuntimeError("unexpected number of source cells")
    if len(external_cells) != expected["external_test_cells"]:
        raise RuntimeError("unexpected number of external cells")

    splits = partitions(training_cells, expected["calibration_repetitions"], expected["seed"])
    if args.max_splits is not None:
        splits = splits[: args.max_splits]
    result_rows: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []
    seed_offsets = config["model_seed_offsets"]
    if set(seed_offsets) != set(menus):
        raise RuntimeError("model seed offsets differ from the locked evidence menus")
    for split_index, (fit_cells, calibration_cells) in enumerate(splits):
        for menu, columns in menus.items():
            train_frame = train_frames[menu]
            test_frame = test_frames[menu]
            fit = train_frame[train_frame["cell"].isin(fit_cells)]
            calibration = train_frame[train_frame["cell"].isin(calibration_cells)]
            seed = expected["seed"] + 100 * split_index + seed_offsets[menu]

            regressor_config = config["regressor"]
            n_regressors = args.estimator_limit or regressor_config["n_estimators"]
            regressor = make_pipeline(
                SimpleImputer(strategy="median"),
                ExtraTreesRegressor(
                    n_estimators=n_regressors,
                    max_features=regressor_config["max_features"],
                    min_samples_leaf=regressor_config["min_samples_leaf"],
                    n_jobs=-1,
                    random_state=seed,
                ),
            )
            regressor.fit(fit[columns], fit["soh"])
            capacity_prediction = regressor.predict(test_frame[columns])

            classifier_config = config["classifier"]
            n_classifiers = args.estimator_limit or classifier_config["n_estimators"]
            classifier = make_pipeline(
                SimpleImputer(strategy="median"),
                RandomForestClassifier(
                    n_estimators=n_classifiers,
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
            low, high, threshold_metadata = calibrated_thresholds(
                calibration["under_delivery"].to_numpy(),
                calibration_probability,
                config["three_decision"]["alpha"],
                config["three_decision"]["beta"],
            )
            calibration_decisions = decision_metrics(
                calibration["under_delivery"].to_numpy(), calibration_probability, low, high
            )
            external_decisions = decision_metrics(
                test_frame["under_delivery"].to_numpy(), external_probability, low, high
            )
            row: dict[str, object] = {
                "split": split_index,
                "menu": menu,
                "fit_cells": ",".join(fit_cells),
                "calibration_cells": ",".join(calibration_cells),
                "external_cells": ",".join(external_cells),
                "rmse": float(mean_squared_error(test_frame["soh"], capacity_prediction) ** 0.5),
                "mae": float(mean_absolute_error(test_frame["soh"], capacity_prediction)),
                "r2": float(r2_score(test_frame["soh"], capacity_prediction)),
                **external_decisions,
                **threshold_metadata,
                "calibration_coverage": calibration_decisions["coverage"],
                "calibration_alert_rate": calibration_decisions["alert_rate"],
                "calibration_unsafe_certify_error": calibration_decisions[
                    "unsafe_certify_error"
                ],
                "calibration_safe_reject_error": calibration_decisions["safe_reject_error"],
            }
            result_rows.append(row)

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
    effects = paired_effects(metrics)
    effect_summary = paired_summary(effects)
    decision_counts = (
        predictions.groupby(["split", "menu", "decision"]).size().rename("count").reset_index()
    )
    numeric = [
        "rmse",
        "mae",
        "r2",
        "auc",
        "brier",
        "coverage",
        "alert_rate",
        "balanced_decisiveness",
        "unsafe_certify_error",
        "safe_reject_error",
    ]
    medians = metrics.groupby("menu")[numeric].median().reset_index()
    worst = metrics.groupby("menu")[["unsafe_certify_error", "safe_reject_error"]].max()
    bootstrap = bootstrap_cell_comparisons(
        predictions,
        seed=config["split"]["seed"],
        draws=config["aggregation"]["bootstrap_draws"],
    )

    effect_lookup = effect_summary.set_index("comparison")
    metric_lookup = medians.set_index("menu")
    thresholds = config["inherited_development_thresholds"]
    original_checks = {
        "eis_actions_rmse_reduction_vs_actions": bool(
            effect_lookup.loc["eis_actions_vs_actions", "rmse_gain_fraction"]
            >= thresholds["eis_actions_rmse_reduction_vs_actions_fraction"]
        ),
        "old_history_eis_rmse_reduction": bool(
            effect_lookup.loc["old_history_eis_vs_old_history", "rmse_gain_fraction"]
            >= thresholds["old_history_eis_rmse_reduction_vs_old_history_fraction"]
        ),
        "old_history_eis_auc_gain": bool(
            effect_lookup.loc["old_history_eis_vs_old_history", "auc_gain"]
            >= thresholds["old_history_eis_auc_gain_vs_old_history"]
        ),
        "real_eis_beats_permuted_auc": bool(
            effect_lookup.loc["old_history_eis_vs_permuted", "auc_gain"]
            >= thresholds["old_history_eis_auc_gain_vs_permuted"]
        ),
        "median_external_side_errors": bool(
            metric_lookup.loc["old_history_eis", "unsafe_certify_error"]
            <= thresholds["maximum_external_side_error"]
            and metric_lookup.loc["old_history_eis", "safe_reject_error"]
            <= thresholds["maximum_external_side_error"]
        ),
    }
    strict_external_side_errors = bool(
        worst.loc["old_history_eis", "unsafe_certify_error"]
        <= thresholds["maximum_external_side_error"]
        and worst.loc["old_history_eis", "safe_reject_error"]
        <= thresholds["maximum_external_side_error"]
    )
    integrity_checks = {
        "input_hashes": True,
        "paired_effect_rows_complete": len(effects) == len(splits) * 4,
        "all_thresholds_strictly_ordered": bool(
            (metrics["threshold_certify"] < metrics["threshold_reject"]).all()
        ),
        "source_side_errors_controlled": bool(
            (
                metrics["calibration_unsafe_certify_error"]
                <= config["three_decision"]["alpha"] + 1e-12
            ).all()
            and (
                metrics["calibration_safe_reject_error"]
                <= config["three_decision"]["beta"] + 1e-12
            ).all()
        ),
    }
    summary = {
        "status": "FAIL" if not all(original_checks.values()) else "PASS",
        "classification": config["classification"],
        "formal_run": args.max_splits is None and args.estimator_limit is None,
        "withdrawn_gate": config["withdrawn_gate"],
        "training_rows": len(train),
        "training_cells": len(training_cells),
        "external_rows": len(test),
        "external_cells": len(external_cells),
        "median_metrics": medians.set_index("menu").to_dict(orient="index"),
        "paired_median_effects": effect_summary.set_index("comparison").to_dict(orient="index"),
        "cell_bootstrap": bootstrap,
        "legacy_threshold_checks_corrected": original_checks,
        "strict_all_splits_external_side_errors": strict_external_side_errors,
        "integrity_checks": integrity_checks,
    }

    for name, frame in (
        ("split_metrics.csv", metrics),
        ("predictions.csv", predictions),
        ("paired_effects.csv", effects),
        ("paired_summary.csv", effect_summary),
        ("median_metrics.csv", medians),
        ("decision_counts.csv", decision_counts),
    ):
        frame.to_csv(args.output / name, index=False, float_format="%.12g")
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output / "config_snapshot.json").write_text(json.dumps(config, indent=2) + "\n")
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": importlib.metadata.version("numpy"),
        "pandas": importlib.metadata.version("pandas"),
        "scipy": importlib.metadata.version("scipy"),
        "scikit_learn": importlib.metadata.version("scikit-learn"),
    }
    (args.output / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    (args.output / "input_hashes.json").write_text(json.dumps(observed_hashes, indent=2) + "\n")

    split_display = metrics[
        [
            "split",
            "menu",
            "rmse",
            "auc",
            "alert_rate",
            "unsafe_certify_error",
            "safe_reject_error",
        ]
    ].copy()
    for column in split_display.columns[2:]:
        split_display[column] = split_display[column].map(lambda value: f"{value:.4f}")
    effect_display = effect_summary.copy()
    for column in effect_display.columns[1:]:
        effect_display[column] = effect_display[column].map(lambda value: f"{value:.4f}")
    lines = [
        "# Jones EIS audit-locked cross-temperature rerun",
        "",
        f"**Corrected external certification gate: {summary['status']}**",
        "",
        "> Method-corrected diagnostic rerun on an already inspected external cohort; not a fresh confirmation.",
        "",
        "## Paired effects",
        "",
        "Every effect is computed within split before taking the median.",
        "",
        "| " + " | ".join(effect_display.columns) + " |",
        "|" + "|".join(["---"] + ["---:"] * (len(effect_display.columns) - 1)) + "|",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in effect_display.to_numpy())
    lines.extend(
        [
            "",
            "## Every registered split",
            "",
            "No synthetic median row is interpreted as an observed split.",
            "",
            "| " + " | ".join(split_display.columns) + " |",
            "|" + "|".join(["---", "---"] + ["---:"] * (len(split_display.columns) - 2)) + "|",
        ]
    )
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in split_display.to_numpy())
    lines.extend(["", "## Corrected legacy checks", "", "| Check | Result |", "|---|---:|"])
    lines.extend(
        f"| {name} | {'PASS' if value else 'FAIL'} |" for name, value in original_checks.items()
    )
    lines.extend(
        [
            f"| strict_all_splits_external_side_errors | {'PASS' if strict_external_side_errors else 'FAIL'} |",
            "",
            "## Scope",
            "",
            "The balanced-decisiveness gain gate is withdrawn because the legacy baseline was a degenerate two-decision rule. Uncontrolled RMSE gains remain descriptive. Controlled EIS value is evaluated against the paired within-cell permutation arm.",
        ]
    )
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
