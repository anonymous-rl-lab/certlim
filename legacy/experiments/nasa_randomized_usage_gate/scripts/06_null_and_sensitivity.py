#!/usr/bin/env python3
import json, os, sys
import numpy as np, pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
sys.path.insert(0,os.path.join(ROOT,'src'))
from nasa_gate.core import hull_tv, max_min_decisiveness
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
AL,BE=CFG['test']['alpha'],CFG['test']['beta']
M=pd.read_parquet(os.path.join(ROOT,'data','models.parquet')); E=[f'e{i}' for i in range(4)]
# --- null: permute grade labels in blocks of cells (protocol §5,§6) ---
rng=np.random.default_rng(CFG['seed']); obs=hull_tv(M[M.grade=='S'][E].values,M[M.grade=='U'][E].values)
cells=M.cell.unique(); null=[]
for b in range(200):
    perm=dict(zip(cells,rng.permutation(cells)))
    g=M.assign(cell2=M.cell.map(perm)).sort_values(['cell2','stage','policy'])
    lab=M.grade.values.copy(); rng.shuffle(lab)
    S=M[lab=='S'][E].values; U=M[lab=='U'][E].values
    if len(S) and len(U): null.append(hull_tv(S,U))
null=np.array(null)
print(f"Delta(n=1) 观测 {obs:.4f}  零均值 {null.mean():.4f}  零 q95 {np.quantile(null,.95):.4f}  "
      f"置换 p = {(1+ (null>=obs-1e-12).sum())/(len(null)+1):.4f}")
# --- sensitivity: thresholds and evidence alphabet ---
rows=[]
for ts,tu in [(CFG['grades']['psi_safe_max'],CFG['grades']['psi_unsafe_min'])]+[tuple(x) for x in CFG['grades']['sensitivity']]:
    g=np.where(M.psi<=ts,'S',np.where(M.psi>=tu,'U','A'))
    S=M[g=='S'][E].values; U=M[g=='U'][E].values
    d=hull_tv(S,U); D=max_min_decisiveness(S,U,AL,BE)
    rows.append(dict(kind='threshold',setting=f'({ts},{tu})',n_safe=len(S),n_unsafe=len(U),
                     delta=d,D=D,bound=min(1,AL+BE+d),holds=bool(D<=AL+BE+d+1e-9)))
raw=pd.read_parquet(os.path.join(ROOT,'data','steps.parquet'))
raw['A']=raw.I_med.round(0).clip(1,5).astype(int); raw['H']=(raw.Vend<=3.25).astype(int)
raw=raw[(raw.A<=4)&(raw.V0<=4.0)].copy()
raw['Z']=pd.cut(raw.V0,[0,3.55,3.7,3.85,4.0],labels=[0,1,2,3]).astype(int)
pref=raw[raw.arm.str.startswith('uniform')].Z.value_counts(normalize=True).sort_index().reindex(range(4)).fillna(0).values
for K,symf in [(2,lambda d:d.H.values),(8,lambda d:(4*(d.A>=3).astype(int)+2*(d.Z>=2).astype(int)+d.H).values)]:
    raw['sym']=symf(raw)
    recs=[]
    for (c,a,t,st),g in raw.groupby(['cell','arm','temp','stage']):
        if len(g)<150: continue
        ph=np.full((4,4),np.nan); ps=np.full((4,4,K),np.nan)
        for z in range(4):
            for aa in range(1,5):
                m=(g.Z==z)&(g.A==aa)
                if m.sum()>=5:
                    ph[z,aa-1]=g.H[m].mean(); ps[z,aa-1]=np.bincount(g.sym[m],minlength=K)/m.sum()
        for pol,w in CFG['policies'].items():
            w=np.array(w); psi=float(np.nansum([pref[z]*np.nansum(w*ph[z]) for z in range(4)]))
            pe=np.zeros(K)
            for z in range(4):
                for aa in range(4):
                    if np.isfinite(ps[z,aa]).all(): pe+=pref[z]*w[aa]*ps[z,aa]
            if pe.sum()>0: recs.append((psi,*(pe/pe.sum())))
    Q=pd.DataFrame(recs,columns=['psi']+[f'e{i}' for i in range(K)])
    gg=np.where(Q.psi<=0.15,'S',np.where(Q.psi>=0.35,'U','A'))
    S=Q[gg=='S'].iloc[:,1:].values; U=Q[gg=='U'].iloc[:,1:].values
    d=hull_tv(S,U); D=max_min_decisiveness(S,U,AL,BE)
    rows.append(dict(kind='alphabet',setting=f'K={K}',n_safe=len(S),n_unsafe=len(U),
                     delta=d,D=D,bound=min(1,AL+BE+d),holds=bool(D<=AL+BE+d+1e-9)))
Sv=pd.DataFrame(rows); Sv.to_csv(os.path.join(ROOT,'results','sensitivity.csv'),index=False)
print(Sv.round(4).to_string(index=False))
json.dump(dict(delta_obs=obs,null_mean=float(null.mean()),null_q95=float(np.quantile(null,.95)),
               p_perm=float((1+(null>=obs-1e-12).sum())/(len(null)+1)),n_perm=len(null)),
          open(os.path.join(ROOT,'results','null_calibration.json'),'w'),indent=2)
