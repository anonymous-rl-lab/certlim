"""Verify released lookups with directly constructed Bernstein coefficient laws."""
import os
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[key]='1'
from functools import lru_cache
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import binom, hypergeom

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'NASA_chain_v2'/'results'


@lru_cache(maxsize=None)
def weight(n, high, m, selected):
    return hypergeom.pmf(selected,n,high,m)


def conditional_coefficients(n,m,low,high):
    """A random subset of m slots meets r high endpoints among n slots."""
    out=np.zeros((len(low),n+1,m+1))
    for r in range(m+1):
        low_p=binom.pmf(np.arange(m-r+1),m-r,low[:,None])
        high_p=binom.pmf(np.arange(r+1),r,high[:,None])
        hits=np.zeros((len(low),m+1))
        for a in range(r+1):
            hits[:,a:a+m-r+1]+=high_p[:,a,None]*low_p
        for i in range(n+1):
            out[:,i,:]+=weight(n,i,m,r)*hits
    return out


def audit(n,stage,lookups):
    lookup=lookups
    assert len(lookup) and lookup[["certify","reject","alert"]].min().min()>=-2e-11
    assert np.allclose(lookup.certify+lookup.reject+lookup.alert,1,rtol=0,atol=3e-12)
    q=stage.qhi.to_numpy()
    accum=np.zeros((len(stage),n+1,n+1,2))
    for m in range(n+1):
        low=conditional_coefficients(n,m,stage.lo0.to_numpy()/(1-q),np.clip(stage.hi0.to_numpy()/(1-q),0,1))
        high=conditional_coefficients(n,n-m,stage.lo1.to_numpy()/q,np.clip(stage.hi1.to_numpy()/q,0,1))
        rates=np.empty((m+1,n-m+1,2))
        for a in range(m+1):
            for b in range(n-m+1):
                row=lookup[(lookup.low_no==m-a)&(lookup.low_cut==a)&(lookup.high_no==n-m-b)&(lookup.high_cut==b)]
                assert len(row)==1
                rates[a,b]=row[['certify','reject']].to_numpy()[0]
        conditional=np.einsum('mia,mjb,abk->mijk',low,high,rates,optimize=True)
        accum+=binom.pmf(m,n,1-q)[:,None,None,None]*conditional
    S=stage.grade.to_numpy()=='S';U=~S
    return accum[U,:,:,0].max(),accum[S,:,:,1].max(),accum.sum(axis=3).min()


def main():
    reports=pd.read_csv(ROOT/'results/comparison.csv')
    rules=pd.read_csv(ROOT/'results/lookups.csv')
    assert len(reports)==24
    sources={k:pd.read_csv(SOURCE/(f+'.csv')).query('grade in ["S","U"]')
             for k,f in [('missing','legacy_grades'),('confidence','legacy_confidence_sets')]}
    for row in reports.itertuples():
        df=sources[row.source]
        if row.policy!='pooled': df=df[df.policy==row.policy]
        pr=rules[(rules.source==row.source)&(rules.policy==row.policy)&(rules.n==row.n)&(rules.method==row.method)]
        a,b,low=audit(row.n,df,pr)
        assert max(a,b) <= .05+2e-12, (row,a,b)
        assert np.max(abs(np.array([a,b,low])-[row.err_unsafe,row.err_safe,row.D_lower]))<5e-10
        assert -5e-9 <= row.D_upper-low < 1e-7
    dependence=pd.read_csv(ROOT/'results/dependence.csv')
    assert np.all(np.diff(dependence.D_lower)<0)
    single=reports.query('source=="confidence" and policy=="pooled" and method=="lookup" and n==1').iloc[0]
    assert abs(dependence.D_lower.iloc[-1]-single.D_lower)<1e-8
    print('PASS: 24 fitted rule families and 720 lookup rows independently verified using hypergeometric coefficients; both side errors and minimum decisiveness reproduced.')


if __name__=='__main__':
    main()
