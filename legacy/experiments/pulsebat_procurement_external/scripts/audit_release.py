#!/usr/bin/env python3
"""Independent audit without importing the released analysis package."""

from __future__ import annotations

import json
from functools import lru_cache
from math import exp, lgamma, log
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog


ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=None)
def compositions(n: int, k: int):
    if k == 1:
        return ((n,),)
    return tuple((i,) + r for i in range(n + 1) for r in compositions(n - i, k - 1))


def block(p: np.ndarray, n: int) -> np.ndarray:
    values = []
    for counts in compositions(n, len(p)):
        lp = lgamma(n + 1) - sum(lgamma(c + 1) for c in counts)
        lp += sum(c * log(probability) for c, probability in zip(counts, p, strict=True) if c)
        values.append(exp(lp))
    out = np.asarray(values)
    return out / out.sum()


def hull_tv(safe: np.ndarray, unsafe: np.ndarray) -> float:
    ns, states = safe.shape
    nu = unsafe.shape[0]
    signed = np.c_[safe.T, -unsafe.T]
    objective = np.r_[np.zeros(ns + nu), 0.5 * np.ones(states)]
    aub = np.r_[np.c_[signed, -np.eye(states)], np.c_[-signed, -np.eye(states)]]
    aeq = np.zeros((2, ns + nu + states))
    aeq[0, :ns] = 1
    aeq[1, ns : ns + nu] = 1
    fit = linprog(objective, A_ub=aub, b_ub=np.zeros(2 * states), A_eq=aeq, b_eq=np.ones(2), bounds=(0, None), method="highs")
    if not fit.success:
        raise RuntimeError(fit.message)
    return float(fit.fun)


def three_decision(safe: np.ndarray, unsafe: np.ndarray) -> float:
    states = safe.shape[1]
    rows, rhs = [], []
    for law in np.vstack([safe, unsafe]):
        rows.append(np.r_[-law, -law, 1.0]); rhs.append(0.0)
    for law in unsafe:
        rows.append(np.r_[law, np.zeros(states + 1)]); rhs.append(0.05)
    for law in safe:
        rows.append(np.r_[np.zeros(states), law, 0.0]); rhs.append(0.05)
    for j in range(states):
        row = np.zeros(2 * states + 1); row[j] = row[states + j] = 1
        rows.append(row); rhs.append(1.0)
    fit = linprog(
        np.r_[np.zeros(2 * states), -1.0], A_ub=np.vstack(rows), b_ub=np.asarray(rhs),
        bounds=[(0, 1)] * (2 * states + 1), method="highs",
    )
    if not fit.success:
        raise RuntimeError(fit.message)
    return float(fit.x[-1])


def laws(pmfs: dict, n: int) -> tuple[np.ndarray, np.ndarray]:
    m = len(block(pmfs[("LMO10", "safe")], n))
    safe, unsafe = [], []
    for chemistry, offset in [("LMO10", 0), ("LFP35", m)]:
        for grade, target in [("safe", safe), ("unsafe", unsafe)]:
            padded = np.zeros(2 * m)
            padded[offset : offset + m] = block(pmfs[(chemistry, grade)], n)
            target.append(padded)
    return np.vstack(safe), np.vstack(unsafe)


def main() -> None:
    data = pd.read_csv(ROOT / "data" / "processed" / "observations.csv")
    frontier = pd.read_csv(ROOT / "results" / "frontier.csv")
    data["r05"] = data.U3 - data.U7
    data["grade"] = np.select([data.SOH >= 0.90, data.SOH <= 0.80], ["safe", "unsafe"], default="buffer")
    unique_ok = not data.duplicated(["chemistry", "ID", "SOC"]).any()
    ten_soc_ok = bool((data.groupby(["chemistry", "ID"]).SOC.nunique() == 10).all())
    counts = data.drop_duplicates(["chemistry", "ID"]).groupby(["chemistry", "grade"]).size()
    counts_ok = all(int(counts[key]) == value for key, value in {
        ("LMO10", "safe"): 15, ("LMO10", "buffer"): 50, ("LMO10", "unsafe"): 30,
        ("LFP35", "safe"): 9, ("LFP35", "buffer"): 39, ("LFP35", "unsafe"): 8,
    }.items())

    at5 = data[data.SOC == 5].copy()
    eligible = at5[at5.grade != "buffer"]
    pmfs = {}
    for chemistry in ["LMO10", "LFP35"]:
        thresholds = at5[at5.chemistry == chemistry].r05.quantile([0.25, 0.5, 0.75]).to_numpy()
        for grade in ["safe", "unsafe"]:
            part = eligible[(eligible.chemistry == chemistry) & (eligible.grade == grade)]
            categories = np.digitize(part.r05.to_numpy(), thresholds)
            count = np.bincount(categories, minlength=4).astype(float)
            pmfs[(chemistry, grade)] = (count + 0.5) / (count.sum() + 2.0)

    checks = []
    max_delta_error = max_d_error = 0.0
    for n in [1, 6, 12]:
        safe, unsafe = laws(pmfs, n)
        delta = hull_tv(safe, unsafe)
        decision = three_decision(safe, unsafe)
        row = frontier[(frontier.menu == "pulse_0p5C") & (frontier.n == n)].iloc[0]
        delta_error = abs(delta - row.delta)
        d_error = abs(decision - row.decisiveness)
        max_delta_error = max(max_delta_error, delta_error)
        max_d_error = max(max_d_error, d_error)
        checks.append({"n": n, "delta": delta, "released_delta": row.delta, "D": decision, "released_D": row.decisiveness})

    audit = {
        "pass": bool(unique_ok and ten_soc_ok and counts_ok and max_delta_error <= 1e-9 and max_d_error <= 1e-9),
        "unique_battery_soc_rows": unique_ok,
        "ten_soc_points_per_battery": ten_soc_ok,
        "cohort_counts_match": counts_ok,
        "max_delta_absolute_error": max_delta_error,
        "max_decisiveness_absolute_error": max_d_error,
        "checks": checks,
    }
    (ROOT / "results" / "INDEPENDENT_AUDIT.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, sort_keys=True))
    if not audit["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

