#!/usr/bin/env python3
"""E3: do conventional methods notice when a channel cannot support the decision?

Every method sees the same registered units, the same grades, and the same three
channels. Each baseline is tuned twice -- once on its own objective and once on
the worst-case objective the frontier rule optimises -- so that the comparison is
not a criterion mismatch dressed up as a result.

The protocol in config/E3_registered.json, including the four predictions, was
hashed before any number below was computed.
"""

from __future__ import annotations

import json
import sys
from itertools import combinations_with_replacement
from math import factorial
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "nasa_randomized_usage_gate" / "data"
CFG = json.loads((ROOT / "config" / "E3_registered.json").read_text())
ALPHA, BETA = CFG["alpha"], CFG["beta"]
K = 4


# ----------------------------------------------------------------- block space
def count_states(n: int, k: int) -> np.ndarray:
    out = []
    for cuts in combinations_with_replacement(range(k), n):
        v = np.zeros(k, dtype=int)
        for c in cuts:
            v[c] += 1
        out.append(v)
    return np.unique(np.array(out), axis=0)


def block_laws(P: np.ndarray, n: int, states: np.ndarray) -> np.ndarray:
    coef = np.array([factorial(n) / np.prod([factorial(int(x)) for x in s]) for s in states])
    out = np.empty((len(P), len(states)))
    for i, p in enumerate(P):
        with np.errstate(divide="ignore"):
            lg = states @ np.log(np.where(p > 0, p, 1.0))
        dead = (states[:, p <= 0].sum(axis=1) > 0) if (p <= 0).any() else np.zeros(len(states), bool)
        row = coef * np.exp(lg)
        row[dead] = 0.0
        out[i] = row / row.sum()
    return out


def hull_tv(S: np.ndarray, U: np.ndarray) -> float:
    ns, k = S.shape
    nu = U.shape[0]
    nw = ns + nu
    rows = []
    for j in range(k):
        for sg in (1.0, -1.0):
            r = np.zeros(nw + k)
            r[:ns] = sg * S[:, j]
            r[ns:nw] = -sg * U[:, j]
            r[nw + j] = -1.0
            rows.append(r)
    aeq = np.zeros((2, nw + k))
    aeq[0, :ns] = 1.0
    aeq[1, ns:nw] = 1.0
    cost = np.concatenate([np.zeros(nw), 0.5 * np.ones(k)])
    res = linprog(cost, A_ub=np.array(rows), b_ub=np.zeros(2 * k), A_eq=aeq,
                  b_eq=np.ones(2), bounds=(0.0, None), method="highs")
    return float(0.5 * np.abs(res.x[:ns] @ S - res.x[ns:nw] @ U).sum())


# ------------------------------------------------------------- the four methods
def frontier_rule(S: np.ndarray, U: np.ndarray):
    """LP-optimal randomised Certify/Alert/Reject: returns (c_x, r_x)."""
    k = S.shape[1]
    nv = 2 * k + 1
    A, b = [], []
    for law in U:
        row = np.zeros(nv); row[:k] = law; A.append(row); b.append(ALPHA)
    for law in S:
        row = np.zeros(nv); row[k:2 * k] = law; A.append(row); b.append(BETA)
    for law in np.vstack([S, U]):
        row = np.zeros(nv); row[:k] = -law; row[k:2 * k] = -law; row[-1] = 1.0
        A.append(row); b.append(0.0)
    for j in range(k):
        row = np.zeros(nv); row[j] = 1.0; row[k + j] = 1.0; A.append(row); b.append(1.0)
    cost = np.zeros(nv); cost[-1] = -1.0
    res = linprog(cost, A_ub=np.array(A), b_ub=np.array(b),
                  bounds=[(0.0, 1.0)] * nv, method="highs")
    x = res.x
    return np.clip(x[:k], 0, 1), np.clip(x[k:2 * k], 0, 1)


def threshold_rule(score: np.ndarray, thr: float):
    """Always-answer rule: Certify where score <= thr, Reject elsewhere."""
    c = (score <= thr).astype(float)
    return c, 1.0 - c


def conformal_rule(S: np.ndarray, U: np.ndarray, eps: float):
    """Split-conformal label set; Alert iff the set is not a singleton.

    Nonconformity of state x for class j is the rank of its class-mixture mass:
    states the class rarely produces are non-conforming. The p-value is the
    class-mixture mass of states at least as non-conforming.
    """
    out = []
    for mix in (S.mean(axis=0), U.mean(axis=0)):
        order = np.argsort(mix)                       # least likely first
        cum = np.empty_like(mix)
        cum[order] = np.cumsum(mix[order])
        out.append(cum)                               # p-value per state
    pS, pU = out
    inS, inU = pS > eps, pU > eps
    c = (inS & ~inU).astype(float)                    # singleton {safe}
    r = (inU & ~inS).astype(float)                    # singleton {unsafe}
    return c, r


def evaluate(c: np.ndarray, r: np.ndarray, S: np.ndarray, U: np.ndarray) -> dict:
    cs, rs = S @ c, S @ r
    cu, ru = U @ c, U @ r
    return {
        "wc_unsafe_certify": float(cu.max()),
        "wc_safe_reject": float(rs.max()),
        "decisiveness": float(min((cs + rs).min(), (cu + ru).min())),
        "balanced_accuracy": float(0.5 * (cs.mean() + ru.mean())),
    }


def tune(make, grid, S, U, objective):
    best, best_val = None, np.inf
    for g in grid:
        m = evaluate(*make(g), S, U)
        val = -m["balanced_accuracy"] if objective == "accuracy" else (
            m["wc_unsafe_certify"] - 1e-6 * m["balanced_accuracy"])
        if val < best_val:
            best, best_val = (g, m), val
    return best


def main() -> None:
    models = pd.read_parquet(DATA / "models.parquet")
    coll = pd.read_parquet(DATA / "collision.parquet")
    adv = pd.read_parquet(ROOT / "results" / "adversarial_laws.parquet")
    for c in ["a0", "a1", "a2", "a3"]:
        adv[c] = adv[c].astype(float)
    tables = {"models": models, "collision": coll, "adversarial": adv}

    rows = []
    for ch in CFG["channels"]:
        df = tables[ch["table"]]
        df = df[df.grade.isin(["S", "U"])]
        P_S = df[df.grade == "S"][ch["cols"]].to_numpy()
        P_U = df[df.grade == "U"][ch["cols"]].to_numpy()
        for n in CFG["block_lengths"]:
            st = count_states(n, K)
            S, U = block_laws(P_S, n, st), block_laws(P_U, n, st)
            delta = hull_tv(S, U)
            print(f"\n=== channel {ch['name']}  n={n}   Delta={delta:.6f} "
                  f"({len(P_S)} safe, {len(P_U)} unsafe models) ===")
            print(f"{'method':<22}{'tuned for':<12}{'wc U->Cert':>12}{'wc S->Rej':>11}"
                  f"{'decisive':>10}{'bal acc':>9}")

            c, r = frontier_rule(S, U)
            m = evaluate(c, r, S, U)
            print(f"{'frontier (alpha=.05)':<22}{'worst case':<12}"
                  f"{m['wc_unsafe_certify']:>12.4f}{m['wc_safe_reject']:>11.4f}"
                  f"{m['decisiveness']:>10.4f}{m['balanced_accuracy']:>9.4f}")
            rows.append({"channel": ch["name"], "n": n, "delta": delta,
                         "method": "frontier", "tuned_for": "worst case", **m})

            lr_score = -(np.log(np.maximum(S.mean(0), 1e-300))
                         - np.log(np.maximum(U.mean(0), 1e-300)))
            ood_score = 0.5 * np.abs(np.eye(len(st)) - S.mean(0)).sum(axis=1)
            makers = {
                "likelihood ratio": (lambda t, s=lr_score: threshold_rule(s, t),
                                     np.quantile(lr_score, np.linspace(0, 1, 201))),
                "OOD distance": (lambda t, s=ood_score: threshold_rule(s, t),
                                 np.quantile(ood_score, np.linspace(0, 1, 201))),
                "conformal selective": (lambda e: conformal_rule(S, U, e),
                                        np.linspace(0.0, 0.5, 201)),
            }
            for name, (make, grid) in makers.items():
                for obj in ("accuracy", "worst case"):
                    g, m = tune(make, grid, S, U, "accuracy" if obj == "accuracy" else "wc")
                    print(f"{name:<22}{obj:<12}{m['wc_unsafe_certify']:>12.4f}"
                          f"{m['wc_safe_reject']:>11.4f}{m['decisiveness']:>10.4f}"
                          f"{m['balanced_accuracy']:>9.4f}")
                    rows.append({"channel": ch["name"], "n": n, "delta": delta,
                                 "method": name, "tuned_for": obj, "param": float(g), **m})

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "results" / "e3_head_to_head.csv", index=False)

    print("\n--- registered predictions ---")
    f = out[out.method == "frontier"]
    p1 = bool((f.wc_unsafe_certify <= ALPHA + 1e-9).all() and (f.wc_safe_reject <= BETA + 1e-9).all())
    fc = f[f.channel == "adversarial"]
    p2 = bool((fc.decisiveness <= ALPHA + BETA + 1e-9).all())
    b = out[(out.method != "frontier") & (out.channel == "adversarial")]
    p3 = bool(((b.balanced_accuracy > 0.6) & (b.wc_unsafe_certify > ALPHA)).any())
    print(f"P1 frontier respects both side errors everywhere : {p1}")
    print(f"P2 frontier decisiveness <= 0.10 on adversarial    : {p2}")
    print(f"P3 a baseline looks accurate yet breaches alpha  : {p3}")
    print(f"P4 all baselines notice instead                  : {not p3}")
    (ROOT / "results" / "e3_predictions.json").write_text(
        json.dumps({"P1": p1, "P2": p2, "P3": p3, "P4": not p3}, indent=2))
    print("\nwritten: results/e3_head_to_head.csv, results/e3_predictions.json")


if __name__ == "__main__":
    sys.exit(main())
