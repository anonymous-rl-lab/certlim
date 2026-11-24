#!/usr/bin/env python3
"""Missions -> (theta, pi) models: evidence pmf, Psi, grade. Also fixes the thresholds."""
import json, os, sys
import numpy as np, pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
MS,HZ,EV=CFG['mission'],CFG['hazard'],CFG['evidence']
BINS=CFG['action_bins_A']; POL={k:np.array(v) for k,v in CFG['policies'].items()}
M=pd.read_parquet(os.path.join(ROOT,'data','missions.parquet'))
M['A']=pd.cut(M.I,BINS,labels=False)                      # 0..4
M['H']=(M.T_max>70).astype(int)
M['sym']=2*(M.A>=3).astype(int)+M.H                        # K=4
R=M[(M.mt==1)&M.A.notna()].copy(); R['A']=R.A.astype(int)
pref=None
rows=[]
for (pack,grp,stage),g in R.groupby(['pack','group','stage']):
    if len(g)<MS['min_missions_per_theta']: continue
    ph=np.full(5,np.nan); psym=np.full((5,4),np.nan)
    for a in range(5):
        m=g.A==a
        if m.sum()>=5:
            ph[a]=g.H[m].mean(); psym[a]=np.bincount(g.sym[m],minlength=4)/m.sum()
    cov=float(np.isfinite(ph).mean())
    for pol,w in POL.items():
        mask=np.isfinite(ph)
        if not mask.any(): continue
        psi=float(np.sum(w[mask]*ph[mask])/w[mask].sum())    # renormalise over covered bins
        pe=np.zeros(4); tot=0.0
        for a in range(5):
            if np.isfinite(psym[a]).all(): pe+=w[a]*psym[a]; tot+=w[a]
        if tot<=0: continue
        pe/=tot
        rows.append(dict(pack=pack,group=grp,stage=int(stage),policy=pol,n_missions=len(g),
                         coverage=cov,psi=psi,**{f'e{i}':float(pe[i]) for i in range(4)}))
T=pd.DataFrame(rows)
q=np.percentile(T.psi,[33,67])
tS,tU=round(float(q[0]),2),round(float(q[1]),2)
T['grade']=np.where(T.psi<=tS,'S',np.where(T.psi>=tU,'U','A'))
T.to_parquet(os.path.join(ROOT,'data','models.parquet'))
json.dump(dict(psi_tertiles=[float(q[0]),float(q[1])],tau_safe=tS,tau_unsafe=tU,
               n_models=len(T),grades=T.grade.value_counts().to_dict(),
               note='thresholds set from pooled Psi tertiles before any Delta/D computation'),
          open(os.path.join(ROOT,'results','thresholds.json'),'w'),indent=2)
print(f"(theta,pi) 模型 {len(T)}  theta 单元 {T.groupby(['pack','stage']).ngroups}  包 {T.pack.nunique()}")
print(f"Psi 三分位 {np.round(q,4)} -> tau=({tS},{tU});等级 {T.grade.value_counts().to_dict()}")
print("\nPsi 按策略:"); print(T.groupby('policy').psi.describe(percentiles=[.25,.5,.75]).round(3).to_string())
print("\n等级 x 组:"); print(pd.crosstab(T.group,T.grade).to_string())
print("格覆盖率中位:",round(float(T.coverage.median()),3))
