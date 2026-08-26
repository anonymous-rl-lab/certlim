#!/usr/bin/env python3
"""Adversarial confounding: choose ONE U-dependent action policy that MINIMISES the
cross-grade hull separation. If the minimum reaches 0, Theta_sf is non-empty and
constructed; if it is bounded away from 0, no confounding in this family can create a
cross-grade collision on this substrate."""
import json, os, sys
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
sys.path.insert(0,os.path.join(ROOT,'src'))
from nasa_gate.core import hull_tv, max_min_decisiveness
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
INC,GR=CFG['include'],CFG['grades']; AL,BE=CFG['test']['alpha'],CFG['test']['beta']
df=pd.read_parquet(os.path.join(ROOT,'data','steps.parquet'))
df['A']=df.I_med.round(0).clip(1,5).astype(int); df['H']=(df.Vend<=3.25).astype(int)
df=df[(df.A.isin(INC['action_support_A']))&(df.V0<=INC['max_V0'])].copy()
df['Z']=pd.cut(df.V0,INC['state_bin_edges'],labels=[0,1,2,3]).astype(int)
df['sym']=2*(df.A>=3).astype(int)+df.H
pref=df[df.arm.str.startswith('uniform')].Z.value_counts(normalize=True).sort_index().reindex(range(4)).fillna(0).values
df['U']=(df.groupby(['cell','stage']).Tmax.transform(lambda s:s>s.median())).astype(int)
pi_tg=np.array(CFG['policies']['uniform'])
tabs=[]; psis=[]
for (cell,arm,temp,stage),g in df.groupby(['cell','arm','temp','stage']):
    if len(g)<INC['min_steps_per_theta']: continue
    ph=np.full((4,4),np.nan); tb=np.full((2,4,4,4),np.nan)
    for z in range(4):
        for a in range(1,5):
            m=(g.Z==z)&(g.A==a)
            if m.sum()>=INC['min_steps_per_cell_of_ZA']: ph[z,a-1]=g.H[m].mean()
            for u in (0,1):
                mu=m&(g.U==u)
                if mu.sum()>=INC['min_steps_per_cell_of_ZA']: tb[u,z,a-1]=np.bincount(g.sym[mu],minlength=4)/mu.sum()
    psi=float(np.nansum([pref[z]*np.nansum(pi_tg*ph[z]) for z in range(4)]))
    if not np.isfinite(tb).any(): continue
    tabs.append(tb); psis.append(psi)
tabs=np.array(tabs); psis=np.array(psis)
grade=np.where(psis<=GR['psi_safe_max'],'S',np.where(psis>=GR['psi_unsafe_min'],'U','A'))
Si=np.where(grade=='S')[0]; Ui=np.where(grade=='U')[0]
print(f"models: safe {len(Si)} unsafe {len(Ui)}")
W=np.zeros((len(tabs),2,4,4))
for i in range(len(tabs)):
    for u in range(2):
        for z in range(4):
            for a in range(4):
                W[i,u,z,a]=0.5*pref[z] if np.isfinite(tabs[i,u,z,a]).all() else 0.0
Tb=np.nan_to_num(tabs)
def pmfs(pi0,pi1):
    P=np.zeros((len(tabs),4))
    for u,pi in ((0,pi0),(1,pi1)):
        w=W[:,u]*pi[None,None,:]                    # (m,z,a)
        P+=np.einsum('mza,mzak->mk',w,Tb[:,u])
    s=P.sum(axis=1,keepdims=True); s[s<=0]=1
    return P/s
def soft(x): e=np.exp(x-x.max()); return e/e.sum()
def obj(v):
    p0,p1=soft(v[:4]),soft(v[4:])
    P=pmfs(p0,p1)
    return hull_tv(P[Si],P[Ui])
rng=np.random.default_rng(CFG['seed']); best=(np.inf,None)
for t in range(40):
    v0=rng.normal(size=8)*1.5
    r=minimize(obj,v0,method='Nelder-Mead',options=dict(maxiter=900,fatol=1e-9,xatol=1e-6))
    if r.fun<best[0]: best=(float(r.fun),r.x)
    if t%10==9: print(f"  restart {t+1}/40  best Delta so far = {best[0]:.6f}")
p0,p1=soft(best[1][:4]),soft(best[1][4:])
P=pmfs(p0,p1); dmin=hull_tv(P[Si],P[Ui]); Dmin=max_min_decisiveness(P[Si],P[Ui],AL,BE)
Pr=pmfs(pi_tg,pi_tg); dr=hull_tv(Pr[Si],Pr[Ui]); Dr=max_min_decisiveness(Pr[Si],Pr[Ui],AL,BE)
res=dict(delta_randomized=dr,D_randomized=Dr,
         delta_adversarial_min=dmin,D_adversarial=Dmin,
         adversarial_policy_U0=[round(float(x),4) for x in p0],
         adversarial_policy_U1=[round(float(x),4) for x in p1],
         collision_achieved=bool(dmin<=1e-6),
         bound_holds=bool(Dmin<=AL+BE+dmin+1e-9),
         restarts=40)
print(json.dumps(res,indent=2,ensure_ascii=False))
json.dump(res,open(os.path.join(ROOT,'results','L3_adversarial.json'),'w'),indent=2)
