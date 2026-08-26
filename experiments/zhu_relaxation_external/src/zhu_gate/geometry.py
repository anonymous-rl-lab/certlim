"""Quantization, convex-hull TV (LP), and permutation null calibration.

The pooled rank/quantile map is label- and domain-blind, but data-adaptive and
transductive.  It is not represented as a population-fixed Markov kernel.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import linprog


def quantize(F: pd.DataFrame, K: int) -> np.ndarray:
    """Rank each column over the pooled sample, sum ranks along a fixed all-ones
    direction, then bin into K equal-frequency cells.

    The direction is fixed a priori (no fitting). Bin edges come from the pooled
    sample and are applied identically to every cell, so the map is
    label-independent and domain-independent.
    """
    if K < 2:
        raise ValueError("K must be >= 2")
    R = F.rank(axis=0, method="average").values
    s = R.sum(axis=1)
    edges = np.quantile(s, np.linspace(0.0, 1.0, K + 1)[1:-1])
    return np.searchsorted(edges, s, side="right").astype(int)


def coarsen(codes: np.ndarray, K_from: int, K_to: int) -> np.ndarray:
    """Strictly nested coarsening of an existing partition (K_from -> K_to)."""
    if K_from % K_to:
        raise ValueError("K_to must divide K_from for a nested coarsening")
    return codes // (K_from // K_to)


def emp_pmf(codes: np.ndarray, K: int) -> np.ndarray:
    c = np.bincount(codes, minlength=K).astype(float)
    return c / c.sum() if c.sum() else c


def hull_tv(S: np.ndarray, U: np.ndarray) -> float:
    """inf TV between conv(S) and conv(U); exact LP on the probability simplex."""
    S = np.atleast_2d(np.asarray(S, float))
    U = np.atleast_2d(np.asarray(U, float))
    if S.shape[1] != U.shape[1]:
        raise ValueError("S and U must share the alphabet size")
    ns, K = S.shape
    nu = U.shape[0]
    nw = ns + nu
    c = np.concatenate([np.zeros(nw), 0.5 * np.ones(K)])
    A = []
    for j in range(K):
        r1 = np.zeros(nw + K); r1[:ns] = S[:, j]; r1[ns:nw] = -U[:, j]; r1[nw + j] = -1.0
        r2 = np.zeros(nw + K); r2[:ns] = -S[:, j]; r2[ns:nw] = U[:, j]; r2[nw + j] = -1.0
        A += [r1, r2]
    Aeq = np.zeros((2, nw + K)); Aeq[0, :ns] = 1.0; Aeq[1, ns:nw] = 1.0
    r = linprog(c, A_ub=np.array(A), b_ub=np.zeros(2 * K), A_eq=Aeq, b_eq=np.ones(2),
                bounds=(0.0, None), method="highs")
    if not r.success:
        raise RuntimeError(f"hull LP failed: {r.message}")
    return float(0.5 * np.abs(r.x[:ns] @ S - r.x[ns:nw] @ U).sum())


def delta_from_codes(codes, domains, dom_class, K) -> float:
    """theta = domain; P_theta = empirical evidence pmf over that domain's cells."""
    S = [emp_pmf(codes[domains == d], K) for d, c in dom_class.items()
         if c == "S" and (domains == d).sum()]
    U = [emp_pmf(codes[domains == d], K) for d, c in dom_class.items()
         if c == "U" and (domains == d).sum()]
    if not S or not U:
        return float("nan")
    return hull_tv(np.vstack(S), np.vstack(U))


def delta_with_null(F, domains, dom_class, K, n_perm, seed):
    """Delta plus its permutation noise floor.

    Null: shuffle the evidence rows across cells, keeping domain sizes and class
    structure fixed. This destroys any evidence<->grade association while leaving
    every other aspect of the geometry untouched.
    """
    rng = np.random.default_rng(seed)
    codes = quantize(F, K)
    obs = delta_from_codes(codes, domains, dom_class, K)
    null = np.array([delta_from_codes(codes[rng.permutation(len(codes))], domains, dom_class, K)
                     for _ in range(n_perm)])
    return {
        "delta": obs,
        "null_mean": float(np.nanmean(null)),
        "null_sd": float(np.nanstd(null, ddof=1)),
        "null_q95": float(np.nanquantile(null, 0.95)),
        "excess": float(obs - np.nanmean(null)),
        "p_perm": float((1 + int(np.sum(null >= obs - 1e-12))) / (n_perm + 1)),
    }


def paired_delta_difference(F_new, F_base, domains, dom_class, K, n_perm, seed):
    """Paired null for a menu difference.

    A single row permutation is applied to both menu code vectors at every
    repetition.  This preserves the paired design promised in the frozen
    protocol; using two independently generated null distributions would not.
    """
    rng = np.random.default_rng(seed)
    new_codes = quantize(F_new, K)
    base_codes = quantize(F_base, K)
    observed = (delta_from_codes(new_codes, domains, dom_class, K)
                - delta_from_codes(base_codes, domains, dom_class, K))
    null = np.empty(n_perm, dtype=float)
    for b in range(n_perm):
        order = rng.permutation(len(domains))
        null[b] = (delta_from_codes(new_codes[order], domains, dom_class, K)
                   - delta_from_codes(base_codes[order], domains, dom_class, K))
    return {
        "observed_gap": float(observed),
        "null_mean": float(np.nanmean(null)),
        "null_sd": float(np.nanstd(null, ddof=1)),
        "null_q05": float(np.nanquantile(null, 0.05)),
        "null_q95": float(np.nanquantile(null, 0.95)),
        "p_upper": float((1 + int(np.sum(null >= observed - 1e-12))) / (n_perm + 1)),
        "p_two_sided": float(min(1.0, 2 * min(
            (1 + int(np.sum(null >= observed - 1e-12))) / (n_perm + 1),
            (1 + int(np.sum(null <= observed + 1e-12))) / (n_perm + 1),
        ))),
        "n_permutations": int(n_perm),
    }


def _within_domain_permutation(values, domains, rng):
    """Return a row-permuted copy, shuffling only inside each domain."""
    values = np.asarray(values)
    out = values.copy()
    domains = np.asarray(domains)
    for domain in np.unique(domains):
        idx = np.flatnonzero(domains == domain)
        out[idx] = values[rng.permutation(idx)]
    return out


def channel_pairing_permutation(X, W, domains, dom_class, K, n_perm, seed):
    """Registered W-within-domain pairing randomization.

    The domain marginal of the relaxation channel is preserved.  Only its
    cell-level pairing with the summary channel is destroyed.  The statistic
    is Delta(X,W)-Delta(X), so the baseline cancels exactly in the randomization
    distribution.
    """
    X = pd.DataFrame(X).reset_index(drop=True)
    W = pd.DataFrame(W).reset_index(drop=True)
    domains = np.asarray(domains)
    base = delta_from_codes(quantize(X, K), domains, dom_class, K)
    observed_joint = delta_from_codes(quantize(pd.concat([X, W], axis=1), K),
                                      domains, dom_class, K)
    observed_gain = observed_joint - base
    rng = np.random.default_rng(seed)
    rows = []
    Wv = W.to_numpy()
    for b in range(n_perm):
        Wp = _within_domain_permutation(Wv, domains, rng)
        joint = pd.concat([X, pd.DataFrame(Wp, columns=W.columns)], axis=1)
        perm_delta = delta_from_codes(quantize(joint, K), domains, dom_class, K)
        rows.append({
            "K": int(K),
            "repetition": int(b),
            "baseline_delta": float(base),
            "observed_joint_delta": float(observed_joint),
            "observed_gain": float(observed_gain),
            "permuted_joint_delta": float(perm_delta),
            "permuted_gain": float(perm_delta - base),
        })
    table = pd.DataFrame(rows)
    null = table["permuted_gain"].to_numpy()
    summary = {
        "K": int(K),
        "baseline_delta": float(base),
        "observed_joint_delta": float(observed_joint),
        "observed_gain": float(observed_gain),
        "null_mean_gain": float(np.mean(null)),
        "null_sd_gain": float(np.std(null, ddof=1)),
        "null_q95_gain": float(np.quantile(null, 0.95)),
        "p_upper": float((1 + int(np.sum(null >= observed_gain - 1e-12))) / (n_perm + 1)),
        "n_permutations": int(n_perm),
    }
    return table, summary


def geometry_metrics(codes, domains, dom_class, K):
    """Convex-hull and pairwise geometry for one empirical alphabet."""
    domains = np.asarray(domains)
    eligible = [d for d, cls in dom_class.items()
                if cls in {"S", "U"} and np.any(domains == d)]
    pmfs = {d: emp_pmf(np.asarray(codes)[domains == d], K) for d in eligible}
    safe = [d for d in eligible if dom_class[d] == "S"]
    unsafe = [d for d in eligible if dom_class[d] == "U"]
    if not safe or not unsafe:
        return {"hull_delta": float("nan"), "min_pairwise_tv": float("nan"),
                "pairwise_minus_hull": float("nan")}
    hull = hull_tv(np.vstack([pmfs[d] for d in safe]),
                   np.vstack([pmfs[d] for d in unsafe]))
    pairwise = min(0.5 * np.abs(pmfs[a] - pmfs[b]).sum()
                   for a in safe for b in unsafe)
    return {
        "hull_delta": float(hull),
        "min_pairwise_tv": float(pairwise),
        "pairwise_minus_hull": float(pairwise - hull),
    }


def geometry_permutation_diagnostics(F, domains, dom_class, K, drop_domain,
                                     n_perm, seed):
    """Post-hoc calibration for the two headline geometry diagnostics."""
    codes = quantize(F, K)
    domains = np.asarray(domains)
    observed = geometry_metrics(codes, domains, dom_class, K)
    reduced_class = {d: c for d, c in dom_class.items() if d != drop_domain}
    observed_reduced = geometry_metrics(codes, domains, reduced_class, K)
    observed["leave_one_shift"] = (observed_reduced["hull_delta"]
                                    - observed["hull_delta"])
    rng = np.random.default_rng(seed)
    rows = []
    for b in range(n_perm):
        permuted = codes[rng.permutation(len(codes))]
        metrics = geometry_metrics(permuted, domains, dom_class, K)
        reduced = geometry_metrics(permuted, domains, reduced_class, K)
        metrics["leave_one_shift"] = reduced["hull_delta"] - metrics["hull_delta"]
        metrics.update(repetition=int(b), K=int(K), dropped_domain=drop_domain)
        rows.append(metrics)
    table = pd.DataFrame(rows)
    summary = []
    for metric in ("hull_delta", "min_pairwise_tv", "pairwise_minus_hull", "leave_one_shift"):
        null = table[metric].to_numpy()
        value = observed[metric]
        summary.append({
            "K": int(K),
            "metric": metric,
            "observed": float(value),
            "null_mean": float(np.nanmean(null)),
            "null_sd": float(np.nanstd(null, ddof=1)),
            "null_q95": float(np.nanquantile(null, 0.95)),
            "p_upper": float((1 + int(np.sum(null >= value - 1e-12))) / (n_perm + 1)),
            "n_permutations": int(n_perm),
            "dropped_domain": drop_domain if metric == "leave_one_shift" else "",
        })
    return table, pd.DataFrame(summary)


def support_sensitivity(F, domains, dom_class, K, minimum_sizes):
    """Recompute the geometry after imposing domain-support thresholds."""
    codes = quantize(F, K)
    domains = np.asarray(domains)
    rows = []
    for threshold in minimum_sizes:
        keep = {d: c for d, c in dom_class.items()
                if int(np.sum(domains == d)) >= threshold}
        metrics = geometry_metrics(codes, domains, keep, K)
        rows.append({
            "K": int(K),
            "minimum_domain_n": int(threshold),
            "n_safe_domains": int(sum(c == "S" for c in keep.values())),
            "n_unsafe_domains": int(sum(c == "U" for c in keep.values())),
            **metrics,
        })
    return pd.DataFrame(rows)


def low_support_bootstrap(F, domains, dom_class, K, drop_domain,
                          n_bootstrap, seed):
    """Conditional cell bootstrap for the low-support leave-one diagnostic.

    The pooled quantizer is held fixed.  The interval therefore describes
    empirical-PMF uncertainty conditional on the registered partition, not
    population uncertainty in the learned partition itself.
    """
    codes = quantize(F, K)
    domains = np.asarray(domains)
    eligible = [d for d, c in dom_class.items()
                if c in {"S", "U"} and np.any(domains == d)]
    safe = [d for d in eligible if dom_class[d] == "S"]
    unsafe = [d for d in eligible if dom_class[d] == "U"]
    rng = np.random.default_rng(seed)
    rows = []
    for b in range(n_bootstrap):
        pmfs = {}
        for domain in eligible:
            values = codes[domains == domain]
            sample = rng.choice(values, size=len(values), replace=True)
            pmfs[domain] = emp_pmf(sample, K)
        full = hull_tv(np.vstack([pmfs[d] for d in safe]),
                       np.vstack([pmfs[d] for d in unsafe]))
        safe_reduced = [d for d in safe if d != drop_domain]
        reduced = hull_tv(np.vstack([pmfs[d] for d in safe_reduced]),
                          np.vstack([pmfs[d] for d in unsafe]))
        rows.append({"repetition": int(b), "K": int(K),
                     "delta_full": float(full), "delta_without": float(reduced),
                     "leave_one_shift": float(reduced - full)})
    table = pd.DataFrame(rows)
    summary = {
        "K": int(K),
        "dropped_domain": drop_domain,
        "n_bootstrap": int(n_bootstrap),
        "conditioning": "pooled quantizer held fixed",
        "delta_full_q025": float(table.delta_full.quantile(0.025)),
        "delta_full_median": float(table.delta_full.median()),
        "delta_full_q975": float(table.delta_full.quantile(0.975)),
        "shift_q025": float(table.leave_one_shift.quantile(0.025)),
        "shift_median": float(table.leave_one_shift.median()),
        "shift_q975": float(table.leave_one_shift.quantile(0.975)),
    }
    return table, summary
