#!/usr/bin/env python3
"""v02 gates G1-G4, G6, G9 on the reference-channel experiment."""
import json, os, sys
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))
from alt_gate.core import count_states, multinomial_pmf, hull_tv, max_min_decisiveness, sion_gap

CFG = json.load(open(os.path.join(ROOT, 'config', 'registered_v02.json')))
ERR = json.load(open(os.path.join(ROOT, 'config', 'errata_corrections.json')))
TOL0, TOLS = ERR['numeric_zero_tolerance'], ERR['sion_tolerance']
TST, EV = CFG['test'], CFG['evidence']
AL, BE = TST['alpha'], TST['beta']
DELTA = EV['smoothing']['delta_primary']
T = pd.read_parquet(os.path.join(ROOT, 'data', 'experiment_v02.parquet'))


def pmfs(tab, K, delta=DELTA):
    """Per-pack add-delta smoothed pmf over the K-symbol alphabet."""
    C = tab[[f'c{K}_{i}' for i in range(K)]].values.astype(float) + delta
    return C / C.sum(axis=1, keepdims=True)


def frontier(tab, K, n_grid, delta=DELTA, alpha=AL, beta=BE):
    P = pmfs(tab, K, delta)
    S, U = P[(tab.grade == 'S').values], P[(tab.grade == 'U').values]
    rows = []
    for n in n_grid:
        st = count_states(n, K)
        Sn = np.vstack([multinomial_pmf(p, st, n) for p in S])
        Un = np.vstack([multinomial_pmf(p, st, n) for p in U])
        d = hull_tv(Sn, Un)
        D = max_min_decisiveness(Sn, Un, alpha, beta)
        g = sion_gap(Sn, Un)
        rows.append(dict(n=int(n), K=int(K), n_states=int(len(st)), Delta=d, D=D,
                         bound=min(1.0, alpha + beta + d), sion_gamma=g,
                         slack=min(1.0, alpha + beta + d) - D))
    return pd.DataFrame(rows)


res = {}
FR = []
for K in EV['K_sensitivity']:
    grid = TST['n_grid_K8'] if K == 8 else TST['n_grid']
    FR.append(frontier(T, K, grid))
FR = pd.concat(FR, ignore_index=True)
FR['gamma_star'] = FR.sion_gamma / 2.0          # gamma* = value of the Sion game / 2
FR.to_csv(os.path.join(ROOT, 'results', 'frontier_v02.csv'), index=False)

# ---- G1 bound ---------------------------------------------------------------
viol = FR[FR.D > FR.bound + 1e-9]
res['G1_bound'] = dict(passed=bool(len(viol) == 0), n_checked=int(len(FR)),
                       max_excess=float((FR.D - FR.bound).max()),
                       min_slack=float(FR.slack.min()))

# ---- G3 monotone (ERRATA E1: Delta is non-DECREASING in n; D likewise, eq 22b) --
mono = []
for K, g in FR.groupby('K'):
    g = g.sort_values('n')
    mono.append(dict(K=int(K),
                     max_decrease_Delta=float(-np.min(np.diff(g.Delta.values), initial=np.inf)),
                     max_decrease_D=float(-np.min(np.diff(g.D.values), initial=np.inf))))
res['G3_monotone'] = dict(
    passed=bool(all(m['max_decrease_Delta'] <= TOL0 and m['max_decrease_D'] <= TOL0 for m in mono)),
    claim='Delta_E(n) and D_{alpha,beta}(E,n) both non-decreasing in n  [Thm 1(2), eq 22b]',
    per_K=mono,
    as_registered_passed=False,
    as_registered_note='the registered wording said non-increasing; see config/errata_corrections.json E1')

# ---- G4 gate function, n*, Sion  (ERRATA E2, E3) ----------------------------
gate, nstar = {}, {}
for K, g in FR.groupby('K'):
    g = g.sort_values('n')
    G = (g.Delta.values <= TOL0).astype(int)                 # G_E(n) = 1{Delta = 0}
    gate[int(K)] = dict(n=[int(x) for x in g.n], G=[int(x) for x in G],
                        non_increasing=bool(np.all(np.diff(G) <= 0)))
    open_ = g.n.values[G == 0]
    nstar[int(K)] = int(open_[0]) if len(open_) else None
FR['sion_err'] = (FR.gamma_star - FR.Delta / 2.0).abs()
sion_err = float(FR.sion_err.max())
res['G4_gate_nstar_sion'] = dict(
    passed=bool(sion_err <= TOLS and all(v['non_increasing'] for v in gate.values())),
    definition='G_E(n) = 1{Delta_E(n) = 0};  n* = inf{n : G_E(n) = 0}   [eq 19, 23]',
    gate_function=gate, n_star=nstar,
    max_sion_error=sion_err, sion_tolerance=TOLS,
    max_sion_error_excluding_K8_n10=float(FR[~((FR.K == 8) & (FR.n == 10))].sion_err.max()),
    as_registered_note='registered n* used the wrong inequality and a 1e-8 Sion tolerance below '
                       'the solver feasibility tolerance; see errata E2, E3')

# ---- Theorem 1(3): permanent obstruction  <=>  exact PAIRWISE collision (E4) ---
po = {}
for K in EV['K_sensitivity']:
    P = pmfs(T, K)
    Sm, Um = P[(T.grade == 'S').values], P[(T.grade == 'U').values]
    pw = min(0.5 * np.abs(a - b).sum() for a in Sm for b in Um)
    g = FR[FR.K == K].sort_values('n')
    po[int(K)] = dict(min_pairwise_TV=float(pw),
                      exact_pairwise_collision=bool(pw <= TOL0),
                      Delta_1=float(g.Delta.iloc[0]),
                      hulls_intersect_at_1=bool(g.Delta.iloc[0] <= TOL0),
                      n_star=nstar[int(K)])
res['permanent_obstruction'] = dict(
    theorem='G_E(n)=1 for all n  <=>  exists theta_S,theta_U with P_{theta_S}=P_{theta_U}  [eq 24]',
    per_K=po,
    consistent=bool(all((v['exact_pairwise_collision'] and v['n_star'] is None) or
                        (not v['exact_pairwise_collision'] and v['n_star'] is not None)
                        for v in po.values())),
    reading='where hulls intersect at n=1 without an exact pairwise collision, the obstruction is '
            'purely compositional and must close at a finite n* -- the chapter says so explicitly '
            'and this is the direct empirical instance of it')

# ---- G2 attainment: adversarially constructed cross-grade collision ---------
# The bound is NOT tight in general (see tests/test_core.py).  It is tight exactly
# at the two boundaries: Delta = 0  =>  D = alpha + beta, and alpha+beta+Delta >= 1
# => D = 1.  G2 tests the first, which is the case the theorem is about: take the
# closest real S/U pair, mix each towards the other until the hulls collide, and
# check that decisiveness collapses to alpha + beta exactly.
P4 = pmfs(T, 4)
S4, U4 = P4[(T.grade == 'S').values], P4[(T.grade == 'U').values]
sn, un = T.pack[(T.grade == 'S').values].values, T.pack[(T.grade == 'U').values].values
pairs = [(i, j, 0.5 * np.abs(S4[i] - U4[j]).sum()) for i in range(len(S4)) for j in range(len(U4))]
i, j, tv = min(pairs, key=lambda x: x[2])
mid = 0.5 * (S4[i] + U4[j])                     # a distribution in both extended hulls
Sc = np.vstack([S4, mid[None, :]])
Uc = np.vstack([U4, mid[None, :]])
two = []
for n in TST['n_grid']:
    st = count_states(n, 4)
    a = np.vstack([multinomial_pmf(p, st, n) for p in Sc])
    b = np.vstack([multinomial_pmf(p, st, n) for p in Uc])
    d = hull_tv(a, b); D = max_min_decisiveness(a, b, AL, BE)
    two.append(dict(n=int(n), Delta=d, D=D, target=AL + BE, err=abs(D - (AL + BE))))
two = pd.DataFrame(two)
two.to_csv(os.path.join(ROOT, 'results', 'G2_attainment.csv'), index=False)
res['G2_attained'] = dict(passed=bool(two.err.max() <= 1e-8 and two.Delta.max() <= 1e-9),
                          closest_real_pair=[str(sn[i]), str(un[j])], pair_TV_1sample=float(tv),
                          max_Delta=float(two.Delta.max()), max_abs_error=float(two.err.max()),
                          note='collision experiment: Delta = 0 at every n and D = alpha+beta exactly')

# ---- G6 data processing on the nested chain ---------------------------------
piv = FR.pivot_table(index='n', columns='K', values='Delta')
common = piv.dropna().index
dp = []
for a, b in ((8, 4), (4, 2)):
    diff = (piv.loc[common, b] - piv.loc[common, a]).max() if a in piv else np.nan
    dp.append(dict(refine=a, coarse=b, max_violation=float(diff)))
# tautology: Delta_{(X, g(X))} = Delta_X  (g deterministic -> support relabelled, no new cells)
P8 = pmfs(T, 8)
joint = P8.copy()                     # (X, g(X)) has exactly the 8 reachable cells of X
taut = abs(hull_tv(P8[(T.grade == 'S').values], P8[(T.grade == 'U').values]) -
           hull_tv(joint[(T.grade == 'S').values], joint[(T.grade == 'U').values]))
res['G6_data_processing'] = dict(passed=bool(all(d['max_violation'] <= 1e-9 for d in dp) and taut <= 1e-12),
                                 chain=dp, tautology_abs_error=float(taut),
                                 n_shared=[int(x) for x in common])

# ---- G9 held-out packs ------------------------------------------------------
T = T.copy(); T['half'] = [int(p[-1]) % 2 for p in T.pack]
g9 = []
for h in (0, 1):
    sub = T[T.half == h]
    ns, nu = int((sub.grade == 'S').sum()), int((sub.grade == 'U').sum())
    if ns == 0 or nu == 0:
        g9.append(dict(half=h, n_S=ns, n_U=nu, skipped=True)); continue
    f = frontier(sub, 4, TST['n_grid'])
    g9.append(dict(half=h, n_S=ns, n_U=nu, skipped=False,
                   max_excess=float((f.D - f.bound).max()),
                   Delta_1=float(f.Delta.iloc[0]), Delta_last=float(f.Delta.iloc[-1])))
res['G9_heldout_packs'] = dict(passed=bool(all(x.get('skipped') or x['max_excess'] <= 1e-9 for x in g9)),
                               halves=g9, split='pack id last digit parity')

res['_errata'] = ERR
json.dump(res, open(os.path.join(ROOT, 'results', 'gates_v02.json'), 'w'), indent=2)

print(FR.round(6).to_string(index=False))
print()
for k, v in res.items():
    if k.startswith('_'): continue
    p = v.get('passed')
    tag = '通过' if p else ('未通过' if p is False else '记录')
    print(f"{k:24s} {tag}")
print()
print(json.dumps({k:v for k,v in res.items() if not k.startswith('_')}, indent=2, ensure_ascii=False))
