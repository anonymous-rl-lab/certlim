#!/usr/bin/env python3
"""Steps -> (theta, pi) models: evidence pmf over K=4 symbols, Psi, grade."""
import json, os, sys
import numpy as np, pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
INC,GR=CFG['include'],CFG['grades']
df=pd.read_parquet(os.path.join(ROOT,'data','steps.parquet'))
df['A']=df.I_med.round(0).clip(1,5).astype(int)
df['H']=(df.Vend<=3.25).astype(int)
df=df[(df.A.isin(INC['action_support_A']))&(df.V0<=INC['max_V0'])].copy()
df['Z']=pd.cut(df.V0,INC['state_bin_edges'],labels=[0,1,2,3]).astype(int)
df['sym']=2*(df.A>=3).astype(int)+df.H          # K=4 evidence symbol
U=df[df.arm.str.startswith('uniform')]
pref=U.Z.value_counts(normalize=True).sort_index().reindex(range(4)).fillna(0).values
POL={k:np.array(v) for k,v in CFG['policies'].items()}
rows=[]
for (cell,arm,temp,stage),g in df.groupby(['cell','arm','temp','stage']):
    if len(g)<INC['min_steps_per_theta']: continue
    # P(H | z, a) and P(sym | z, a) from randomized data -> identified
    ph=np.full((4,4),np.nan); psym=np.full((4,4,4),np.nan)
    for z in range(4):
        for a in range(1,5):
            m=(g.Z==z)&(g.A==a)
            if m.sum()>=INC['min_steps_per_cell_of_ZA']:
                ph[z,a-1]=g.H[m].mean()
                psym[z,a-1]=np.bincount(g.sym[m],minlength=4)/m.sum()
    cov=float(np.isfinite(ph).mean())
    for pol,w in POL.items():
        psi=float(np.nansum([pref[z]*np.nansum(w*ph[z]) for z in range(4)]))
        pe=np.zeros(4)
        for z in range(4):
            for a in range(4):
                if np.isfinite(psym[z,a]).all(): pe+=pref[z]*w[a]*psym[z,a]
        if pe.sum()<=0: continue
        pe=pe/pe.sum()
        rows.append(dict(cell=cell,arm=arm,temp=temp,stage=stage,policy=pol,n_steps=len(g),
                         coverage=cov,psi=psi,**{f'e{i}':float(pe[i]) for i in range(4)}))
M=pd.DataFrame(rows)
M['grade']=np.where(M.psi<=GR['psi_safe_max'],'S',np.where(M.psi>=GR['psi_unsafe_min'],'U','A'))
M.to_parquet(os.path.join(ROOT,'data','models.parquet'))
print(f"模型 (theta,pi) = {len(M)},电芯 {M.cell.nunique()},theta 单元 {M.groupby(['cell','stage']).ngroups}")
print(M.grade.value_counts().to_dict())
print("\n证据分布去重后的唯一点数(小数 3 位):",
      M[[f'e{i}' for i in range(4)]].round(3).drop_duplicates().shape[0])
print("\n按等级的证据分布均值:")
print(M.groupby('grade')[[f'e{i}' for i in range(4)]].mean().round(4).to_string())
