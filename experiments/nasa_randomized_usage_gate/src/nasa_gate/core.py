"""Exact hull-TV, exact max-min decisiveness, and multinomial count experiments."""
from __future__ import annotations
import itertools, numpy as np
from scipy.optimize import linprog
from scipy.special import gammaln


def count_states(n: int, K: int) -> np.ndarray:
    """All non-negative integer vectors of length K summing to n."""
    out = []
    def rec(rem, k, cur):
        if k == 1:
            out.append(cur + [rem]); return
        for v in range(rem + 1):
            rec(rem - v, k - 1, cur + [v])
    rec(n, K, [])
    return np.array(out, dtype=int)


def multinomial_pmf(p: np.ndarray, states: np.ndarray, n: int) -> np.ndarray:
    """Probability of each count vector under Multinomial(n, p). Sufficient statistic
    for n iid draws, so hull TV is unchanged by this reduction."""
    p = np.asarray(p, float)
    coef = gammaln(n + 1) - gammaln(states + 1).sum(axis=1)
    pos = p > 0
    # convention 0*log(0) = 0: sum only over positive-probability symbols
    lg = states[:, pos] @ np.log(p[pos])
    # any count on a zero-probability symbol makes the state impossible
    if (~pos).any():
        lg = np.where(states[:, ~pos].sum(axis=1) > 0, -np.inf, lg)
    return np.exp(coef + lg)


def hull_tv(S: np.ndarray, U: np.ndarray) -> float:
    ns, K = S.shape; nu = U.shape[0]; nw = ns + nu
    c = np.concatenate([np.zeros(nw), 0.5 * np.ones(K)])
    rows, cols, vals = [], [], []
    for j in range(K):
        for sgn, off in ((1.0, 2 * j), (-1.0, 2 * j + 1)):
            rows += [off] * nw + [off]
            cols += list(range(nw)) + [nw + j]
            vals += list(sgn * S[:, j]) + list(-sgn * U[:, j]) + [-1.0]
    from scipy.sparse import coo_matrix
    A = coo_matrix((vals, (rows, cols)), shape=(2 * K, nw + K)).tocsr()
    Aeq = np.zeros((2, nw + K)); Aeq[0, :ns] = 1.0; Aeq[1, ns:nw] = 1.0
    r = linprog(c, A_ub=A, b_ub=np.zeros(2 * K), A_eq=Aeq, b_eq=np.ones(2),
                bounds=(0.0, None), method="highs")
    if not r.success:
        raise RuntimeError(r.message)
    return float(0.5 * np.abs(r.x[:ns] @ S - r.x[ns:nw] @ U).sum())


def max_min_decisiveness(S: np.ndarray, U: np.ndarray, alpha: float, beta: float) -> float:
    """Exact sup over randomized three-decision rules of inf_theta P(Gamma != Alert),
    subject to sup_U P(Certify)<=alpha and sup_S P(Reject)<=beta.  LP in (c, r, t)."""
    K = S.shape[1]; NV = 2 * K + 1
    A, b = [], []
    for p in U:
        row = np.zeros(NV); row[:K] = p; A.append(row); b.append(alpha)
    for p in S:
        row = np.zeros(NV); row[K:2 * K] = p; A.append(row); b.append(beta)
    for p in np.vstack([S, U]):
        row = np.zeros(NV); row[:K] = -p; row[K:2 * K] = -p; row[-1] = 1.0
        A.append(row); b.append(0.0)
    for j in range(K):
        row = np.zeros(NV); row[j] = 1.0; row[K + j] = 1.0; A.append(row); b.append(1.0)
    c = np.zeros(NV); c[-1] = -1.0
    r = linprog(c, A_ub=np.array(A), b_ub=np.array(b),
                bounds=[(0.0, 1.0)] * (2 * K) + [(0.0, 1.0)], method="highs")
    if not r.success:
        raise RuntimeError(r.message)
    return float(r.x[-1])


def sion_gap(S: np.ndarray, U: np.ndarray) -> float:
    """max_{0<=f<=1} [ min_S <f,P> - max_U <f,Q> ];  equals hull TV by Sion minimax."""
    K = S.shape[1]
    c = np.concatenate([np.zeros(K), [-1.0, 1.0]]); A = []
    for p in S:
        row = np.zeros(K + 2); row[:K] = -p; row[K] = 1.0; A.append(row)
    for p in U:
        row = np.zeros(K + 2); row[:K] = p; row[K + 1] = -1.0; A.append(row)
    r = linprog(c, A_ub=np.array(A), b_ub=np.zeros(len(A)),
                bounds=[(0.0, 1.0)] * (K + 2), method="highs")
    if not r.success:
        raise RuntimeError(r.message)
    f = r.x[:K]
    return float((S @ f).min() - (U @ f).max())
