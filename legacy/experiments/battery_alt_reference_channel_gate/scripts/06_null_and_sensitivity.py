#!/usr/bin/env python3
"""v02: permutation null calibration and registered sensitivity sweep."""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
from alt_gate.core import count_states, multinomial_pmf, hull_tv, max_min_decisiveness

CFG = json.load(open(os.path.join(ROOT, 'config', 'registered_v02.json')))
ERR = json.load(open(os.path.join(ROOT, 'config', 'errata_corrections.json')))
TOL0 = ERR['numeric_zero_tolerance']
TST, EV, NC, SN = CFG['test'], CFG['evidence'], CFG['null_calibration'], CFG['sensitivity']
AL, BE = TST['alpha'], TST['beta']
KP = EV['K_primary']
rng = np.random.default_rng(CFG['seed'])

T = pd.read_parquet(os.path.join(ROOT, 'data', 'experiment_v02.parquet'))
NG = TST['n_grid']


def pmf_of(tab, K, delta):
    C = tab[[f'c{K}_{i}' for i in range(K)]].values.astype(float) + delta
    return C / C.sum(axis=1, keepdims=True)


def stats(grades, tab, K=KP, delta=EV['smoothing']['delta_primary'], n_grid=NG):
    P = pmf_of(tab, K, delta)
    S, U = P[grades == 'S'], P[grades == 'U']
    if len(S) == 0 or len(U) == 0:
        return None
    out = {}
    ns = None
    for n in n_grid:
        st = count_states(n, K)
        d = hull_tv(np.vstack([multinomial_pmf(p, st, n) for p in S]),
                    np.vstack([multinomial_pmf(p, st, n) for p in U]))
        out[n] = d
        if ns is None and d > TOL0:
            ns = n
    return dict(Delta_1=out[n_grid[0]], Delta_max_n=out[n_grid[-1]], n_star=ns, curve=out)


# ---------------- permutation null -------------------------------------------
obs = stats(T.grade.values, T)
grp = T.group.values
perm_rows = []
for b in range(NC['grade_permutations']):
    lab = T.grade.values.copy()
    for g in np.unique(grp):                       # block: permute within group
        idx = np.where(grp == g)[0]
        lab[idx] = rng.permutation(lab[idx])
    s = stats(lab, T, n_grid=[1, NG[-1]])
    if s is None:
        continue
    perm_rows.append(dict(b=b, Delta_1=s['Delta_1'], Delta_20=s['Delta_max_n']))
PN = pd.DataFrame(perm_rows)
PN.to_csv(os.path.join(ROOT, 'results', 'null_permutations.csv'), index=False)

null = dict(
    n_permutations=int(len(PN)), block=NC['block'], K=KP,
    observed=dict(Delta_1=obs['Delta_1'], Delta_20=obs['Delta_max_n'], n_star=obs['n_star']),
    null_Delta_1=dict(mean=float(PN.Delta_1.mean()), q05=float(PN.Delta_1.quantile(.05)),
                      median=float(PN.Delta_1.median()), q95=float(PN.Delta_1.quantile(.95)),
                      frac_zero=float((PN.Delta_1 <= TOL0).mean())),
    null_Delta_20=dict(mean=float(PN.Delta_20.mean()), q05=float(PN.Delta_20.quantile(.05)),
                       median=float(PN.Delta_20.median()), q95=float(PN.Delta_20.quantile(.95))),
    p_right_Delta_20=float((PN.Delta_20 >= obs['Delta_max_n'] - 1e-12).mean()),
    p_left_Delta_1=float((PN.Delta_1 <= obs['Delta_1'] + 1e-12).mean()),
    registered_statistic='Delta_E(1) at K_primary',
    supplementary=('Delta_E(20) and n* are reported alongside because the observed Delta_E(1) is '
                   'exactly 0, i.e. at the floor of its range, which makes a right-tailed test on '
                   'it uninformative by construction. Both are reported; neither is substituted '
                   'for the registered statistic.'))
json.dump(null, open(os.path.join(ROOT, 'results', 'null_calibration_v02.json'), 'w'), indent=2)

# ---------------- registered sensitivity sweep --------------------------------
M = pd.read_parquet(os.path.join(ROOT, 'data', 'missions.parquet'))
M['rise'] = M.T_max - M.T_0
REG0, REF0 = M[M.mt == 1], M[M.mt == 0]
nref_all = REF0.groupby('pack').size()
sens = []
for thr in SN['hazard_threshold_degC']:
    for minref in SN['min_reference_discharges']:
        packs = sorted(nref_all[nref_all >= minref].index)
        ref = REF0[REF0.pack.isin(packs)].copy()
        reg = REG0[REG0.pack.isin(packs)]
        haz = reg.groupby('pack').T_max.apply(lambda s: float((s > thr).mean())).reindex(packs)
        q33, q67 = np.percentile(haz.values, [100 / 3, 200 / 3])
        gr = np.where(haz.values <= q33, 'S', np.where(haz.values >= q67, 'U', 'A'))
        cuts = {f: float(ref[f].median()) for f in ['dur', 'rise', 'V_med']}
        sym8 = (4 * (ref.dur.values >= cuts['dur']) + 2 * (ref['rise'].values >= cuts['rise'])
                + (ref.V_med.values >= cuts['V_med'])).astype(int)
        ref = ref.assign(sym8=sym8, sym4=sym8 // 2, sym2=sym8 // 4)
        rows = []
        for p in packs:
            r = ref[ref.pack == p]
            d = dict(pack=p)
            for K, col in ((8, 'sym8'), (4, 'sym4'), (2, 'sym2')):
                c = np.bincount(r[col].values, minlength=K).astype(float)
                for i in range(K):
                    d[f'c{K}_{i}'] = float(c[i])
            rows.append(d)
        tab = pd.DataFrame(rows)
        for delta in SN['smoothing_delta']:
            s = stats(np.array(gr), tab, delta=delta)
            if s is None:
                sens.append(dict(hazard_thr=thr, min_ref=minref, delta=delta, skipped=True)); continue
            # G1 re-check under this setting
            P = pmf_of(tab, KP, delta); Sm, Um = P[gr == 'S'], P[gr == 'U']
            exc = -np.inf
            for n in NG:
                st = count_states(n, KP)
                a = np.vstack([multinomial_pmf(p, st, n) for p in Sm])
                b = np.vstack([multinomial_pmf(p, st, n) for p in Um])
                d = hull_tv(a, b); D = max_min_decisiveness(a, b, AL, BE)
                exc = max(exc, D - min(1.0, AL + BE + d))
            sens.append(dict(hazard_thr=thr, min_ref=minref, delta=delta, skipped=False,
                             n_packs=len(packs), n_S=int((gr == 'S').sum()), n_U=int((gr == 'U').sum()),
                             Delta_1=s['Delta_1'], Delta_20=s['Delta_max_n'], n_star=s['n_star'],
                             G1_max_excess=float(exc)))
SS = pd.DataFrame(sens)
SS.to_csv(os.path.join(ROOT, 'results', 'sensitivity_v02.csv'), index=False)

print("=== 置换零假设 (block = group, %d 次) ===" % len(PN))
print(json.dumps(null, indent=2, ensure_ascii=False))
print()
print("=== 敏感性 ===")
print(SS.round(5).to_string(index=False))
print()
print("G1 在所有敏感性设定下的最大越界:", float(SS[~SS.skipped].G1_max_excess.max()))
print("n* 取值:", sorted(set(SS[~SS.skipped].n_star.dropna().astype(int))),
      " 缺失(未在网格上关门)次数:", int(SS[~SS.skipped].n_star.isna().sum()))
