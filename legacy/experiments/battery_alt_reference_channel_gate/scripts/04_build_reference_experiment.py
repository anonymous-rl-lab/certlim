#!/usr/bin/env python3
"""v02: build the reference-channel experiment.

Grades come from operational hazard rate; evidence comes from the standardised
2.52 A reference discharge.  Writes data/experiment_v02.parquet and
results/freeze_v02.json (grades, cut points, per-pack pmfs).
"""
import json, os, hashlib
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CFG = json.load(open(os.path.join(ROOT, 'config', 'registered_v02.json')))
MINREF = CFG['unit']['min_reference_discharges']
EV = CFG['evidence']

M = pd.read_parquet(os.path.join(ROOT, 'data', 'missions.parquet'))
M['rise'] = M.T_max - M.T_0
REG, REF = M[M.mt == 1].copy(), M[M.mt == 0].copy()

nref = REF.groupby('pack').size()
packs = sorted(nref[nref >= MINREF].index)
REF = REF[REF.pack.isin(packs)].copy()
REG = REG[REG.pack.isin(packs)].copy()

# ---- grades (fixed here, before any Delta / D) -------------------------------
haz = REG.groupby('pack').T_max.apply(lambda s: float((s > 70).mean())).reindex(packs)
q33, q67 = np.percentile(haz.values, [100/3, 200/3])
grade = pd.Series(np.where(haz <= q33, 'S', np.where(haz >= q67, 'U', 'A')), index=packs)

# ---- evidence quantiser (pooled medians over included packs' references) -----
cuts = {f: float(REF[f].median()) for f in ['dur', 'rise', 'V_med']}
b = {f: (REF[f].values >= cuts[f]).astype(int) for f in cuts}
REF['sym8'] = 4 * b['dur'] + 2 * b['rise'] + b['V_med']
REF['sym4'] = REF.sym8 // 2          # drops the V_med bit  (strictly nested)
REF['sym2'] = REF.sym8 // 4          # drops the rise bit   (strictly nested)

rows = []
for p in packs:
    r = REF[REF.pack == p]
    d = dict(pack=p, group=r.group.iloc[0], n_ref=int(len(r)),
             n_regular=int((REG.pack == p).sum()), hazard=float(haz[p]), grade=grade[p])
    for K, col in ((8, 'sym8'), (4, 'sym4'), (2, 'sym2')):
        c = np.bincount(r[col].values, minlength=K).astype(float)
        for i in range(K):
            d[f'c{K}_{i}'] = float(c[i])
    rows.append(d)
T = pd.DataFrame(rows)
T.to_parquet(os.path.join(ROOT, 'data', 'experiment_v02.parquet'))

freeze = dict(
    config_sha256=hashlib.sha256(open(os.path.join(ROOT, 'config', 'registered_v02.json'), 'rb').read()).hexdigest(),
    n_packs=len(packs), packs=packs,
    hazard_tertiles=[float(q33), float(q67)],
    grades=T.grade.value_counts().to_dict(),
    grade_by_pack={p: grade[p] for p in packs},
    hazard_by_pack={p: float(haz[p]) for p in packs},
    quantiser_cuts=cuts,
    n_ref_by_pack={p: int(nref[p]) for p in packs},
    note='grades and quantiser cut points fixed here; no Delta or D has been computed yet')
json.dump(freeze, open(os.path.join(ROOT, 'results', 'freeze_v02.json'), 'w'), indent=2)

print(f"纳入包 {len(packs)} (reference >= {MINREF})")
print(f"hazard 三分位 {q33:.4f} / {q67:.4f} -> 等级 {T.grade.value_counts().to_dict()}")
print(f"量化切点 {json.dumps({k: round(v,4) for k,v in cuts.items()})}")
print()
print(T[['pack', 'group', 'n_ref', 'n_regular', 'hazard', 'grade']].sort_values('hazard').to_string(index=False))
print()
print("等级 x 组:"); print(pd.crosstab(T.group, T.grade).to_string())
print("\nK=8 每包零格数:", T[[f'c8_{i}' for i in range(8)]].eq(0).sum(axis=1).describe()[['min','50%','max']].round(2).to_dict())
