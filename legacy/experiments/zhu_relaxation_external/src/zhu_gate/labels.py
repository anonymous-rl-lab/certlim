"""Robust EOL extraction, hazard labelling, and domain-level policy risk."""
from __future__ import annotations
import numpy as np
import pandas as pd


def drop_aborted(cap: pd.Series, window: int, factor: float):
    """Remove interrupted cycles: capacity below `factor` x centred local median."""
    local = cap.rolling(window, center=True, min_periods=3).median()
    bad = cap < factor * local
    return cap[~bad], int(bad.sum())


def first_sustained_crossing(cap: pd.Series, frac: float, k: int):
    """EOL = first cycle at or below frac*c0 that stays there for k valid cycles."""
    c0 = float(np.median(cap.iloc[:5]))
    thr = frac * c0
    v, idx = cap.values, cap.index.values
    for i in range(max(0, len(v) - k + 1)):
        if np.all(v[i:i + k] <= thr):
            return float(idx[i]), c0
    return float("nan"), c0


def hazard_labels(frame: pd.DataFrame, hazard_cycles: int) -> np.ndarray:
    """H=1 early failure; H=0 survived past the hazard horizon; NaN genuinely censored."""
    eol = frame["eol90"]
    survived = (eol > hazard_cycles) | (eol.isna() & (frame["n_cycles"] > hazard_cycles))
    return np.where(eol <= hazard_cycles, 1.0, np.where(survived, 0.0, np.nan))


def domain_classes(frame: pd.DataFrame, hazard_cycles: int, psi_safe_max: float,
                   psi_unsafe_min: float):
    """Psi(domain) = P(H=1 | domain); grade domains into S / U / A(buffer)."""
    H = hazard_labels(frame, hazard_cycles)
    labelled = frame[~np.isnan(H)].copy()
    labelled["H"] = H[~np.isnan(H)]
    psi = labelled.groupby("domain")["H"].agg(["mean", "size"]).rename(columns={"mean": "psi", "size": "n"})
    psi["cls"] = np.where(psi.psi <= psi_safe_max, "S",
                          np.where(psi.psi >= psi_unsafe_min, "U", "A"))
    return labelled, psi
