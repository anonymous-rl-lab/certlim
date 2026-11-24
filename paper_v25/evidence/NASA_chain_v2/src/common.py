from pathlib import Path
import os
from itertools import combinations
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.special import gammaln
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / os.environ.get('NASA_RESULTS', 'results')
OUT.mkdir(parents=True,exist_ok=True)
SEED = 20261124
STEPS = ROOT / 'data/nasa_steps.csv.gz'
POL = {'uniform': [.25,.25,.25,.25], 'skew_high': [.05,.20,.15,.60], 'skew_low': [.25,.60,.10,.05]}
def read_steps():
    return pd.read_csv(STEPS,float_precision='round_trip').sort_values(['cell','stage','step_k']).reset_index(drop=True)
def grade(lo,hi):
    return np.where(hi<=.15+1e-12,'S',np.where(lo>=.35-1e-12,'U','?'))
def states(n,k):
    return np.array([np.diff((-1,)+cut+(n+k-1,))-1 for cut in combinations(range(n+k-1),k-1)])
def lift(p,st):
    p=np.atleast_2d(p)
    coeff=gammaln(st[0].sum()+1)-gammaln(st+1).sum(1)
    lp=np.log(np.maximum(p,1e-300))@st.T+coeff
    a=np.exp(lp)
    if np.any(p<=0): a[((p<=0).astype(int)@st.T)>0]=0
    assert np.max(abs(a.sum(axis=1)-1))<1e-8
    return a
def solve(c,A,b):
    sol=linprog(c,A_ub=A,b_ub=b,bounds=(0,1),method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
    if not sol.success: raise RuntimeError(sol.message)
    return sol.x
def separation(S,U):
    k=S.shape[1]
    A=np.r_[np.c_[-S,np.ones(len(S)),np.zeros(len(S))],np.c_[U,np.zeros(len(U)),-np.ones(len(U))]]
    x=solve(np.r_[np.zeros(k),-1,1],A,np.zeros(len(A)))
    return max(0.,float(x[-2]-x[-1]))
def rule(S,U):
    k=S.shape[1]
    Z=lambda m: sparse.csr_matrix((m,k))
    L=np.vstack([S,U])
    A=sparse.bmat([[U,Z(len(U)),np.zeros((len(U),1))],[Z(len(S)),S,np.zeros((len(S),1))],[-L,-L,np.ones((len(L),1))],[sparse.eye(k),sparse.eye(k),np.zeros((k,1))]],format='csr')
    x=solve(np.r_[np.zeros(2*k),-1],A,np.r_[np.full(len(L),.05),np.zeros(len(L)),np.ones(k)])
    return np.clip(x[:k],0,1),np.clip(x[k:2*k],0,1),float(x[-1])
def write(df,name):
    pd.DataFrame(df).to_csv(OUT/(name+'.csv'),index=False,float_format='%.11g')
def p4(group_mass,t0,t1):
    return np.stack([1-group_mass-t0,t0,group_mass-t1,t1],axis=-1).clip(0,1)
def fixed_design_margin(count,w,M):
    good=count>=5
    return np.sqrt(.5*np.log(2*M/.05)*((w**2)*good/np.maximum(count,1)).sum(axis=-1))
