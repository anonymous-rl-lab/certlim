#!/usr/bin/env python3
"""L3: construct a confounded observational channel from the randomized arm and test
whether it creates a cross-grade collision that the randomized channel does not have.

Latent U = step temperature above/below the theta-unit median (treated as unobserved).
Confounded arm: the action distribution depends on U (hot -> heavy load).
True Psi stays identified from the randomized arm."""
import json, os, sys
import numpy as np, pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
sys.path.insert(0,os.path.join(ROOT,'src'))
from nasa_gate.core import hull_tv, max_min_decisiveness
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
INC,GR,POL=CFG['include'],CFG['grades'],CFG['policies']
AL,BE=CFG['test']['alpha'],CFG['test']['beta']
df=pd.read_parquet(os.path.join(ROOT,'data','steps.parquet'))
df['A']=df.I_med.round(0).clip(1,5).astype(int)
df['H']=(df.Vend<=3.25).astype(int)
df=df[(df.A.isin(INC['action_support_A']))&(df.V0<=INC['max_V0'])].copy()
df['Z']=pd.cut(df.V0,INC['state_bin_edges'],labels=[0,1,2,3]).astype(int)
df['sym']=2*(df.A>=3).astype(int)+df.H
pref=df[df.arm.str.startswith('uniform')].Z.value_counts(normalize=True).sort_index().reindex(range(4)).fillna(0).values
# latent U: step temperature relative to the theta-unit median (unobserved by the certifier)
df['U']=(df.groupby(['cell','stage']).Tmax.transform(lambda s: s>s.median())).astype(int)
pi_lo=np.array(POL['skew_low']); pi_hi=np.array(POL['skew_high']); pi_tg=np.array(POL['uniform'])
rows=[]
for (cell,arm,temp,stage),g in df.groupby(['cell','arm','temp','stage']):
    if len(g)<INC['min_steps_per_theta']: continue
    ph=np.full((4,4),np.nan); psym=np.full((4,4,4),np.nan)
    psym_u=np.full((2,4,4,4),np.nan)
    for z in range(4):
        for a in range(1,5):
            m=(g.Z==z)&(g.A==a)
            if m.sum()>=INC['min_steps_per_cell_of_ZA']:
                ph[z,a-1]=g.H[m].mean(); psym[z,a-1]=np.bincount(g.sym[m],minlength=4)/m.sum()
            for u in (0,1):
                mu=m&(g.U==u)
                if mu.sum()>=INC['min_steps_per_cell_of_ZA']:
                    psym_u[u,z,a-1]=np.bincount(g.sym[mu],minlength=4)/mu.sum()
    # true Psi under the frozen target policy, from the randomized arm  -> identified
    psi=float(np.nansum([pref[z]*np.nansum(pi_tg*ph[z]) for z in range(4)]))
    def mix(pol_of_u, table):
        pe=np.zeros(4); tot=0.0
        for u in (0,1):
            for z in range(4):
                for a in range(4):
                    v = table[u,z,a] if table.ndim==4 else table[z,a]
                    if np.isfinite(v).all():
                        w=0.5*pref[z]*pol_of_u(u)[a]; pe+=w*v; tot+=w
        return pe/tot if tot>0 else None
    e_rand = mix(lambda u: pi_tg, psym_u)                       # randomized channel
    e_conf = mix(lambda u: pi_hi if u==1 else pi_lo, psym_u)    # confounded channel
    if e_rand is None or e_conf is None: continue
    rows.append(dict(cell=cell,arm=arm,stage=stage,psi=psi,
        **{f'r{i}':float(e_rand[i]) for i in range(4)},
        **{f'c{i}':float(e_conf[i]) for i in range(4)}))
T=pd.DataFrame(rows)
T['grade']=np.where(T.psi<=GR['psi_safe_max'],'S',np.where(T.psi>=GR['psi_unsafe_min'],'U','A'))
T.to_parquet(os.path.join(ROOT,'data','collision.parquet'))
S=T[T.grade=='S']; U=T[T.grade=='U']
print(f"theta 单元 {len(T)}:安全 {len(S)} 危险 {len(U)} 缓冲 {(T.grade=='A').sum()}")
R=[f'r{i}' for i in range(4)]; C=[f'c{i}' for i in range(4)]
d_rand=hull_tv(S[R].values,U[R].values); d_conf=hull_tv(S[C].values,U[C].values)
D_rand=max_min_decisiveness(S[R].values,U[R].values,AL,BE)
D_conf=max_min_decisiveness(S[C].values,U[C].values,AL,BE)
joint=np.hstack([S[C].values*0.5,S[R].values*0.5]); jointU=np.hstack([U[C].values*0.5,U[R].values*0.5])
d_join=hull_tv(joint,jointU); D_join=max_min_decisiveness(joint,jointU,AL,BE)
res=dict(n_safe=len(S),n_unsafe=len(U),
         delta_randomized=d_rand,D_randomized=D_rand,
         delta_confounded=d_conf,D_confounded=D_conf,
         delta_joint=d_join,D_joint=D_join,
         G5_confounding_creates_collision=bool(d_conf<d_rand),
         G5_exact_collision=bool(d_conf<=1e-6),
         G6_bound_bites=bool(D_conf<=AL+BE+d_conf+1e-9),
         G6_channel_restores=bool(d_join>d_conf and D_join>D_conf))
print(json.dumps(res,indent=2))
json.dump(res,open(os.path.join(ROOT,'results','L3_collision.json'),'w'),indent=2)
