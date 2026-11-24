"""Finite-alphabet block laws and exact certification linear programs."""

from __future__ import annotations

from functools import lru_cache
from math import exp, lgamma, log

import numpy as np
from scipy.optimize import linprog


@lru_cache(maxsize=None)
def count_vectors(n: int, k: int) -> tuple[tuple[int, ...], ...]:
    if k == 1:
        return ((n,),)
    return tuple((first,) + rest for first in range(n + 1) for rest in count_vectors(n - first, k - 1))


def multinomial_law(p: np.ndarray, n: int) -> np.ndarray:
    p = np.asarray(p, dtype=float)
    values = []
    for counts in count_vectors(n, len(p)):
        lp = lgamma(n + 1) - sum(lgamma(c + 1) for c in counts)
        impossible = False
        for count, probability in zip(counts, p, strict=True):
            if count and probability == 0:
                impossible = True
                break
            if count:
                lp += count * log(probability)
        values.append(0.0 if impossible else exp(lp))
    out = np.asarray(values)
    return out / out.sum()


def convex_hull_tv(safe: np.ndarray, unsafe: np.ndarray) -> float:
    safe = np.asarray(safe, dtype=float)
    unsafe = np.asarray(unsafe, dtype=float)
    ns, states = safe.shape
    nu = unsafe.shape[0]
    signed = np.c_[safe.T, -unsafe.T]
    objective = np.r_[np.zeros(ns + nu), 0.5 * np.ones(states)]
    aub = np.vstack([np.c_[signed, -np.eye(states)], np.c_[-signed, -np.eye(states)]])
    aeq = np.zeros((2, ns + nu + states))
    aeq[0, :ns] = 1
    aeq[1, ns : ns + nu] = 1
    fit = linprog(
        objective,
        A_ub=aub,
        b_ub=np.zeros(2 * states),
        A_eq=aeq,
        b_eq=np.ones(2),
        bounds=(0, None),
        method="highs",
    )
    if not fit.success:
        raise RuntimeError(fit.message)
    return 0.0 if abs(fit.fun) < 1e-10 else float(fit.fun)


def exact_decisiveness(safe: np.ndarray, unsafe: np.ndarray, alpha: float, beta: float) -> float:
    safe = np.asarray(safe, dtype=float)
    unsafe = np.asarray(unsafe, dtype=float)
    states = safe.shape[1]
    objective = np.r_[np.zeros(2 * states), -1.0]
    rows, rhs = [], []
    for law in np.vstack([safe, unsafe]):
        rows.append(np.r_[-law, -law, 1.0])
        rhs.append(0.0)
    for law in unsafe:
        rows.append(np.r_[law, np.zeros(states + 1)])
        rhs.append(alpha)
    for law in safe:
        rows.append(np.r_[np.zeros(states), law, 0.0])
        rhs.append(beta)
    for j in range(states):
        row = np.zeros(2 * states + 1)
        row[j] = row[states + j] = 1.0
        rows.append(row)
        rhs.append(1.0)
    fit = linprog(
        objective,
        A_ub=np.vstack(rows),
        b_ub=np.asarray(rhs),
        bounds=[(0, 1)] * (2 * states + 1),
        method="highs",
    )
    if not fit.success:
        raise RuntimeError(fit.message)
    return float(fit.x[-1])


def disjoint_block_laws(pmfs: dict, menu: str, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Block laws on a disjoint union of chemistry-specific count spaces."""
    example = pmfs[(menu, "LMO10", "safe")]
    block_size = len(multinomial_law(example, n))
    safe, unsafe = [], []
    for chemistry, offset in [("LMO10", 0), ("LFP35", block_size)]:
        for grade, target in [("safe", safe), ("unsafe", unsafe)]:
            law = multinomial_law(pmfs[(menu, chemistry, grade)], n)
            padded = np.zeros(2 * block_size)
            padded[offset : offset + block_size] = law
            target.append(padded)
    return np.vstack(safe), np.vstack(unsafe)

