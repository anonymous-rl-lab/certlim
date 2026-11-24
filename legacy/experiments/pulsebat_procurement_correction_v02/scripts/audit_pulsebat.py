#!/usr/bin/env python3
"""Corrective PulseBat audit without modifying the frozen repo_v5 release.

The audit treats operating SOC as part of the evidence experiment, separates
convex-hull and pairwise geometry, and repeats the released whole-battery
permutation/bootstrap procedure for every SOC-by-menu point.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy


HERE = Path(__file__).resolve().parent
OVERLAY = HERE.parent
WORKSPACE = OVERLAY.parent
SIBLING_SOURCE = OVERLAY.parent / "pulsebat_procurement_external"
SOURCE = (
    SIBLING_SOURCE
    if SIBLING_SOURCE.exists()
    else WORKSPACE / "repo_v5" / "experiments" / "pulsebat_procurement_external"
)
sys.path.insert(0, str(SOURCE / "src"))

from pulsebat_gate.analysis import (  # noqa: E402
    FEATURES,
    add_registered_columns,
    calibration_thresholds,
    categorical_pmf,
)
from pulsebat_gate.core import convex_hull_tv, disjoint_block_laws, multinomial_law  # noqa: E402


CHEMISTRIES = ("LMO10", "LFP35")
MENUS = ("ocv", "pulse_0p5C", "pulse_1C", "pulse_1p5C")
SOCS = tuple(range(5, 51, 5))
PSEUDO = 0.5
BINS = 4
BASE_SEED = 20260826


def seed_for(soc: int, menu: str) -> int:
    if soc == 5 and menu == "pulse_0p5C":
        return BASE_SEED
    digest = hashlib.sha256(f"{BASE_SEED}:{soc}:{menu}".encode()).digest()
    return int.from_bytes(digest[:8], "little")


def symbols_and_thresholds(df: pd.DataFrame, soc: int) -> tuple[pd.DataFrame, dict]:
    all_soc = df[df.SOC == soc].copy()
    eligible = all_soc[all_soc.grade != "buffer"].copy()
    thresholds = calibration_thresholds(all_soc, BINS)
    for menu, feature in FEATURES.items():
        eligible[f"symbol:{menu}"] = [
            int(np.digitize(value, thresholds[(chemistry, menu)]))
            for value, chemistry in zip(eligible[feature], eligible.chemistry, strict=True)
        ]
    return eligible, thresholds


def pmf_from_symbols(symbols: np.ndarray) -> np.ndarray:
    counts = np.bincount(np.asarray(symbols, dtype=int), minlength=BINS).astype(float)
    return (counts + PSEUDO) / (counts.sum() + BINS * PSEUDO)


def two_block_hull_tv(p: np.ndarray, q: np.ndarray, r: np.ndarray, s: np.ndarray) -> float:
    """Exact two-block convex-hull TV by enumerating LP break-line vertices."""
    lines = [
        (1.0, 0.0, 0.0),
        (1.0, 0.0, 1.0),
        (0.0, 1.0, 0.0),
        (0.0, 1.0, 1.0),
    ]
    lines.extend((float(pi), float(-qi), 0.0) for pi, qi in zip(p, q, strict=True))
    lines.extend(
        (float(ri), float(-si), float(ri - si))
        for ri, si in zip(r, s, strict=True)
    )
    candidates = []
    for i, (a1, b1, c1) in enumerate(lines):
        for a2, b2, c2 in lines[i + 1 :]:
            determinant = a1 * b2 - a2 * b1
            if abs(determinant) < 1e-14:
                continue
            lam = (c1 * b2 - c2 * b1) / determinant
            mu = (a1 * c2 - a2 * c1) / determinant
            if -1e-12 <= lam <= 1 + 1e-12 and -1e-12 <= mu <= 1 + 1e-12:
                candidates.append((min(1.0, max(0.0, lam)), min(1.0, max(0.0, mu))))
    values = [
        0.5 * (np.abs(lam * p - mu * q).sum() + np.abs((1 - lam) * r - (1 - mu) * s).sum())
        for lam, mu in candidates
    ]
    return float(min(values))


def delta_pairwise(labeled: pd.DataFrame, menu: str) -> tuple[float, dict[str, float]]:
    distances = {}
    laws = {}
    for chemistry in CHEMISTRIES:
        part = labeled[labeled.chemistry == chemistry]
        safe = pmf_from_symbols(part.loc[part.grade == "safe", f"symbol:{menu}"].to_numpy())
        unsafe = pmf_from_symbols(part.loc[part.grade == "unsafe", f"symbol:{menu}"].to_numpy())
        laws[chemistry] = (safe, unsafe)
        distances[chemistry] = float(0.5 * np.abs(safe - unsafe).sum())
    exact = two_block_hull_tv(
        laws["LMO10"][0], laws["LMO10"][1], laws["LFP35"][0], laws["LFP35"][1]
    )
    return exact, distances


def build_pmfs_from_labeled(labeled: pd.DataFrame, menu: str) -> dict:
    pmfs = {}
    for chemistry in CHEMISTRIES:
        for grade in ("safe", "unsafe"):
            part = labeled[(labeled.chemistry == chemistry) & (labeled.grade == grade)]
            pmfs[(menu, chemistry, grade)] = pmf_from_symbols(part[f"symbol:{menu}"].to_numpy())
    return pmfs


def point_uncertainty(
    eligible: pd.DataFrame,
    menu: str,
    soc: int,
    permutations: int,
    bootstraps: int,
) -> tuple[dict, list[dict]]:
    rng = np.random.default_rng(seed_for(soc, menu))
    observed, chemistry_tv = delta_pairwise(eligible, menu)
    samples: list[dict] = []

    symbol_column = f"symbol:{menu}"
    chemistry_arrays = {}
    for chemistry in CHEMISTRIES:
        part = eligible[eligible.chemistry == chemistry]
        chemistry_arrays[chemistry] = {
            "symbols": part[symbol_column].to_numpy(dtype=int),
            "grades": part.grade.to_numpy(),
        }

    def minimum_tv(parts: dict[str, tuple[np.ndarray, np.ndarray]]) -> float:
        laws = {}
        for chemistry in CHEMISTRIES:
            safe_symbols, unsafe_symbols = parts[chemistry]
            p = pmf_from_symbols(safe_symbols)
            q = pmf_from_symbols(unsafe_symbols)
            laws[chemistry] = (p, q)
        return two_block_hull_tv(
            laws["LMO10"][0], laws["LMO10"][1], laws["LFP35"][0], laws["LFP35"][1]
        )

    permutation_values = []
    for replicate in range(permutations):
        parts = {}
        for chemistry in CHEMISTRIES:
            values = chemistry_arrays[chemistry]
            labels = rng.permutation(values["grades"])
            symbols = values["symbols"]
            parts[chemistry] = (symbols[labels == "safe"], symbols[labels == "unsafe"])
        value = minimum_tv(parts)
        permutation_values.append(value)
        samples.append({"soc": soc, "menu": menu, "kind": "permutation", "replicate": replicate, "delta_one": value})

    strata = {
        (chemistry, grade): eligible[
            (eligible.chemistry == chemistry) & (eligible.grade == grade)
        ][symbol_column].to_numpy(dtype=int)
        for chemistry in CHEMISTRIES
        for grade in ("safe", "unsafe")
    }
    bootstrap_values = []
    for replicate in range(bootstraps):
        parts = {}
        # Match pandas groupby(sort=True): LFP35 precedes LMO10, but the TV
        # minimum is chemistry-order invariant.  RNG draws retain that order
        # so the registered point reproduces the released uncertainty file.
        draws = {}
        for key in sorted(strata):
            symbols = strata[key]
            draws[key] = symbols[rng.integers(0, len(symbols), size=len(symbols))]
        for chemistry in CHEMISTRIES:
            parts[chemistry] = (draws[(chemistry, "safe")], draws[(chemistry, "unsafe")])
        value = minimum_tv(parts)
        bootstrap_values.append(value)
        samples.append({"soc": soc, "menu": menu, "kind": "bootstrap", "replicate": replicate, "delta_one": value})

    perm = np.asarray(permutation_values)
    boot = np.asarray(bootstrap_values)
    ci = np.quantile(boot, [0.025, 0.5, 0.975])
    return {
        "soc": soc,
        "menu": menu,
        "observed_delta_one": observed,
        "lmo10_pairwise_tv": chemistry_tv["LMO10"],
        "lfp35_pairwise_tv": chemistry_tv["LFP35"],
        "load_bearing_chemistry": min(chemistry_tv, key=chemistry_tv.get),
        "permutations": permutations,
        "permutation_p": float((1 + np.sum(perm >= observed - 1e-12)) / (1 + len(perm))),
        "permutation_null_mean": float(perm.mean()),
        "permutation_null_q95": float(np.quantile(perm, 0.95)),
        "bootstrap_replicates": bootstraps,
        "bootstrap_ci95_low": float(ci[0]),
        "bootstrap_median": float(ci[1]),
        "bootstrap_ci95_high": float(ci[2]),
    }, samples


def pairwise_hull_audit(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    eligible, _ = symbols_and_thresholds(df, 5)
    for menu in MENUS:
        pmfs = build_pmfs_from_labeled(eligible, menu)
        for n in (1, 2, 3, 4, 5, 6, 8, 10, 12):
            safe, unsafe = disjoint_block_laws(pmfs, menu, n)
            hull = convex_hull_tv(safe, unsafe)
            pairwise = {}
            for chemistry in CHEMISTRIES:
                p = multinomial_law(pmfs[(menu, chemistry, "safe")], n)
                q = multinomial_law(pmfs[(menu, chemistry, "unsafe")], n)
                pairwise[chemistry] = float(0.5 * np.abs(p - q).sum())
            minimum = min(pairwise.values())
            rows.append({
                "soc": 5,
                "menu": menu,
                "n": n,
                "convex_hull_delta": hull,
                "minimum_pairwise_tv": minimum,
                "absolute_difference": abs(hull - minimum),
                "lmo10_pairwise_tv": pairwise["LMO10"],
                "lfp35_pairwise_tv": pairwise["LFP35"],
                "load_bearing_chemistry": min(pairwise, key=pairwise.get),
            })
    return pd.DataFrame(rows)


def leave_one_out(df: pd.DataFrame) -> pd.DataFrame:
    eligible, _ = symbols_and_thresholds(df, 5)
    rows = []
    observed, _ = delta_pairwise(eligible, "pulse_0p5C")
    for chemistry in CHEMISTRIES:
        for battery_id in sorted(eligible.loc[eligible.chemistry == chemistry, "ID"].unique()):
            sample = eligible[eligible.ID != battery_id]
            value, distances = delta_pairwise(sample, "pulse_0p5C")
            rows.append({
                "deleted_chemistry": chemistry,
                "deleted_id": battery_id,
                "observed_delta_one": observed,
                "leave_one_out_delta_one": value,
                "change": value - observed,
                "lmo10_pairwise_tv": distances["LMO10"],
                "lfp35_pairwise_tv": distances["LFP35"],
            })
    return pd.DataFrame(rows)


def paired_bootstrap_contrast(
    df: pd.DataFrame,
    bootstraps: int,
) -> tuple[dict, pd.DataFrame]:
    low, _ = symbols_and_thresholds(df, 5)
    high, _ = symbols_and_thresholds(df, 10)
    low = low.set_index("ID", drop=False)
    high = high.set_index("ID", drop=False)
    common = sorted(set(low.index) & set(high.index))
    low = low.loc[common]
    high = high.loc[common]
    observed_low, _ = delta_pairwise(low, "pulse_0p5C")
    observed_high, _ = delta_pairwise(high, "ocv")

    strata = []
    for chemistry in CHEMISTRIES:
        for grade in ("safe", "unsafe"):
            ids = low[(low.chemistry == chemistry) & (low.grade == grade)].ID.to_numpy()
            strata.append(ids)

    rng = np.random.default_rng(BASE_SEED + 1010)
    rows = []
    for replicate in range(bootstraps):
        sampled_ids = np.concatenate([ids[rng.integers(0, len(ids), size=len(ids))] for ids in strata])
        low_sample = low.loc[sampled_ids].reset_index(drop=True)
        high_sample = high.loc[sampled_ids].reset_index(drop=True)
        d_low, _ = delta_pairwise(low_sample, "pulse_0p5C")
        d_high, _ = delta_pairwise(high_sample, "ocv")
        rows.append({
            "replicate": replicate,
            "soc10_ocv_delta": d_high,
            "soc5_pulse_0p5C_delta": d_low,
            "difference": d_high - d_low,
        })
    samples = pd.DataFrame(rows)
    ci = samples.difference.quantile([0.025, 0.5, 0.975]).to_numpy()
    summary = {
        "contrast": "SOC10 OCV minus SOC5 pulse_0p5C",
        "observed_soc10_ocv_delta": observed_high,
        "observed_soc5_pulse_delta": observed_low,
        "observed_difference": observed_high - observed_low,
        "paired_whole_battery_bootstrap_replicates": bootstraps,
        "difference_ci95": [float(ci[0]), float(ci[2])],
        "difference_median": float(ci[1]),
        "probability_difference_positive": float((samples.difference > 0).mean()),
    }
    return summary, samples


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--permutations", type=int, default=999)
    parser.add_argument("--bootstraps", type=int, default=2000)
    parser.add_argument("--tag", default="full")
    args = parser.parse_args()

    outdir = OVERLAY / "results" / args.tag
    outdir.mkdir(parents=True, exist_ok=True)
    df = add_registered_columns(pd.read_csv(SOURCE / "data" / "processed" / "observations.csv"))

    grid_rows, all_samples = [], []
    for soc in SOCS:
        eligible, _ = symbols_and_thresholds(df, soc)
        for menu in MENUS:
            summary, samples = point_uncertainty(eligible, menu, soc, args.permutations, args.bootstraps)
            grid_rows.append(summary)
            all_samples.extend(samples)

    grid = pd.DataFrame(grid_rows)
    hull = pairwise_hull_audit(df)
    loo = leave_one_out(df)
    contrast, contrast_samples = paired_bootstrap_contrast(df, args.bootstraps)

    grid.to_csv(outdir / "soc_menu_uncertainty.csv", index=False, float_format="%.12g")
    pd.DataFrame(all_samples).to_csv(outdir / "soc_menu_samples.csv", index=False, float_format="%.12g")
    hull.to_csv(outdir / "pairwise_hull_audit.csv", index=False, float_format="%.12g")
    loo.to_csv(outdir / "leave_one_out.csv", index=False, float_format="%.12g")
    contrast_samples.to_csv(outdir / "paired_contrast_samples.csv", index=False, float_format="%.12g")

    registered = grid[(grid.soc == 5) & (grid.menu == "pulse_0p5C")].iloc[0]
    key = grid[(grid.soc == 10) & (grid.menu == "ocv")].iloc[0]
    summary = {
        "audit_scope": "corrective overlay; frozen repo_v5 unchanged",
        "permutations_per_point": args.permutations,
        "bootstraps_per_point": args.bootstraps,
        "grid_points": len(grid),
        "max_hull_pairwise_difference": float(hull.absolute_difference.max()),
        "registered_point_reproduction": {
            "delta": float(registered.observed_delta_one),
            "permutation_p": float(registered.permutation_p),
            "bootstrap_ci95": [float(registered.bootstrap_ci95_low), float(registered.bootstrap_ci95_high)],
        },
        "soc10_ocv": {
            "delta": float(key.observed_delta_one),
            "permutation_p": float(key.permutation_p),
            "bootstrap_ci95": [float(key.bootstrap_ci95_low), float(key.bootstrap_ci95_high)],
        },
        "paired_contrast": contrast,
        "load_bearing_counts": {
            "LMO10_safe": int(((df.SOC == 5) & (df.chemistry == "LMO10") & (df.grade == "safe")).sum()),
            "LMO10_unsafe": int(((df.SOC == 5) & (df.chemistry == "LMO10") & (df.grade == "unsafe")).sum()),
            "LFP35_safe": int(((df.SOC == 5) & (df.chemistry == "LFP35") & (df.grade == "safe")).sum()),
            "LFP35_unsafe": int(((df.SOC == 5) & (df.chemistry == "LFP35") & (df.grade == "unsafe")).sum()),
        },
        "software": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
    }
    (outdir / "audit_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
