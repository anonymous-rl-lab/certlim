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
from scipy.optimize import linprog
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PROJECT = Path(__file__).resolve().parents[1]


def add_history(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values(["cell", "cycle"]).copy()
    groups = frame.groupby("cell", sort=False)
    for lag in range(1, 6):
        frame[f"capacity_soh_lag{lag}"] = groups["soh"].shift(lag)
    action_columns = ["charge_stage1_ma", "charge_stage2_ma", "discharge_current_ma"]
    for column in action_columns:
        for lag in range(1, 4):
            frame[f"{column}_lag{lag}"] = groups[column].shift(lag)
    frame["under_delivery"] = (frame["soh"] < 0.50).astype(int)
    frame["environment"] = frame["cell"] + "_w" + ((frame["cycle"] - 1) // 20).astype(str)
    return frame


def feature_menus(frame: pd.DataFrame) -> dict[str, list[str]]:
    snapshot = [
        "cycle",
        "previous_soh",
        "cumulative_throughput_mah",
        "ocv_v",
        "charge_stage1_ma",
        "charge_stage2_ma",
        "discharge_current_ma",
    ]
    history = snapshot + [f"capacity_soh_lag{lag}" for lag in range(1, 6)]
    history += [
        f"{column}_lag{lag}"
        for column in ("charge_stage1_ma", "charge_stage2_ma", "discharge_current_ma")
        for lag in range(1, 4)
    ]
    eis = sorted(column for column in frame if column.startswith("eis_re_") or column.startswith("eis_neg_im_"))
    return {
        "old_snapshot": snapshot,
        "old_history": history,
        "old_history_eis": history + eis,
        "old_history_eis_permuted": history + eis,
    }


def permute_eis_within_cell(frame: pd.DataFrame, seed: int) -> pd.DataFrame:
    result = frame.copy()
    columns = sorted(
        column for column in frame if column.startswith("eis_re_") or column.startswith("eis_neg_im_")
    )
    rng = np.random.default_rng(seed)
    for _, indices in frame.groupby("cell").groups.items():
        indices = np.asarray(list(indices))
        donor = rng.permutation(indices)
        result.loc[indices, columns] = frame.loc[donor, columns].to_numpy()
    return result


def calibrated_thresholds(
    y: np.ndarray,
    probability: np.ndarray,
    alpha: float,
    beta: float,
    crossed_threshold_handling: str = "legacy_collapse",
) -> tuple[float, float]:
    unsafe = np.sort(probability[y == 1])
    safe = np.sort(probability[y == 0])
    if len(unsafe) == 0 or len(safe) == 0:
        raise RuntimeError("calibration partition does not contain both endpoint classes")

    allowed_certify = int(np.floor(alpha * len(unsafe)))
    if allowed_certify == 0:
        low = float(np.nextafter(unsafe[0], -np.inf))
    elif allowed_certify >= len(unsafe):
        low = float(np.nextafter(unsafe[-1], np.inf))
    else:
        low = float((unsafe[allowed_certify - 1] + unsafe[allowed_certify]) / 2)

    allowed_reject = int(np.floor(beta * len(safe)))
    if allowed_reject == 0:
        high = float(np.nextafter(safe[-1], np.inf))
    elif allowed_reject >= len(safe):
        high = float(np.nextafter(safe[0], -np.inf))
    else:
        boundary = len(safe) - allowed_reject
        high = float((safe[boundary - 1] + safe[boundary]) / 2)

    if low >= high:
        if crossed_threshold_handling == "conservative_ordering":
            low, high = high, low
            if low == high:
                low = float(np.nextafter(low, -np.inf))
                high = float(np.nextafter(high, np.inf))
        elif crossed_threshold_handling == "legacy_collapse":
            midpoint = (low + high) / 2
            low = float(np.nextafter(midpoint, -np.inf))
            high = float(np.nextafter(midpoint, np.inf))
        else:
            raise RuntimeError(f"unknown crossed-threshold handling: {crossed_threshold_handling}")
    return low, high


def decision_metrics(y: np.ndarray, probability: np.ndarray, low: float, high: float) -> dict[str, float]:
    certify = probability <= low
    reject = probability >= high
    decisive = certify | reject
    unsafe = y == 1
    safe = y == 0
    unsafe_coverage = float(decisive[unsafe].mean())
    safe_coverage = float(decisive[safe].mean())
    return {
        "auc": float(roc_auc_score(y, probability)),
        "brier": float(brier_score_loss(y, probability)),
        "coverage": float(decisive.mean()),
        "unsafe_coverage": unsafe_coverage,
        "safe_coverage": safe_coverage,
        "balanced_decisiveness": min(unsafe_coverage, safe_coverage),
        "unsafe_certify_error": float(certify[unsafe].mean()),
        "safe_reject_error": float(reject[safe].mean()),
        "threshold_certify": low,
        "threshold_reject": high,
    }


def cell_splits(cells: list[str], repetitions: int, seed: int) -> list[tuple[list[str], list[str], list[str]]]:
    rng = np.random.default_rng(seed)
    output = []
    for _ in range(repetitions):
        shuffled = list(rng.permutation(cells))
        output.append((shuffled[:8], shuffled[8:12], shuffled[12:16]))
    return output


def product_rows(histograms: np.ndarray, block_length: int) -> np.ndarray:
    result = histograms.copy()
    for _ in range(1, block_length):
        result = np.stack([np.kron(row, base) for row, base in zip(result, histograms)])
    return result


def convex_hull_tv(safe: np.ndarray, unsafe: np.ndarray) -> float:
    ns, nu = len(safe), len(unsafe)
    k = safe.shape[1]
    objective = np.r_[np.zeros(ns + nu), np.full(k, 0.5)]
    a_ub = np.zeros((2 * k, ns + nu + k))
    b_ub = np.zeros(2 * k)
    for index in range(k):
        difference = np.r_[safe[:, index], -unsafe[:, index]]
        a_ub[2 * index, : ns + nu] = difference
        a_ub[2 * index, ns + nu + index] = -1
        a_ub[2 * index + 1, : ns + nu] = -difference
        a_ub[2 * index + 1, ns + nu + index] = -1
    a_eq = np.zeros((2, ns + nu + k))
    a_eq[0, :ns] = 1
    a_eq[1, ns : ns + nu] = 1
    result = linprog(
        objective,
        A_ub=a_ub,
        b_ub=b_ub,
        A_eq=a_eq,
        b_eq=np.ones(2),
        bounds=(0, None),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"TV linear program failed: {result.message}")
    return float(max(0.0, min(1.0, result.fun)))


def geometry_diagnostic(
    frame_by_menu: dict[str, pd.DataFrame],
    menus: dict[str, list[str]],
    config: dict[str, object],
) -> pd.DataFrame:
    geometry = config["geometry"]
    risks = frame_by_menu["old_history"].groupby("environment").agg(
        n=("under_delivery", "size"), risk=("under_delivery", "mean"), cell=("cell", "first")
    )
    risks = risks[risks["n"] >= geometry["minimum_observations"]]
    grade = pd.Series("buffer", index=risks.index)
    grade.loc[risks["risk"] <= geometry["safe_risk_upper"]] = "safe"
    grade.loc[risks["risk"] >= geometry["unsafe_risk_lower"]] = "unsafe"
    if (grade == "safe").sum() < 2 or (grade == "unsafe").sum() < 2:
        raise RuntimeError("too few safe/unsafe environments for the registered geometry diagnostic")

    rows: list[dict[str, object]] = []
    for menu_name in ("old_history", "old_history_eis", "old_history_eis_permuted"):
        frame = frame_by_menu[menu_name]
        columns = menus[menu_name]
        for seed in geometry["quantizer_seeds"]:
            n_components = min(10, len(columns), len(frame) - 1)
            transform = make_pipeline(
                SimpleImputer(strategy="median"),
                StandardScaler(),
                PCA(n_components=n_components, random_state=seed),
            )
            coordinates = transform.fit_transform(frame[columns])
            labels = KMeans(
                n_clusters=geometry["quantizer_bins"], n_init=20, random_state=seed
            ).fit_predict(coordinates)
            temporary = pd.DataFrame({"environment": frame["environment"], "bin": labels})
            histogram = pd.crosstab(temporary["environment"], temporary["bin"], normalize="index")
            histogram = histogram.reindex(index=risks.index, columns=range(geometry["quantizer_bins"]), fill_value=0)
            safe_hist = histogram.loc[grade == "safe"].to_numpy(float)
            unsafe_hist = histogram.loc[grade == "unsafe"].to_numpy(float)
            for block_length in geometry["block_lengths"]:
                delta = convex_hull_tv(
                    product_rows(safe_hist, block_length),
                    product_rows(unsafe_hist, block_length),
                )
                rows.append(
                    {
                        "menu": menu_name,
                        "seed": seed,
                        "block_length": block_length,
                        "delta_hat": delta,
                        "safe_environments": int((grade == "safe").sum()),
                        "buffer_environments": int((grade == "buffer").sum()),
                        "unsafe_environments": int((grade == "unsafe").sum()),
                    }
                )
    return pd.DataFrame(rows)


def run_classification(
    frame_by_menu: dict[str, pd.DataFrame], menus: dict[str, list[str]], config: dict[str, object]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_config = config["split"]
    model_config = config["model"]
    decision_config = config["three_decision"]
    cells = sorted(frame_by_menu["old_history"]["cell"].unique())
    splits = cell_splits(cells, split_config["repetitions"], split_config["seed"])
    metric_rows: list[dict[str, object]] = []
    prediction_rows: list[pd.DataFrame] = []
    for split_index, (train_cells, calibration_cells, test_cells) in enumerate(splits):
        seed_offsets = config.get("model_seed_offsets")
        for menu_index, menu_name in enumerate(menus):
            frame = frame_by_menu[menu_name]
            columns = menus[menu_name]
            train = frame[frame["cell"].isin(train_cells)]
            calibration = frame[frame["cell"].isin(calibration_cells)]
            test = frame[frame["cell"].isin(test_cells)]
            model = make_pipeline(
                SimpleImputer(strategy="median"),
                RandomForestClassifier(
                    n_estimators=model_config["n_estimators"],
                    max_depth=model_config["max_depth"],
                    min_samples_leaf=model_config["min_samples_leaf"],
                    class_weight=model_config["class_weight"],
                    max_features="sqrt",
                    n_jobs=-1,
                    random_state=(
                        split_config["seed"]
                        + 100 * split_index
                        + (seed_offsets[menu_name] if seed_offsets else menu_index)
                    ),
                ),
            )
            model.fit(train[columns], train["under_delivery"])
            calibration_probability = model.predict_proba(calibration[columns])[:, 1]
            test_probability = model.predict_proba(test[columns])[:, 1]
            low, high = calibrated_thresholds(
                calibration["under_delivery"].to_numpy(),
                calibration_probability,
                decision_config["alpha"],
                decision_config["beta"],
                decision_config.get("crossed_threshold_handling", "legacy_collapse"),
            )
            metrics = decision_metrics(
                test["under_delivery"].to_numpy(), test_probability, low, high
            )
            metrics.update(
                {
                    "split": split_index,
                    "menu": menu_name,
                    "train_cells": ",".join(train_cells),
                    "calibration_cells": ",".join(calibration_cells),
                    "test_cells": ",".join(test_cells),
                    "n_test": len(test),
                }
            )
            metric_rows.append(metrics)
            prediction = test.loc[:, ["cell", "cycle", "soh", "under_delivery"]].copy()
            prediction["probability"] = test_probability
            prediction["decision"] = np.where(
                test_probability <= low,
                "Certify",
                np.where(test_probability >= high, "Reject", "Alert"),
            )
            prediction["split"] = split_index
            prediction["menu"] = menu_name
            prediction_rows.append(prediction)
    return pd.DataFrame(metric_rows), pd.concat(prediction_rows, ignore_index=True)


def median_table(metrics: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        "auc",
        "brier",
        "coverage",
        "balanced_decisiveness",
        "unsafe_certify_error",
        "safe_reject_error",
    ]
    return metrics.groupby("menu")[numeric].median().reset_index()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=Path, default=PROJECT / "results" / "smoke" / "cycles.csv")
    parser.add_argument("--config", type=Path, default=PROJECT / "config" / "small.json")
    parser.add_argument("--output", type=Path, default=PROJECT / "results" / "small")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if config["status"] not in {"FROZEN_BEFORE_MODEL_FIT", "AUDIT_LOCKED_BEFORE_CORRECTED_RERUN"}:
        raise RuntimeError("small protocol is not frozen")
    audit_rerun = config["status"] == "AUDIT_LOCKED_BEFORE_CORRECTED_RERUN"
    if audit_rerun:
        digest = hashlib.sha256(args.cycles.read_bytes()).hexdigest()
        if digest != config["input_cycle_sha256"]:
            raise RuntimeError(f"cycle-table hash mismatch: {digest}")
    args.output.mkdir(parents=True, exist_ok=True)

    frame = add_history(pd.read_csv(args.cycles))
    permuted = permute_eis_within_cell(frame, seed=config["split"]["seed"] + 991)
    menus = feature_menus(frame)
    frames = {name: frame for name in menus}
    frames["old_history_eis_permuted"] = permuted

    metrics, predictions = run_classification(frames, menus, config)
    geometry = geometry_diagnostic(frames, menus, config)
    metrics.to_csv(args.output / "split_metrics.csv", index=False, float_format="%.12g")
    predictions.to_csv(args.output / "predictions.csv", index=False, float_format="%.12g")
    geometry.to_csv(args.output / "geometry.csv", index=False, float_format="%.12g")
    medians = median_table(metrics)
    medians.to_csv(args.output / "median_metrics.csv", index=False, float_format="%.12g")

    by_menu = medians.set_index("menu")
    geom_median = geometry.groupby(["menu", "block_length"])["delta_hat"].median()
    old = by_menu.loc["old_history"]
    new = by_menu.loc["old_history_eis"]
    permuted_row = by_menu.loc["old_history_eis_permuted"]
    thresholds = config.get("inherited_development_thresholds", config.get("development_success_gates"))
    metric_lookup = metrics.set_index(["split", "menu"])
    paired_rows = []
    for split in sorted(metrics["split"].unique()):
        old_split = metric_lookup.loc[(split, "old_history")]
        new_split = metric_lookup.loc[(split, "old_history_eis")]
        permuted_split = metric_lookup.loc[(split, "old_history_eis_permuted")]
        paired_rows.append(
            {
                "split": split,
                "auc_gain_vs_old_history": new_split.auc - old_split.auc,
                "brier_reduction_vs_old_history": old_split.brier - new_split.brier,
                "auc_gain_vs_permuted_eis": new_split.auc - permuted_split.auc,
            }
        )
    paired = pd.DataFrame(paired_rows)
    paired.to_csv(args.output / "paired_effects.csv", index=False, float_format="%.12g")
    paired_median = paired.drop(columns="split").median(numeric_only=True)
    checks = {
        "auc_gain_vs_old_history": bool(
            paired_median["auc_gain_vs_old_history"] >= thresholds["auc_gain_vs_old_history"]
        ),
        "brier_reduction_vs_old_history": bool(
            paired_median["brier_reduction_vs_old_history"]
            >= thresholds["brier_reduction_vs_old_history"]
        ),
        "new_menu_side_errors": bool(
            new.unsafe_certify_error <= thresholds["maximum_test_side_error"]
            and new.safe_reject_error <= thresholds["maximum_test_side_error"]
        ),
        "auc_gain_vs_permuted_eis": bool(
            paired_median["auc_gain_vs_permuted_eis"] >= thresholds["auc_gain_vs_permuted_eis"]
        ),
    }
    structural_checks = {
        "delta_monotonicity": bool(
            geometry.sort_values("block_length")
            .groupby(["menu", "seed"])["delta_hat"]
            .apply(lambda values: np.all(np.diff(values.to_numpy()) >= -1e-8))
            .all()
        ),
    }
    cost = {
        "median_eis_acquisition_seconds": float(frame["eis_duration_s"].median()),
        "p90_eis_acquisition_seconds": float(frame["eis_duration_s"].quantile(0.90)),
    }
    summary = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "classification": config.get("classification", "legacy development run"),
        "interpretation": "development gate only; not a confirmatory causal certification result",
        "geometry_warning": (
            "The per-menu independent KMeans quantizers do not preserve evidence nesting; "
            "cross-menu delta comparisons are withdrawn. Use scripts/run_nested_geometry.py."
        ),
        "n_rows": len(frame),
        "n_cells": int(frame["cell"].nunique()),
        "endpoint_prevalence": float(frame["under_delivery"].mean()),
        "median_metrics": medians.set_index("menu").to_dict(orient="index"),
        "median_delta": {
            f"{menu}_n{block}": float(value) for (menu, block), value in geom_median.items()
        },
        "evidence_time_cost": cost,
        "paired_median_effects": {key: float(value) for key, value in paired_median.items()},
        "scientific_checks": checks,
        "structural_checks": structural_checks,
        "withdrawn_gates": config.get("withdrawn_gates", {}),
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    table = medians.copy()
    for column in table.columns[1:]:
        table[column] = table[column].map(lambda value: f"{value:.3f}")
    lines = [
        "# Jones EIS small development-gate report",
        "",
        f"**Overall registered gate: {summary['status']}**",
        "",
        "> This is a development result for severe under-delivery, not a field-safety label or a confirmatory causal claim.",
        "",
        "> The independent-quantizer delta table is retained for provenance but withdrawn for cross-menu comparison. Use the nested-geometry report.",
        "",
        "## Cell-disjoint predictive and three-decision results",
        "",
        "Median over five registered 8/4/4 cell splits.",
        "",
        "| " + " | ".join(table.columns) + " |",
        "|" + "|".join(["---"] + ["---:"] * (len(table.columns) - 1)) + "|",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in table.to_numpy())
    lines.extend(["", "## Empirical convex-hull separation", ""])
    geometry_table = geometry.groupby(["menu", "block_length"])["delta_hat"].agg(["median", "min", "max"]).reset_index()
    lines.extend(
        [
            "| menu | n | median delta | min | max |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in geometry_table.itertuples(index=False):
        lines.append(f"| {row.menu} | {row.block_length} | {row.median:.3f} | {row.min:.3f} | {row.max:.3f} |")
    split_table = metrics[[
        "split", "menu", "auc", "brier", "coverage", "balanced_decisiveness",
        "unsafe_certify_error", "safe_reject_error",
    ]].copy()
    for column in split_table.columns[2:]:
        split_table[column] = split_table[column].map(lambda value: f"{value:.3f}")
    lines.extend([
        "", "## Every split", "",
        "No synthetic median row is interpreted as an observed split.", "",
        "| " + " | ".join(split_table.columns) + " |",
        "|" + "|".join(["---", "---"] + ["---:"] * (len(split_table.columns) - 2)) + "|",
    ])
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in split_table.to_numpy())
    lines.extend(["", "## Corrected scientific checks", "", "| Check | Result |", "|---|---:|"])
    lines.extend(f"| {key} | {'PASS' if value else 'FAIL'} |" for key, value in checks.items())
    lines.extend(
        [
            "",
            "## Evidence cost",
            "",
            f"- Median observed EIS acquisition time: {cost['median_eis_acquisition_seconds']:.1f} s",
            f"- 90th percentile: {cost['p90_eis_acquisition_seconds']:.1f} s",
            "- These are physical acquisition-time costs only; monetary and operational-integration costs are not in the dataset.",
        ]
    )
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
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
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
