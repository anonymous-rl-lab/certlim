#!/usr/bin/env python3
"""L1: D(n) <= alpha+beta+Delta(n).  L2: monotonicity, n*, Sion identity."""
import json, os, sys, time
import numpy as np, pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
sys.path.insert(0,os.path.join(ROOT,'src'))
from nasa_gate.core import count_states, multinomial_pmf, hull_tv, max_min_decisiveness, sion_gap
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
AL=CFG['test']['alpha']; BE=CFG['test']['beta']
M=pd.read_parquet(os.path.join(ROOT,'data','models.parquet'))
E=[f'e{i}' for i in range(4)]
PS=M[M.grade=='S'][E].values; PU=M[M.grade=='U'][E].values
print(f"safe models {len(PS)}  unsafe models {len(PU)}")
rows=[]
MAXN=int(os.environ.get('MAX_N','20'))   # protocol deviation: grid truncated for compute (ERRATA 1)
for n in [x for x in CFG['test']['n_grid'] if x<=MAXN]:
    t0=time.time(); st=count_states(n,4)
    S=np.vstack([multinomial_pmf(p,st,n) for p in PS])
    U=np.vstack([multinomial_pmf(p,st,n) for p in PU])
    d=hull_tv(S,U); g=sion_gap(S,U); D=max_min_decisiveness(S,U,AL,BE)
    bound=min(1.0,AL+BE+d)
    rows.append(dict(n=n,n_states=len(st),delta=d,sion_gap=g,sion_residual=abs(d-g),
                     gamma=g/2,D=D,bound=bound,slack=bound-D,G1=bool(D<=bound+1e-9),
                     secs=time.time()-t0))
    print(f"  n={n:3d} states={len(st):5d}  Delta={d:.6f}  D={D:.6f}  bound={bound:.6f}  "
          f"slack={bound-D:+.2e}  G1={'OK' if D<=bound+1e-9 else 'VIOLATION'}  [{time.time()-t0:.1f}s]")
R=pd.DataFrame(rows)
R[['n','secs']].to_csv(os.path.join(ROOT,'results','runtime.csv'),index=False)   # wall clock, excluded from MANIFEST
R=R.drop(columns=['secs'])
mono=bool((R.delta.diff().dropna()>=-1e-9).all())
nz=R[R.delta<=1e-9]; nstar=int(R[R.delta>1e-9].n.min()) if (R.delta>1e-9).any() else None
atzero=R[R.delta<=1e-9]
G2=bool(np.allclose(atzero.D,AL+BE,atol=1e-6)) if len(atzero) else None
print(f"\nG1 全部满足: {bool(R.G1.all())}")
print(f"G2 Delta=0 处 D == alpha+beta: {G2}  (观测 D={atzero.D.tolist()})")
print(f"G3 Delta(n) 单调不减: {mono}")
print(f"G4 n* = {nstar};  Sion 恒等式最大残差 = {R.sion_residual.max():.2e}")
json.dump(dict(max_n_run=MAXN,G1_bound=bool(R.G1.all()),G2_attained=G2,G3_monotone=mono,
               n_star=nstar,sion_max_residual=float(R.sion_residual.max())),
          open(os.path.join(ROOT,'results','L1_L2_gates.json'),'w'),indent=2)
