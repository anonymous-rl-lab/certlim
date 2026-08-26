"""Registered PulseBat analysis and uncertainty calculations."""

from __future__ import annotations

import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from .core import convex_hull_tv, disjoint_block_laws, exact_decisiveness


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "registered.json"
DATA = ROOT / "data" / "processed" / "observations.csv"
RESULTS = ROOT / "results"
MENUS = ["nameplate", "ocv", "pulse_0p5C", "pulse_1C", "pulse_1p5C"]
FEATURES = {"ocv": "U1", "pulse_0p5C": "r05", "pulse_1C": "r10", "pulse_1p5C": "r15p"}


def load_config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def add_registered_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["r05"] = out["U3"] - out["U7"]
    out["r10"] = out["U11"] - out["U15"]
    out["r15p"] = out["U19"] - out["U21"]
    out["grade"] = np.select(
        [out["SOH"] >= 0.90, out["SOH"] <= 0.80],
        ["safe", "unsafe"],
        default="buffer",
    )
    return out


def calibration_thresholds(all_soc: pd.DataFrame, bins: int = 4) -> dict:
    quantiles = [i / bins for i in range(1, bins)]
    return {
        (chemistry, menu): all_soc[all_soc.chemistry == chemistry][feature].quantile(quantiles).to_numpy()
        for chemistry in ["LMO10", "LFP35"]
        for menu, feature in FEATURES.items()
    }


def categorical_pmf(values: np.ndarray, thresholds: np.ndarray, bins: int, pseudo: float) -> tuple[np.ndarray, np.ndarray]:
    symbols = np.digitize(values, thresholds)
    counts = np.bincount(symbols, minlength=bins).astype(float)
    pmf = (counts + pseudo) / (counts.sum() + bins * pseudo)
    return pmf, counts


def build_pmfs(df: pd.DataFrame, cfg: dict, bins: int = 4) -> tuple[dict, pd.DataFrame, dict]:
    soc = cfg["evidence"]["soc_percent"]
    all_soc = df[df.SOC == soc].copy()
    eligible = all_soc[all_soc.grade != "buffer"].copy()
    thresholds = calibration_thresholds(all_soc, bins)
    pseudo = cfg["evidence"]["dirichlet_pseudocount"]
    pmfs: dict = {}
    rows = []
    for chemistry in ["LMO10", "LFP35"]:
        for grade in ["safe", "unsafe"]:
            # One-symbol within-chemistry law; chemistry is encoded by the
            # disjoint support in disjoint_block_laws.
            pmfs[("nameplate", chemistry, grade)] = np.array([1.0])
            rows.append({
                "menu": "nameplate", "chemistry": chemistry, "grade": grade,
                "category": 0, "count": int((eligible.chemistry.eq(chemistry) & eligible.grade.eq(grade)).sum()),
                "probability": 1.0,
            })
        for menu, feature in FEATURES.items():
            for grade in ["safe", "unsafe"]:
                part = eligible[(eligible.chemistry == chemistry) & (eligible.grade == grade)]
                pmf, counts = categorical_pmf(part[feature].to_numpy(), thresholds[(chemistry, menu)], bins, pseudo)
                pmfs[(menu, chemistry, grade)] = pmf
                for category, (count, probability) in enumerate(zip(counts, pmf, strict=True)):
                    rows.append({
                        "menu": menu, "chemistry": chemistry, "grade": grade,
                        "category": category, "count": int(count), "probability": probability,
                    })
    threshold_json = {
        f"{chemistry}:{menu}": values.tolist()
        for (chemistry, menu), values in thresholds.items()
    }
    return pmfs, pd.DataFrame(rows), threshold_json


def cohort_table(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    unique = df.drop_duplicates(["chemistry", "ID"])
    rows = []
    for chemistry in ["LMO10", "LFP35"]:
        for grade in ["safe", "buffer", "unsafe"]:
            part = unique[(unique.chemistry == chemistry) & (unique.grade == grade)]
            rows.append({
                "chemistry": chemistry,
                "grade": grade,
                "batteries": len(part),
                "soh_min": float(part.SOH.min()) if len(part) else np.nan,
                "soh_median": float(part.SOH.median()) if len(part) else np.nan,
                "soh_max": float(part.SOH.max()) if len(part) else np.nan,
            })
    return pd.DataFrame(rows)


def frontier_table(pmfs: dict, cfg: dict) -> pd.DataFrame:
    alpha, beta = cfg["errors"]["alpha"], cfg["errors"]["beta"]
    rows = []
    for menu in MENUS:
        for n in cfg["n_grid"]:
            safe, unsafe = disjoint_block_laws(pmfs, menu, n)
            delta = convex_hull_tv(safe, unsafe)
            decisiveness = exact_decisiveness(safe, unsafe, alpha, beta)
            bound = min(1.0, alpha + beta + delta)
            rows.append({
                "menu": menu,
                "n": n,
                "states": safe.shape[1],
                "delta": delta,
                "decisiveness": decisiveness,
                "theorem_bound": bound,
                "bound_slack": bound - decisiveness,
                "seconds_per_battery": cfg["physical_cost_seconds_per_battery"][menu],
                "total_seconds": n * cfg["physical_cost_seconds_per_battery"][menu],
                "maximum_c_rate": cfg["maximum_c_rate"][menu],
            })
    return pd.DataFrame(rows)


def delta_one_from_labeled(
    labeled: pd.DataFrame,
    thresholds: dict,
    menu: str,
    bins: int,
    pseudo: float,
) -> float:
    feature = FEATURES[menu]
    pmfs = {}
    for chemistry in ["LMO10", "LFP35"]:
        for grade in ["safe", "unsafe"]:
            part = labeled[(labeled.chemistry == chemistry) & (labeled.grade == grade)]
            pmf, _ = categorical_pmf(part[feature].to_numpy(), thresholds[(chemistry, menu)], bins, pseudo)
            pmfs[(menu, chemistry, grade)] = pmf
    safe, unsafe = disjoint_block_laws(pmfs, menu, 1)
    return convex_hull_tv(safe, unsafe)


def uncertainty(df: pd.DataFrame, cfg: dict) -> tuple[dict, pd.DataFrame]:
    rng = np.random.default_rng(cfg["random_seed"])
    soc = cfg["evidence"]["soc_percent"]
    bins = cfg["evidence"]["quantizer_bins"]
    pseudo = cfg["evidence"]["dirichlet_pseudocount"]
    all_soc = df[df.SOC == soc].copy()
    eligible = all_soc[all_soc.grade != "buffer"].copy()
    thresholds = calibration_thresholds(all_soc, bins)
    observed = delta_one_from_labeled(eligible, thresholds, "pulse_0p5C", bins, pseudo)

    permuted = []
    for _ in range(cfg["permutations"]):
        sample = eligible.copy()
        for chemistry in ["LMO10", "LFP35"]:
            index = sample.index[sample.chemistry == chemistry]
            sample.loc[index, "grade"] = rng.permutation(sample.loc[index, "grade"].to_numpy())
        permuted.append(delta_one_from_labeled(sample, thresholds, "pulse_0p5C", bins, pseudo))
    permuted = np.asarray(permuted)
    permutation_p = float((1 + np.sum(permuted >= observed - 1e-12)) / (1 + len(permuted)))

    bootstrapped = []
    strata = [part for _, part in eligible.groupby(["chemistry", "grade"], sort=True)]
    for _ in range(cfg["bootstrap_replicates"]):
        sample = pd.concat(
            [part.iloc[rng.integers(0, len(part), size=len(part))] for part in strata],
            ignore_index=True,
        )
        bootstrapped.append(delta_one_from_labeled(sample, thresholds, "pulse_0p5C", bins, pseudo))
    bootstrapped = np.asarray(bootstrapped)
    ci = np.quantile(bootstrapped, [0.025, 0.5, 0.975])

    summary = {
        "observed_delta_one": observed,
        "permutations": cfg["permutations"],
        "permutation_null_mean": float(permuted.mean()),
        "permutation_null_q95": float(np.quantile(permuted, 0.95)),
        "permutation_p": permutation_p,
        "bootstrap_replicates": cfg["bootstrap_replicates"],
        "bootstrap_ci95": [float(ci[0]), float(ci[2])],
        "bootstrap_median": float(ci[1]),
    }
    samples = pd.DataFrame({
        "kind": ["permutation"] * len(permuted) + ["bootstrap"] * len(bootstrapped),
        "replicate": list(range(len(permuted))) + list(range(len(bootstrapped))),
        "delta_one": np.r_[permuted, bootstrapped],
    })
    return summary, samples


def sensitivity_tables(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    pseudo = cfg["evidence"]["dirichlet_pseudocount"]
    grade_rows = []
    all5 = df[df.SOC == 5].copy()
    for safe_cut, unsafe_cut in [(0.88, 0.78), (0.90, 0.80), (0.92, 0.82)]:
        labeled = all5.copy()
        labeled["grade"] = np.select(
            [labeled.SOH >= safe_cut, labeled.SOH <= unsafe_cut],
            ["safe", "unsafe"], default="buffer",
        )
        eligible = labeled[labeled.grade != "buffer"]
        for bins in [2, 3, 4, 5, 6]:
            thresholds = calibration_thresholds(all5, bins)
            for menu in ["ocv", "pulse_0p5C"]:
                value = delta_one_from_labeled(eligible, thresholds, menu, bins, pseudo)
                grade_rows.append({
                    "safe_soh": safe_cut, "unsafe_soh": unsafe_cut,
                    "bins": bins, "menu": menu, "delta_one": value,
                })

    soc_rows = []
    for soc in [5, 10, 20, 30, 40, 50]:
        all_soc = df[df.SOC == soc].copy()
        eligible = all_soc[all_soc.grade != "buffer"]
        thresholds = calibration_thresholds(all_soc, 4)
        for menu in ["ocv", "pulse_0p5C"]:
            soc_rows.append({
                "soc": soc,
                "menu": menu,
                "delta_one": delta_one_from_labeled(eligible, thresholds, menu, 4, pseudo),
            })
    return pd.DataFrame(grade_rows), pd.DataFrame(soc_rows)


def evaluate_gates(cohorts: pd.DataFrame, frontier: pd.DataFrame, uncertainty_summary: dict, cfg: dict) -> dict:
    tol = 2e-8
    decisive = cohorts[cohorts.grade.isin(["safe", "unsafe"])]
    g0 = bool((decisive.batteries >= 8).all())
    nameplate = frontier[frontier.menu == "nameplate"]
    target = cfg["errors"]["alpha"] + cfg["errors"]["beta"]
    g1 = bool((nameplate.delta.abs() <= tol).all() and ((nameplate.decisiveness - target).abs() <= tol).all())
    pulse = frontier[frontier.menu == "pulse_0p5C"].sort_values("n")
    g2 = bool(
        float(pulse[pulse.n == 1].delta.iloc[0]) >= 0.40
        and np.all(np.diff(pulse.delta.to_numpy()) >= -tol)
        and float(pulse[pulse.n == 6].decisiveness.iloc[0]) >= 0.95
    )
    g3 = bool((frontier.bound_slack >= -tol).all())
    pivot = frontier.pivot(index="n", columns="menu", values="delta")
    g4 = bool(
        (pivot["pulse_0p5C"] >= pivot["pulse_1C"] - tol).all()
        and (pivot["pulse_0p5C"] >= pivot["pulse_1p5C"] - tol).all()
        and cfg["physical_cost_seconds_per_battery"]["pulse_0p5C"]
        < cfg["physical_cost_seconds_per_battery"]["pulse_1C"]
    )
    g5 = bool(
        uncertainty_summary["permutation_p"] <= 0.01
        and uncertainty_summary["bootstrap_ci95"][0] > 0.25
    )
    gates = {
        "G0_class_support": g0,
        "G1_nameplate_collision": g1,
        "G2_pulse_gate": g2,
        "G3_main_bound": g3,
        "G4_low_stress_dominance": g4,
        "G5_uncertainty": g5,
    }
    return {"overall_pass": bool(all(gates.values())), "gates": gates}


def run() -> dict:
    cfg = load_config()
    df = add_registered_columns(pd.read_csv(DATA))
    cohorts = cohort_table(df, cfg)
    pmfs, pmf_table, thresholds = build_pmfs(df, cfg, cfg["evidence"]["quantizer_bins"])
    frontier = frontier_table(pmfs, cfg)
    uncertainty_summary, uncertainty_samples = uncertainty(df, cfg)
    grade_sensitivity, soc_sensitivity = sensitivity_tables(df, cfg)
    gates = evaluate_gates(cohorts, frontier, uncertainty_summary, cfg)

    RESULTS.mkdir(parents=True, exist_ok=True)
    cohorts.to_csv(RESULTS / "cohorts.csv", index=False, float_format="%.12g")
    pmf_table.to_csv(RESULTS / "pmfs.csv", index=False, float_format="%.12g")
    frontier.to_csv(RESULTS / "frontier.csv", index=False, float_format="%.12g")
    uncertainty_samples.to_csv(RESULTS / "uncertainty_samples.csv", index=False, float_format="%.12g")
    grade_sensitivity.to_csv(RESULTS / "grade_quantizer_sensitivity.csv", index=False, float_format="%.12g")
    soc_sensitivity.to_csv(RESULTS / "soc_sensitivity.csv", index=False, float_format="%.12g")
    (RESULTS / "uncertainty.json").write_text(json.dumps(uncertainty_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (RESULTS / "gates.json").write_text(json.dumps(gates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "protocol_status": cfg["protocol_status"],
        "physical_batteries": int(df.ID.nunique()),
        "rows": int(len(df)),
        "thresholds": thresholds,
        "overall_pass": gates["overall_pass"],
        "software": {
            "python": platform.python_version(), "numpy": np.__version__,
            "pandas": pd.__version__, "scipy": scipy.__version__,
        },
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "cohorts": cohorts, "frontier": frontier, "uncertainty": uncertainty_summary,
        "gates": gates, "summary": summary,
    }

