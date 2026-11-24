from __future__ import annotations

from dataclasses import dataclass
from math import ceil, exp, sqrt
from typing import Callable, Hashable, Iterable, Mapping, Sequence

import numpy as np
from scipy.optimize import linprog
from scipy.stats import binom


PMF = dict[tuple[int, ...], float]


@dataclass(frozen=True)
class PrimalLPResult:
    delta: float
    safe_weights: np.ndarray
    unsafe_weights: np.ndarray
    mixed_safe: np.ndarray
    mixed_unsafe: np.ndarray
    objective_residual: float
    normalization_residual: float


@dataclass(frozen=True)
class DualLPResult:
    gap: float
    gamma: float
    statistic: np.ndarray
    safe_floor: float
    unsafe_ceiling: float
    feasibility_residual: float


def _check_open_half(name: str, value: float) -> None:
    if not 0.0 < value < 0.5:
        raise ValueError(f"{name} must lie in (0, 1/2); got {value}")


def latent_flip_probability(q: float) -> float:
    """Return r in (0,1/2) satisfying 2 r (1-r) = q."""

    _check_open_half("q", q)
    return (1.0 - sqrt(1.0 - 2.0 * q)) / 2.0


def direct_observational_pmf(q: float) -> PMF:
    """Exact P(A,H) in the direct world H=A xor E."""

    _check_open_half("q", q)
    out: PMF = {}
    for a in (0, 1):
        for e in (0, 1):
            h = a ^ e
            out[(a, h)] = out.get((a, h), 0.0) + 0.5 * (q if e else 1.0 - q)
    return out


def hidden_observational_pmf(q: float) -> PMF:
    """Exact P(A,H) in the hidden-common-cause world."""

    r = latent_flip_probability(q)
    out: PMF = {}
    for u in (0, 1):
        for e_a in (0, 1):
            for e_h in (0, 1):
                prob = 0.5
                prob *= r if e_a else 1.0 - r
                prob *= r if e_h else 1.0 - r
                key = (u ^ e_a, u ^ e_h)
                out[key] = out.get(key, 0.0) + prob
    return out


def binary_proxy_joint_pmf(model: str, q: float, s: float) -> PMF:
    """Exact P(A,H,W) for the registered binary-proxy construction."""

    _check_open_half("q", q)
    _check_open_half("s", s)
    out: PMF = {}
    if model == "direct":
        for a in (0, 1):
            for e in (0, 1):
                for u0 in (0, 1):
                    for e_w in (0, 1):
                        prob = 0.25
                        prob *= q if e else 1.0 - q
                        prob *= s if e_w else 1.0 - s
                        key = (a, a ^ e, u0 ^ e_w)
                        out[key] = out.get(key, 0.0) + prob
    elif model == "hidden":
        r = latent_flip_probability(q)
        for u in (0, 1):
            for e_a in (0, 1):
                for e_h in (0, 1):
                    for e_w in (0, 1):
                        prob = 0.5
                        prob *= r if e_a else 1.0 - r
                        prob *= r if e_h else 1.0 - r
                        prob *= s if e_w else 1.0 - s
                        key = (u ^ e_a, u ^ e_h, u ^ e_w)
                        out[key] = out.get(key, 0.0) + prob
    else:
        raise ValueError("model must be 'direct' or 'hidden'")
    return out


def total_variation(left: Mapping[Hashable, float], right: Mapping[Hashable, float]) -> float:
    keys = set(left) | set(right)
    return 0.5 * sum(abs(left.get(k, 0.0) - right.get(k, 0.0)) for k in keys)


def expectation(pmf: Mapping[tuple[int, ...], float], fn: Callable[[tuple[int, ...]], float]) -> float:
    return sum(prob * fn(value) for value, prob in pmf.items())


def pushforward_pmf(
    pmf: Mapping[tuple[int, ...], float],
    fn: Callable[[tuple[int, ...]], Hashable],
) -> dict[Hashable, float]:
    out: dict[Hashable, float] = {}
    for value, prob in pmf.items():
        key = fn(value)
        out[key] = out.get(key, 0.0) + prob
    return out


def policy_risk(model: str, q: float, action: int) -> float:
    """Return Psi=P(H=1 | do(A=action)) for the paired SCM."""

    _check_open_half("q", q)
    if action not in (0, 1):
        raise ValueError("action must be 0 or 1")
    if model == "direct":
        return q if action == 0 else 1.0 - q
    if model == "hidden":
        return 0.5
    raise ValueError("model must be 'direct' or 'hidden'")


def grade(risk: float, tau_safe: float, tau_unsafe: float) -> str:
    if not 0.0 <= tau_safe < tau_unsafe <= 1.0:
        raise ValueError("thresholds must satisfy 0 <= tau_safe < tau_unsafe <= 1")
    if risk <= tau_safe:
        return "safe"
    if risk >= tau_unsafe:
        return "unsafe"
    return "ambiguous"


def proxy_delta(q: float, s: float) -> float:
    r = latent_flip_probability(q)
    _check_open_half("s", s)
    return (1.0 - 2.0 * r) * (1.0 - 2.0 * s) / 2.0


def bernoulli_count_pmfs(probabilities: Sequence[float], n: int) -> np.ndarray:
    """Return count distributions; this is a sufficient-state reduction for iid Bernoulli models."""

    if n < 1:
        raise ValueError("n must be positive")
    k = np.arange(n + 1)
    return np.vstack([binom.pmf(k, n, p) for p in probabilities])


def convex_hull_tv_lp(safe_pmfs: np.ndarray, unsafe_pmfs: np.ndarray) -> PrimalLPResult:
    """Solve the finite-class convex-hull total-variation LP."""

    safe = np.asarray(safe_pmfs, dtype=float)
    unsafe = np.asarray(unsafe_pmfs, dtype=float)
    if safe.ndim != 2 or unsafe.ndim != 2 or safe.shape[1] != unsafe.shape[1]:
        raise ValueError("safe_pmfs and unsafe_pmfs must be 2D with the same state count")
    n_safe, n_states = safe.shape
    n_unsafe = unsafe.shape[0]
    n_weights = n_safe + n_unsafe

    objective = np.concatenate([np.zeros(n_weights), 0.5 * np.ones(n_states)])
    inequalities: list[np.ndarray] = []
    for state in range(n_states):
        positive = np.zeros(n_weights + n_states)
        positive[:n_safe] = safe[:, state]
        positive[n_safe:n_weights] = -unsafe[:, state]
        positive[n_weights + state] = -1.0
        inequalities.append(positive)

        negative = np.zeros(n_weights + n_states)
        negative[:n_safe] = -safe[:, state]
        negative[n_safe:n_weights] = unsafe[:, state]
        negative[n_weights + state] = -1.0
        inequalities.append(negative)

    equalities = np.zeros((2, n_weights + n_states))
    equalities[0, :n_safe] = 1.0
    equalities[1, n_safe:n_weights] = 1.0
    result = linprog(
        objective,
        A_ub=np.asarray(inequalities),
        b_ub=np.zeros(2 * n_states),
        A_eq=equalities,
        b_eq=np.ones(2),
        bounds=(0.0, None),
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"primal LP failed: {result.message}")

    safe_weights = result.x[:n_safe]
    unsafe_weights = result.x[n_safe:n_weights]
    mixed_safe = safe_weights @ safe
    mixed_unsafe = unsafe_weights @ unsafe
    recomputed = 0.5 * np.abs(mixed_safe - mixed_unsafe).sum()
    return PrimalLPResult(
        delta=float(recomputed),
        safe_weights=safe_weights,
        unsafe_weights=unsafe_weights,
        mixed_safe=mixed_safe,
        mixed_unsafe=mixed_unsafe,
        objective_residual=float(abs(result.fun - recomputed)),
        normalization_residual=float(
            max(abs(safe_weights.sum() - 1.0), abs(unsafe_weights.sum() - 1.0))
        ),
    )


def dual_separator_lp(safe_pmfs: np.ndarray, unsafe_pmfs: np.ndarray) -> DualLPResult:
    """Compute the Sion/TV optimal statistic 0<=f<=1 and its separation gap."""

    safe = np.asarray(safe_pmfs, dtype=float)
    unsafe = np.asarray(unsafe_pmfs, dtype=float)
    if safe.ndim != 2 or unsafe.ndim != 2 or safe.shape[1] != unsafe.shape[1]:
        raise ValueError("safe_pmfs and unsafe_pmfs must be 2D with the same state count")
    n_states = safe.shape[1]
    # Variables are (f_1,...,f_K,a,b); maximize a-b by minimizing -a+b.
    objective = np.concatenate([np.zeros(n_states), [-1.0, 1.0]])
    inequalities: list[np.ndarray] = []
    for pmf in safe:
        row = np.zeros(n_states + 2)
        row[:n_states] = -pmf
        row[n_states] = 1.0
        inequalities.append(row)  # a <= E_P f
    for pmf in unsafe:
        row = np.zeros(n_states + 2)
        row[:n_states] = pmf
        row[n_states + 1] = -1.0
        inequalities.append(row)  # E_Q f <= b
    bounds = [(0.0, 1.0)] * (n_states + 2)
    result = linprog(
        objective,
        A_ub=np.asarray(inequalities),
        b_ub=np.zeros(len(inequalities)),
        bounds=bounds,
        method="highs",
    )
    if not result.success:
        raise RuntimeError(f"dual LP failed: {result.message}")

    statistic = result.x[:n_states]
    safe_expectations = safe @ statistic
    unsafe_expectations = unsafe @ statistic
    safe_floor = float(safe_expectations.min())
    unsafe_ceiling = float(unsafe_expectations.max())
    gap = safe_floor - unsafe_ceiling
    feasibility = max(
        0.0,
        float(result.x[n_states] - safe_floor),
        float(unsafe_ceiling - result.x[n_states + 1]),
    )
    return DualLPResult(
        gap=float(gap),
        gamma=float(gap / 2.0),
        statistic=statistic,
        safe_floor=safe_floor,
        unsafe_ceiling=unsafe_ceiling,
        feasibility_residual=float(feasibility),
    )


def finite_block_frontier(
    safe_probabilities: Sequence[float],
    unsafe_probabilities: Sequence[float],
    n_values: Iterable[int],
    dual_n_max: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for n in n_values:
        safe = bernoulli_count_pmfs(safe_probabilities, n)
        unsafe = bernoulli_count_pmfs(unsafe_probabilities, n)
        primal = convex_hull_tv_lp(safe, unsafe)
        row: dict[str, object] = {
            "n": n,
            "delta": primal.delta,
            "gate_open": bool(primal.delta <= 1e-12),
            "safe_weights": ";".join(f"{x:.16g}" for x in primal.safe_weights),
            "unsafe_weights": ";".join(f"{x:.16g}" for x in primal.unsafe_weights),
            "primal_objective_residual": primal.objective_residual,
            "normalization_residual": primal.normalization_residual,
            "dual_gap": np.nan,
            "gamma": np.nan,
            "primal_dual_residual": np.nan,
            "dual_feasibility_residual": np.nan,
            "dual_statistic": "",
        }
        if n <= dual_n_max:
            dual = dual_separator_lp(safe, unsafe)
            row.update(
                {
                    "dual_gap": dual.gap,
                    "gamma": dual.gamma,
                    "primal_dual_residual": abs(primal.delta - dual.gap),
                    "dual_feasibility_residual": dual.feasibility_residual,
                    "dual_statistic": ";".join(f"{x:.16g}" for x in dual.statistic),
                }
            )
        rows.append(row)
    return rows


def proxy_rule_exact_errors(q: float, s: float, n: int) -> dict[str, float | int]:
    """Exact errors for thresholding the mean of T=1{A=W}."""

    if n < 1:
        raise ValueError("n must be positive")
    delta = proxy_delta(q, s)
    threshold = 0.5 + delta / 2.0
    critical_count = int(ceil(n * threshold))
    direct_error = float(binom.sf(critical_count - 1, n, 0.5))
    hidden_error = float(binom.cdf(critical_count - 1, n, 0.5 + delta))
    bound = float(exp(-n * delta * delta / 2.0))
    return {
        "n": n,
        "delta": delta,
        "threshold": threshold,
        "critical_count": critical_count,
        "direct_error_exact": direct_error,
        "hidden_error_exact": hidden_error,
        "hoeffding_bound": bound,
    }
