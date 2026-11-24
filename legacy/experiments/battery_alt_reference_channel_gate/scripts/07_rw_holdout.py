#!/usr/bin/env python3
"""Part B, G7: held-out arm validation on NASA Randomised-Walk.

Psi(theta, pi) = sum_z p_ref(z) sum_a pi(a) P(H | theta, z, a).

G7a  ARM TRANSPORT (the registered test).  Estimate Psi(., skew_high) and
     Psi(., skew_low) from cells that only ever ran a uniform policy, and compare
     against cells that actually ran those policies.  Arms are assigned per cell,
     so the comparison is between-cell and is made stage by stage.

G7b  WITHIN-CELL CONTROL.  Same functional, but source and target are two disjoint
     halves of the SAME cell's log.  This carries no transport, only estimation
     error, and bounds how much of any G7a bias is just noise.
"""
import argparse, json, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CFG = json.load(open(os.path.join(ROOT, 'config', 'registered_v02.json')))
HO = CFG['rw_holdout'] if 'rw_holdout' in CFG else json.load(
    open(os.path.join(ROOT, 'config', 'registered.json')))['rw_holdout']
RWCFG = json.load(open(os.path.join(ROOT, 'config', 'rw_registered.json')))
INC, POLD = RWCFG['include'], RWCFG['policies']
POL = {k: np.array(v) for k, v in POLD.items()}
rng = np.random.default_rng(CFG['seed'])

ap = argparse.ArgumentParser(); ap.add_argument('--steps', required=True)
steps = ap.parse_args().steps

df = pd.read_parquet(steps)
df = df[df.temp == 'room'].copy()                      # uniform arms exist at room only
df['A'] = df.I_med.round(0).clip(1, 5).astype(int)
df['H'] = (df.Vend <= 3.25).astype(int)
df = df[(df.A.isin(INC['action_support_A'])) & (df.V0 <= INC['max_V0'])].copy()
df['Z'] = pd.cut(df.V0, INC['state_bin_edges'], labels=[0, 1, 2, 3]).astype(int)
df['family'] = np.where(df.arm.str.startswith('uniform'), 'uniform', df.arm)
UNI = df[df.family == 'uniform']
p_ref = UNI.Z.value_counts(normalize=True).sort_index().reindex(range(4)).fillna(0).values


def psi(sub, w, min_cell=INC['min_steps_per_cell_of_ZA']):
    """Psi = sum_z p_ref(z) sum_a w(a) P(H|z,a); returns (psi, coverage)."""
    ph = np.full((4, 4), np.nan)
    for z in range(4):
        for a in range(1, 5):
            m = (sub.Z == z) & (sub.A == a)
            if m.sum() >= min_cell:
                ph[z, a - 1] = sub.H[m].mean()
    cov = float(np.isfinite(ph).mean())
    val, tot = 0.0, 0.0
    for z in range(4):
        ok = np.isfinite(ph[z])
        if not ok.any():
            continue
        val += p_ref[z] * float(np.sum(w[ok] * ph[z][ok]) / w[ok].sum())
        tot += p_ref[z]
    return (val / tot if tot > 0 else np.nan), cov


# ---------------- per-(cell, stage) Psi under each policy --------------------
rows = []
for (cell, fam, stage), g in df.groupby(['cell', 'family', 'stage']):
    if len(g) < INC['min_steps_per_theta']:
        continue
    d = dict(cell=cell, family=fam, stage=int(stage), n=len(g))
    for pol, w in POL.items():
        v, cov = psi(g, w)
        d[f'psi_{pol}'] = v; d['cov'] = cov
    rows.append(d)
P = pd.DataFrame(rows).dropna(subset=[f'psi_{p}' for p in POL])

# ---------------- G7a: arm transport ----------------------------------------
recs = []
for pol in ('skew_high', 'skew_low'):
    src = P[P.family == 'uniform']
    tgt = P[P.family == pol]
    stages = sorted(set(src.stage) & set(tgt.stage))
    for s in stages:
        a = src[src.stage == s][f'psi_{pol}'].values
        b = tgt[tgt.stage == s][f'psi_{pol}'].values
        if len(a) < 2 or len(b) < 2:
            continue
        recs.append(dict(policy=pol, stage=int(s), n_src=len(a), n_tgt=len(b),
                         pred=float(np.median(a)), real=float(np.median(b)),
                         bias=float(np.median(a) - np.median(b))))
A = pd.DataFrame(recs)
A.to_csv(os.path.join(ROOT, 'results', 'G7a_arm_transport.csv'), index=False)

rho, pval = (spearmanr(A.pred, A.real) if len(A) >= 3 else (np.nan, np.nan))
# bootstrap over stages
bs = []
for _ in range(HO['bootstrap']):
    idx = rng.integers(0, len(A), len(A))
    bs.append(np.median(np.abs(A.bias.values[idx])))
g7a = dict(n_points=int(len(A)), median_abs_bias=float(np.median(np.abs(A.bias))),
           bias_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
           spearman_rho=float(rho), spearman_p=float(pval),
           max_abs_bias=float(np.abs(A.bias).max()),
           criteria=dict(max_abs_bias=HO['max_abs_bias'], min_spearman=HO['min_spearman']),
           passed_bias=bool(np.median(np.abs(A.bias)) <= HO['max_abs_bias']),
           passed_spearman=bool(rho >= HO['min_spearman']))
g7a['passed'] = bool(g7a['passed_bias'] and g7a['passed_spearman'])

# ---------------- G7b: within-cell disjoint-half control ---------------------
recs = []
for (cell, fam, stage), g in df.groupby(['cell', 'family', 'stage']):
    if len(g) < 2 * INC['min_steps_per_theta']:
        continue
    perm = rng.permutation(len(g)); h = len(g) // 2
    g1, g2 = g.iloc[perm[:h]], g.iloc[perm[h:]]
    for pol, w in POL.items():
        v1, c1 = psi(g1, w); v2, c2 = psi(g2, w)
        if not (np.isfinite(v1) and np.isfinite(v2)):
            continue
        recs.append(dict(cell=cell, family=fam, stage=int(stage), policy=pol,
                         pred=float(v1), real=float(v2), bias=float(v1 - v2)))
B = pd.DataFrame(recs)
B.to_csv(os.path.join(ROOT, 'results', 'G7b_within_cell.csv'), index=False)
rb, pb = spearmanr(B.pred, B.real)
g7b = dict(n_points=int(len(B)), median_abs_bias=float(np.median(np.abs(B.bias))),
           spearman_rho=float(rb), spearman_p=float(pb),
           by_policy={p: dict(median_abs_bias=float(np.median(np.abs(gg.bias))),
                              spearman_rho=float(spearmanr(gg.pred, gg.real)[0]))
                      for p, gg in B.groupby('policy')},
           role='control: no transport, estimation error only')

# ---------------- G7c: is the G7a bias policy-specific or an arm level shift? ---
recs = []
for pol in POL:
    for fam in ('skew_high', 'skew_low'):
        src, tgt = P[P.family == 'uniform'], P[P.family == fam]
        for s_ in sorted(set(src.stage) & set(tgt.stage)):
            a = src[src.stage == s_][f'psi_{pol}'].values
            b = tgt[tgt.stage == s_][f'psi_{pol}'].values
            if len(a) < 2 or len(b) < 2:
                continue
            recs.append(dict(evaluated_policy=pol, target_arm=fam, stage=int(s_),
                             bias=float(np.median(a) - np.median(b))))
C = pd.DataFrame(recs)
C.to_csv(os.path.join(ROOT, 'results', 'G7c_policy_vs_arm.csv'), index=False)
g7c = {p_: float(np.median(np.abs(gg.bias))) for p_, gg in C.groupby('evaluated_policy')}
g7c_out = dict(median_abs_bias_by_evaluated_policy=g7c,
               spread=float(max(g7c.values()) - min(g7c.values())),
               reading=('the arms are assigned per cell, so arm and unit are perfectly '
                        'confounded in NASA RW. If the bias is about the same size no matter '
                        'which policy the functional is evaluated at, the gap is an arm/unit '
                        'level shift, not a policy-transport failure.'))

out = dict(G7a_arm_transport=g7a, G7b_within_cell_control=g7b, G7c_policy_vs_arm=g7c_out,
           note='room temperature only; the uniform arms were never run at 40C, so any '
                'cross-arm comparison at 40C would confound policy with temperature.')
json.dump(out, open(os.path.join(ROOT, 'results', 'G7_rw_holdout.json'), 'w'), indent=2)

print("=== G7a 跨臂迁移 (注册判据) ===")
print(A.round(4).to_string(index=False)); print()
print(json.dumps(g7a, indent=2, ensure_ascii=False)); print()
print("=== G7b 同一电芯两半对照 ===")
print(json.dumps(g7b, indent=2, ensure_ascii=False)); print()
print("=== G7c 偏差是策略特异还是臂间水平差 ===")
print(json.dumps(g7c_out, indent=2, ensure_ascii=False))
