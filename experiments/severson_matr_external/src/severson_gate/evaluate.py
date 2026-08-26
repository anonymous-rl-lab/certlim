"""Frozen regression, conformal decisions, metrics, and gate logic."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .registry import menu_columns


REAL_MENUS = ("protocol", "scalar5", "scalar100", "curve5", "curve100")


def _conformal_radius(scores: np.ndarray, coverage: float) -> float:
    scores = np.sort(np.asarray(scores, dtype=float))
    rank = min(len(scores), math.ceil((len(scores) + 1) * coverage))
    return float(scores[rank - 1])


def _cp_interval(errors: int, total: int, confidence: float = 0.95):
    if total == 0:
        return np.nan, np.nan
    tail = (1.0 - confidence) / 2.0
    lower = 0.0 if errors == 0 else float(beta.ppf(tail, errors, total - errors + 1))
    upper = 1.0 if errors == total else float(beta.ppf(1 - tail, errors + 1, total - errors))
    return lower, upper


def build_model(config: dict) -> Pipeline:
    alphas = np.logspace(
        config["model"]["alpha_grid_log10_min"],
        config["model"]["alpha_grid_log10_max"],
        config["model"]["alpha_grid_size"],
    )
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", RidgeCV(alphas=alphas)),
    ])


def _decision_metrics(frame: pd.DataFrame, config: dict) -> dict[str, float | int]:
    reject_max = config["target"]["reject_max_cycles"]
    certify_min = config["target"]["certify_min_cycles"]
    unsafe = frame["cycle_life"] <= reject_max
    safe = frame["cycle_life"] >= certify_min
    buffer = ~(unsafe | safe)
    false_cert = int(((frame["decision"] == "Certify") & unsafe).sum())
    false_reject = int(((frame["decision"] == "Reject") & safe).sum())
    n_unsafe, n_safe = int(unsafe.sum()), int(safe.sum())
    fc_rate = false_cert / n_unsafe if n_unsafe else np.nan
    fr_rate = false_reject / n_safe if n_safe else np.nan
    unsafe_dec = float((frame.loc[unsafe, "decision"] != "Alert").mean()) if n_unsafe else np.nan
    safe_dec = float((frame.loc[safe, "decision"] != "Alert").mean()) if n_safe else np.nan
    fc_lo, fc_hi = _cp_interval(false_cert, n_unsafe)
    fr_lo, fr_hi = _cp_interval(false_reject, n_safe)
    return {
        "external_unsafe_n": n_unsafe,
        "external_safe_n": n_safe,
        "external_buffer_n": int(buffer.sum()),
        "unsafe_false_certifications": false_cert,
        "unsafe_false_certification_rate": fc_rate,
        "unsafe_false_certification_cp95_lo": fc_lo,
        "unsafe_false_certification_cp95_hi": fc_hi,
        "safe_false_rejections": false_reject,
        "safe_false_rejection_rate": fr_rate,
        "safe_false_rejection_cp95_lo": fr_lo,
        "safe_false_rejection_cp95_hi": fr_hi,
        "unsafe_decisiveness": unsafe_dec,
        "safe_decisiveness": safe_dec,
        "balanced_decisiveness": float(np.nanmean([unsafe_dec, safe_dec])),
        "buffer_certify_n": int(((frame["decision"] == "Certify") & buffer).sum()),
        "buffer_reject_n": int(((frame["decision"] == "Reject") & buffer).sum()),
        "buffer_alert_n": int(((frame["decision"] == "Alert") & buffer).sum()),
    }


def fit_one(data: pd.DataFrame, menu: str, config: dict, permutation_seed: int | None = None):
    base_menu = menu.replace("_permuted", "")
    columns = menu_columns(list(data.columns), base_menu)
    working = data.copy()
    if permutation_seed is not None:
        curve_columns = [c for c in columns if c.startswith("curve")]
        rng = np.random.default_rng(permutation_seed)
        for split in ("fit", "calibration", "external"):
            rows = working.index[working["split"] == split].to_numpy()
            permutation = rng.permutation(rows)
            working.loc[rows, curve_columns] = working.loc[permutation, curve_columns].to_numpy()

    fit = working[working["split"] == "fit"].copy()
    calibration = working[working["split"] == "calibration"].copy()
    external = working[working["split"] == "external"].copy()
    model = build_model(config)
    model.fit(fit[columns], np.log10(fit["cycle_life"]))
    calibration_prediction = model.predict(calibration[columns])
    scores = np.abs(np.log10(calibration["cycle_life"].to_numpy()) - calibration_prediction)
    radius = _conformal_radius(scores, config["conformal"]["nominal_coverage"])

    pred_log = model.predict(external[columns])
    external["prediction"] = np.power(10.0, pred_log)
    external["interval_lower"] = np.power(10.0, pred_log - radius)
    external["interval_upper"] = np.power(10.0, pred_log + radius)
    external["decision"] = np.where(
        external["interval_lower"] >= config["target"]["certify_min_cycles"],
        "Certify",
        np.where(
            external["interval_upper"] <= config["target"]["reject_max_cycles"],
            "Reject",
            "Alert",
        ),
    )
    external["menu"] = menu
    y = external["cycle_life"].to_numpy()
    pred = external["prediction"].to_numpy()
    metrics: dict[str, float | int | str] = {
        "menu": menu,
        "n_features": len(columns),
        "ridge_alpha": float(model.named_steps["ridge"].alpha_),
        "conformal_log10_radius": radius,
        "external_rmse_cycles": float(np.sqrt(mean_squared_error(y, pred))),
        "external_mae_cycles": float(mean_absolute_error(y, pred)),
        "external_mape": float(np.mean(np.abs(pred - y) / y)),
        "external_r2": float(r2_score(y, pred)),
        "external_interval_coverage": float(
            ((y >= external["interval_lower"]) & (y <= external["interval_upper"])).mean()
        ),
        "external_mean_interval_width": float(
            (external["interval_upper"] - external["interval_lower"]).mean()
        ),
    }
    metrics.update(_decision_metrics(external, config))
    return metrics, external[[
        "cell_id", "split", "batch", "cycle_life", "prediction",
        "interval_lower", "interval_upper", "decision", "menu",
    ]]


def evaluate_all(data: pd.DataFrame, config: dict):
    metrics = []
    predictions = []
    for menu in REAL_MENUS:
        row, pred = fit_one(data, menu, config)
        metrics.append(row)
        predictions.append(pred)

    permutation_rows = []
    base_seed = int(config["seed"])
    for index in range(int(config["negative_control_permutations"])):
        for menu in ("curve5", "curve100"):
            seed = base_seed + 1000 * (index + 1) + (5 if menu == "curve5" else 100)
            row, _ = fit_one(data, f"{menu}_permuted", config, permutation_seed=seed)
            row["permutation_index"] = index
            row["permutation_seed"] = seed
            permutation_rows.append(row)

    return pd.DataFrame(metrics), pd.concat(predictions, ignore_index=True), pd.DataFrame(permutation_rows)


def evaluate_gates(metrics: pd.DataFrame, permutations: pd.DataFrame, config: dict, integrity: dict):
    by_menu = metrics.set_index("menu")
    gates = config["gates"]
    curve5_mape = float(by_menu.loc["curve5", "external_mape"])
    scalar100_mape = float(by_menu.loc["scalar100", "external_mape"])
    permutation_median = float(
        permutations.loc[permutations["menu"] == "curve5_permuted", "external_mape"].median()
    )
    g0 = (
        integrity["split_counts"] == {"fit": 41, "calibration": 43, "external": 40}
        and integrity["duplicate_ids"] == []
        and integrity["external_unsafe_n"] >= gates["min_external_unsafe"]
        and integrity["external_safe_n"] >= gates["min_external_safe"]
        and integrity["chronology_ok"]
    )
    g1 = curve5_mape <= scalar100_mape * (1.0 - gates["curve5_mape_improvement_over_scalar100"])
    g2 = curve5_mape <= permutation_median * (
        1.0 - gates["curve5_mape_improvement_over_permutation_median"]
    )
    qualifying = []
    for menu in ("curve5", "curve100"):
        row = by_menu.loc[menu]
        side_ok = (
            row["unsafe_false_certification_rate"] <= gates["max_side_error"]
            and row["safe_false_rejection_rate"] <= gates["max_side_error"]
        )
        decisive = row["balanced_decisiveness"] >= gates["min_balanced_decisiveness"]
        if side_ok and decisive:
            qualifying.append(menu)
    g3 = bool(qualifying)
    g4 = any(
        by_menu.loc[menu, "external_interval_coverage"] >= gates["min_external_interval_coverage"]
        for menu in qualifying
    )
    results = {
        "G0_integrity": bool(g0),
        "G1_curve5_beats_scalar100": bool(g1),
        "G2_curve5_beats_permuted": bool(g2),
        "G3_nonvacuous_certification": bool(g3),
        "G4_transport_calibration": bool(g4),
        "qualifying_curve_menus": qualifying,
        "curve5_external_mape": curve5_mape,
        "scalar100_external_mape": scalar100_mape,
        "curve5_permutation_median_mape": permutation_median,
    }
    results["overall_pass"] = all(results[key] for key in results if key.startswith("G"))
    return results
