"""Frozen evidence menus.

Every derived column is deterministic once the pooled sample is fixed.  Rank
and qcut operations are nevertheless pooled, data-adaptive transformations;
v01.1 therefore calls them label-blind/transductive rather than population-
fixed maps.  See PROTOCOL_ERRATA items 2 and 12.

`summary_derived` is built to have the SAME column count as `summary_relax`
(8 + 34 both) so that "add 34 information-free columns" is a dimension-matched
null for "add 34 relaxation columns".
"""
from __future__ import annotations
import pandas as pd

PRODUCT_PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3), (4, 5), (4, 6), (5, 7), (6, 7)]


def summary_columns(frame) -> list[str]:
    return [c for c in frame.columns if c.startswith("sm_")]


def relax_columns(frame) -> list[str]:
    return [c for c in frame.columns if c.startswith("rx")]


def derived_block(X: pd.DataFrame) -> pd.DataFrame:
    """34 deterministic functions of X in the released pooled-data pipeline."""
    cols = list(X.columns)
    g = X.apply(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False), axis=0).add_prefix("g_")
    sq = X ** 2; sq.columns = [f"sq_{c}" for c in cols]
    rk = X.rank(axis=0); rk.columns = [f"rk_{c}" for c in cols]
    pr = pd.DataFrame({f"pr_{i}{j}": X[cols[i]].values * X[cols[j]].values
                       for i, j in PRODUCT_PAIRS}, index=X.index)
    return pd.concat([g, sq, rk, pr], axis=1)


def build_menus(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    sm, rx = summary_columns(frame), relax_columns(frame)
    X = frame[sm].copy()
    W = frame[rx].copy()
    D = derived_block(X)
    menus = {
        "summary": X,
        "g_summary": D[[c for c in D.columns if c.startswith("g_")]],
        "summary_derived": pd.concat([X, D], axis=1),
        "relax": W,
        "summary_relax": pd.concat([X, W], axis=1),
    }
    if menus["summary_derived"].shape[1] != menus["summary_relax"].shape[1]:
        raise AssertionError("dimension-matched null broken: derived and relax menus differ in width")
    return menus
