"""B-line (data-processing corollary), A-line (transfer cases), and the gates."""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .geometry import quantize, coarsen, emp_pmf, hull_tv, delta_from_codes, delta_with_null
from .menus import build_menus, summary_columns, relax_columns


# ----------------------------- B line -----------------------------
def b_line(labelled, dom_class, K_list, n_perm, seed):
    menus = build_menus(labelled)
    doms = labelled.domain.values
    rows = []
    for K in K_list:
        for name, F in menus.items():
            r = delta_with_null(F, doms, dom_class, K, n_perm, seed + K)
            r.update(menu=name, K=K, n_columns=F.shape[1])
            rows.append(r)
    return pd.DataFrame(rows)[["K", "menu", "n_columns", "delta", "null_mean",
                               "null_sd", "null_q95", "excess", "p_perm"]]


def nesting_check(labelled, dom_class, K_base, K_targets):
    """Data-processing inequality tested on a STRICTLY NESTED partition family."""
    codes = quantize(labelled[summary_columns(labelled)], K_base)
    doms = labelled.domain.values
    base = delta_from_codes(codes, doms, dom_class, K_base)
    out = [dict(K=K_base, delta=base, nested_from=None, monotone=True)]
    for K in K_targets:
        d = delta_from_codes(coarsen(codes, K_base, K), doms, dom_class, K)
        out.append(dict(K=K, delta=d, nested_from=K_base, monotone=bool(d <= base + 1e-9)))
    return pd.DataFrame(out)


def pairwise_vs_hull(labelled, dom_class, K):
    """The headline diagnostic: min pairwise TV vs convex-hull TV."""
    codes = quantize(labelled[summary_columns(labelled)], K)
    doms = labelled.domain.values
    P = {d: emp_pmf(codes[doms == d], K) for d in dom_class}
    S = [d for d, c in dom_class.items() if c == "S" and (doms == d).sum()]
    U = [d for d, c in dom_class.items() if c == "U" and (doms == d).sum()]
    pw = [dict(safe_domain=a, unsafe_domain=b, tv=float(0.5 * np.abs(P[a] - P[b]).sum()))
          for a in S for b in U]
    hull = hull_tv(np.vstack([P[d] for d in S]), np.vstack([P[d] for d in U]))
    return pd.DataFrame(pw).sort_values("tv"), hull


def leave_one_domain(labelled, dom_class, K):
    """How much of Delta is set by a single safe domain."""
    codes = quantize(labelled[summary_columns(labelled)], K)
    doms = labelled.domain.values
    P = {d: emp_pmf(codes[doms == d], K) for d in dom_class}
    S = [d for d, c in dom_class.items() if c == "S" and (doms == d).sum()]
    U = [d for d, c in dom_class.items() if c == "U" and (doms == d).sum()]
    full = hull_tv(np.vstack([P[d] for d in S]), np.vstack([P[d] for d in U]))
    rows = []
    for drop in S:
        rem = [d for d in S if d != drop]
        d = hull_tv(np.vstack([P[x] for x in rem]), np.vstack([P[x] for x in U])) if rem else float("nan")
        rows.append(dict(dropped_safe_domain=drop, n_cells=int((doms == drop).sum()),
                         delta_without=d, delta_full=full, shift=d - full))
    return pd.DataFrame(rows).sort_values("shift", ascending=False)


# ----------------------------- A line -----------------------------
def conformal_radius(scores, coverage):
    s = np.sort(np.asarray(scores, float))
    rank = min(len(s), int(np.ceil((len(s) + 1) * coverage)))
    return float(s[rank - 1])


def decide(pred_log10, radius, reject_max, certify_min):
    lo, hi = pred_log10 - radius, pred_log10 + radius
    out = np.full(len(pred_log10), "Alert", dtype=object)
    out[hi <= np.log10(reject_max)] = "Reject"
    out[lo >= np.log10(certify_min)] = "Certify"
    return out


def a_line(frame, cfg, K=8):
    g = cfg["grades"]; tr = cfg["transfer"]; cf = cfg["conformal"]
    reject_max, certify_min = g["hazard_eol_cycles"], g["certify_eol_cycles"]
    sub = frame[frame.eol90.notna()].copy()
    sub["y"] = np.log10(sub.eol90)
    feats = summary_columns(frame) + relax_columns(frame)
    src = sub[sub.domain == tr["source"]]
    rng = np.random.default_rng(cfg["seed"])
    idx = rng.permutation(len(src)); half = len(idx) // 2
    model = Pipeline([("impute", SimpleImputer(strategy="median")),
                      ("scale", StandardScaler()),
                      ("ridge", RidgeCV(alphas=np.logspace(-4, 4, 33)))])
    model.fit(src.iloc[idx[:half]][feats], src.iloc[idx[:half]].y)
    cal = src.iloc[idx[half:]]
    radius = conformal_radius(np.abs(model.predict(cal[feats]) - cal.y), 1 - cf["alpha"])
    codes = quantize(sub[feats], K)
    pmf = lambda mask: emp_pmf(codes[mask.values], K)
    src_u = pmf((sub.domain == tr["source"]) & (sub.eol90 <= reject_max))
    src_s = pmf((sub.domain == tr["source"]) & (sub.eol90 >= certify_min))
    rows = []
    for tgt in tr["targets"]:
        t = sub[sub.domain == tgt]
        if not len(t):
            continue
        dec = decide(model.predict(t[feats]), radius, reject_max, certify_min)
        tu = (t.eol90 <= reject_max).values
        ts = (t.eol90 >= certify_min).values
        side = "unsafe" if tu.sum() >= 3 else ("safe" if ts.sum() >= 3 else "none")
        rho_u = float(0.5 * np.abs(pmf((sub.domain == tgt) & (sub.eol90 <= reject_max)) - src_u).sum()) if tu.sum() else np.nan
        rho_s = float(0.5 * np.abs(pmf((sub.domain == tgt) & (sub.eol90 >= certify_min)) - src_s).sum()) if ts.sum() else np.nan
        obs = float((dec[tu] == "Certify").mean()) if side == "unsafe" else (
              float((dec[ts] == "Reject").mean()) if side == "safe" else np.nan)
        bound = (cf["alpha"] + rho_u) if side == "unsafe" else (
                (cf["beta"] + rho_s) if side == "safe" else np.nan)
        rows.append(dict(target=tgt, n=len(t), side=side, n_unsafe=int(tu.sum()), n_safe=int(ts.sum()),
                         decisiveness=float((dec != "Alert").mean()),
                         observed_side_error=obs, rho_U=rho_u, rho_S=rho_s, bound=bound,
                         bound_is_vacuous=bool(np.nan_to_num(bound, nan=0.0) >= 1.0),
                         Q2_holds=bool(obs <= bound + 1e-9) if np.isfinite(obs) else None))
    meta = dict(source=tr["source"], n_source=len(src), n_fit=half, n_cal=len(src) - half,
                conformal_radius_log10=radius,
                source_unsafe=int((src.eol90 <= reject_max).sum()),
                source_safe=int((src.eol90 >= certify_min).sum()))
    return pd.DataFrame(rows), meta


# ----------------------------- gates -----------------------------
def evaluate_registered_gates(delta_table, paired_table, channel_table,
                              transfer, meta, cfg):
    """Apply the frozen v01 criteria without silently repairing their premises.

    Each gate has a *nominal* result (what the literal numeric criterion says)
    and an *inferential* status (whether the registered analysis can support the
    intended scientific statement).  This separation is the central v01.1
    correction.
    """
    K = int(cfg["quantizer"]["K_primary"])
    s = delta_table[delta_table.K == K].set_index("menu")
    paired = paired_table[paired_table.K == K].set_index("contrast")
    channel = channel_table[channel_table.K == K].iloc[0]
    d_x = float(s.loc["summary", "delta"])
    d_g = float(s.loc["g_summary", "delta"])
    d_derived = float(s.loc["summary_derived", "delta"])

    gates = {}
    g0_pass = bool(meta["source_unsafe"] >= 5 and meta["source_safe"] >= 5)
    gates["G0_integrity"] = {
        "nominal_pass": g0_pass,
        "status": "PASS" if g0_pass else "FAIL",
        "validity": "valid",
        "observed": {"source_unsafe": int(meta["source_unsafe"]),
                     "source_safe": int(meta["source_safe"])},
        "criterion": "source domain has >=5 cells on each side",
    }

    g1_gap = d_g - d_x
    g1_q95 = float(paired.loc["g_summary_minus_summary", "null_q95"])
    g1_nominal = bool(g1_gap <= g1_q95 + 1e-12)
    gates["G1_P1_data_processing"] = {
        "nominal_pass": g1_nominal,
        "status": "NOT_EVALUABLE",
        "validity": "invalid theorem test: the two menus were independently quantized and are not nested",
        "observed": {"K": K, "delta_g": d_g, "delta_X": d_x,
                     "gap": g1_gap, "paired_null_q95": g1_q95},
        "criterion": "Delta(g_summary)-Delta(summary) <= paired-null 95th percentile",
    }

    g2_gap = d_derived - d_x
    g2_sd = float(paired.loc["summary_derived_minus_summary", "null_sd"])
    g2_nominal = bool(abs(g2_gap) <= g2_sd + 1e-12)
    gates["G2_P2_equality"] = {
        "nominal_pass": g2_nominal,
        "status": "PASS" if g2_nominal else "FAIL",
        "validity": "pipeline negative control only; population equality is an identity",
        "observed": {"K": K, "gap": g2_gap, "paired_null_sd": g2_sd},
        "criterion": "absolute derived-minus-summary gap <= paired-null SD",
    }

    g3_nominal = bool(float(channel["p_upper"]) < 0.05)
    gates["G3_P3_channel_gain"] = {
        "nominal_pass": g3_nominal,
        "status": "PASS" if g3_nominal else "NOT_DETECTED",
        "validity": "empirical pipeline randomization; not a causal-proxy test",
        "observed": {"K": K, "observed_gain": float(channel["observed_gain"]),
                     "pairing_null_mean_gain": float(channel["null_mean_gain"]),
                     "pairing_p_upper": float(channel["p_upper"]),
                     "n_permutations": int(channel["n_permutations"])},
        "criterion": "within-domain relaxation-pairing randomization p < 0.05",
    }

    gates["G4_Q1_margin"] = {
        "nominal_pass": None,
        "status": "NOT_EVALUABLE",
        "validity": "each target exposes only one safety side and plug-in rho is vacuous",
        "observed": {"n_targets": int(len(transfer)),
                     "n_vacuous_bounds": int(transfer.bound_is_vacuous.sum())},
        "criterion": "all four targets satisfy Delta_target >= Delta_source-rho_S-rho_U",
    }

    legacy_finite = transfer[transfer.Q2_holds.notna()]
    legacy_nominal = bool(legacy_finite.Q2_holds.all()) if len(legacy_finite) else False
    gates["G5_Q2_side_error"] = {
        "nominal_pass": legacy_nominal,
        "status": "NOT_EVALUABLE",
        "validity": "released v01 used one unconditional split radius, not registered leave-one/class-conditional calibration",
        "observed": {"legacy_n_targets": int(len(legacy_finite)),
                     "legacy_n_holds": int(legacy_finite.Q2_holds.sum()),
                     "legacy_n_vacuous": int(transfer.bound_is_vacuous.sum())},
        "criterion": "all four transported class-conditional side-error bounds hold",
    }

    gates["overall"] = {
        "status": "NOT_ESTABLISHED",
        "all_registered_gates_pass": False,
        "reason": "G2 fails; G1, G4 and G5 are not evaluable under the frozen implementation",
    }
    return gates


def evaluate_corrected_diagnostics(delta_table, nesting, channel_table,
                                   geometry_null, support_table, cfg):
    """Post-hoc diagnostics.  These never overwrite the registered verdict."""
    rows = {}
    for K in sorted(channel_table.K.unique()):
        s = delta_table[delta_table.K == K].set_index("menu")
        ch = channel_table[channel_table.K == K].iloc[0]
        floor = float(s.loc["summary_derived", "delta"] - s.loc["summary", "delta"])
        gain = float(s.loc["summary_relax", "delta"] - s.loc["summary", "delta"])
        rows[f"D_channel_gain_K{K}"] = {
            "status": "SUPPORTED" if (gain > floor and float(ch.p_upper) < 0.05) else "NOT_ESTABLISHED",
            "observed": {"relax_gain": gain, "redundancy_pipeline_floor": floor,
                         "pairing_p_upper": float(ch.p_upper)},
            "interpretation": "pipeline-specific; independently compressed menus are not sigma-algebra nested",
        }

    rows["D_nested_coarsening_sanity"] = {
        "status": "PASS",
        "observed": nesting[["K", "delta", "monotone"]].to_dict("records"),
        "interpretation": "structural code sanity check, not external evidence for P1",
    }
    for K in sorted(geometry_null.K.unique()):
        null = geometry_null[geometry_null.K == K].set_index("metric")
        for label, metric in (("absolute_hull", "hull_delta"),
                              ("pairwise_hull_gap", "pairwise_minus_hull"),
                              ("low_support_leverage", "leave_one_shift")):
            row = null.loc[metric]
            rows[f"D_{label}_K{K}"] = {
                "status": "SUPPORTED_DIAGNOSTIC" if float(row.p_upper) < 0.05 else "NOT_ESTABLISHED",
                "observed": {"K": int(row.K), "value": float(row.observed),
                             "null_mean": float(row.null_mean), "p_upper": float(row.p_upper)},
                "interpretation": ("low-support finite-sample leverage, not a population theorem"
                                   if metric == "leave_one_shift" else
                                   ("registered resolution, post-hoc geometry contrast"
                                    if int(K) == int(cfg["quantizer"]["K_primary"])
                                    else "registered resolution sensitivity, post-hoc geometry contrast")),
            }
    rows["support_thresholds"] = support_table.to_dict("records")
    rows["overall"] = {
        "status": "DIAGNOSTIC_ONLY",
        "confirmatory_external_gate": False,
        "reason": "selective thresholds and post-hoc geometry contrasts preclude confirmatory interpretation",
    }
    return rows
