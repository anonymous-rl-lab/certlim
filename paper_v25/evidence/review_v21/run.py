"""Same-budget retrospective NASA comparisons using interval-product laws."""
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.stats import binom

HERE = Path(__file__).resolve().parent
NASA = HERE.parent / 'NASA_chain_v2'
sys.path.insert(0, str(NASA / "src"))
from common import states, lift, p4
from legacy import h_extremes

OUT = HERE / "results"
BUDGET = .05


def make_banks(df, n):
    """Stationary grid for upper optima; tensor Bernstein hull for feasible rules."""
    st = states(n, 4)
    x = np.linspace(0, 1, n+1)
    b = binom.pmf(np.arange(n+1), n, x[:, None])
    inv = np.linalg.inv(b)
    a, h = np.meshgrid(x, x, indexing="ij")
    def laws(x0, x1):
        t0 = df.lo0.to_numpy()[:, None] + (df.hi0-df.lo0).to_numpy()[:, None]*x0
        t1 = df.lo1.to_numpy()[:, None] + (df.hi1-df.lo1).to_numpy()[:, None]*x1
        return lift(p4(df.qhi.to_numpy()[:, None], t0, t1).reshape(-1, 4), st)
    grid = laws(a.ravel(), h.ravel())
    cube = grid.reshape(len(df), n+1, n+1, len(st))
    control = np.einsum('ia,mabs,jb->mijs', inv, cube, inv, optimize=True).reshape(grid.shape)
    assert control.min() > -1e-9 and np.max(abs(control.sum(1)-1)) < 1e-9
    # Check tensor reconstruction at two non-grid locations, independently of optimization.
    for u, v in ((.213,.731),(.867,.411)):
        w = np.outer(binom.pmf(np.arange(n+1),n,u), binom.pmf(np.arange(n+1),n,v))
        recon = np.einsum('ab,mabs->ms', w, control.reshape(cube.shape))
        assert np.max(abs(recon-laws(u,v))) < 2e-9
    return grid, control, laws(.5,.5).mean(axis=0)


def score_family(method, safe, unsafe):
    k = len(safe)
    if method == "lookup":
        return None, None
    if method in {"LR","OOD"}:
        score = np.log(unsafe.clip(1e-300))-np.log(safe.clip(1e-300)) if method=="LR" else 1-safe
        # Optional score ties have identical action probabilities.
        order = np.argsort(score, kind='stable')
        diff = np.diff(np.eye(k)[order], axis=0)
        monotone = np.block([[diff, np.zeros_like(diff)], [np.zeros_like(diff), -diff]])
        tied = diff[np.abs(np.diff(score[order])) < 1e-12]
        eq = np.block([[tied, np.zeros_like(tied)], [np.zeros_like(tied), tied]]) if len(tied) else None
        return monotone, eq
    def ranks(mass):
        return (mass[None,:]*(mass[None,:] <= mass[:,None]+1e-14)).sum(1)
    ps, pu = ranks(safe), ranks(unsafe)
    cuts = np.unique(np.r_[0., ps, pu, 1.])
    c = (ps[None,:] > cuts[:,None]) & (pu[None,:] <= cuts[:,None])
    r = (pu[None,:] > cuts[:,None]) & (ps[None,:] <= cuts[:,None])
    # Randomized mixtures, including data-independent decisions.
    rules = np.unique(np.vstack([np.c_[c,r],np.zeros(2*k),
                                 np.r_[np.ones(k),np.zeros(k)],np.r_[np.zeros(k),np.ones(k)]]),axis=0)
    return rules, None


def optimize(S,U,method="lookup",mixtures=None):
    """Constraint generation with exhaustive final separation over both banks."""
    k=S.shape[1]
    family, equal = (None,None) if method=="lookup" else score_family(method,*mixtures)
    mix = method=="mass_rank"
    variables = 2*k+1 + (len(family) if mix else 0)
    base = np.zeros((k, variables)); base[:,:k]=np.eye(k); base[:,k:2*k]=np.eye(k)
    rhs0 = np.ones(k)
    eqrows=[]; eqrhs=[]
    if mix:
        e=np.zeros((2*k,variables));e[:,:2*k]=np.eye(2*k);e[:,2*k+1:]=-family.T
        norm=np.zeros(variables);norm[2*k+1:]=1
        eqrows.extend(e);eqrhs.extend(np.zeros(2*k));eqrows.append(norm);eqrhs.append(1.)
    elif family is not None:
        base=np.vstack([base,np.pad(family,((0,0),(0,1)))])
        rhs0=np.r_[rhs0,np.zeros(len(family))]
        if equal is not None:
            eqrows.extend(np.pad(equal,((0,0),(0,1))));eqrhs.extend(np.zeros(len(equal)))
    selected=[{0},{0},{0},{0}]
    objective=np.zeros(variables);objective[2*k]=-1.
    banks=(U,S,S,U)
    for _ in range(300):
        rows=[base];rhs=[rhs0]
        for j,(law,idx) in enumerate(zip(banks, selected)):
            vals=law[sorted(idx)]; A=np.zeros((len(vals),variables))
            if j==0: A[:,:k]=vals
            elif j==1: A[:,k:2*k]=vals
            else: A[:,:k]=-vals;A[:,k:2*k]=-vals;A[:,2*k]=1
            rows.append(A);rhs.append(np.full(len(vals),BUDGET if j<2 else 0.))
        sol=linprog(objective,A_ub=np.vstack(rows),b_ub=np.concatenate(rhs),
                    A_eq=np.array(eqrows) if eqrows else None,b_eq=eqrhs or None,bounds=(0,1),
                    method='highs',options={'primal_feasibility_tolerance':1e-9,'dual_feasibility_tolerance':1e-9})
        if not sol.success: raise RuntimeError(sol.message)
        c,r,t=sol.x[:k],sol.x[k:2*k],sol.x[2*k]
        errors=[U@c-BUDGET,S@r-BUDGET,t-S@(c+r),t-U@(c+r)]
        if max(x.max() for x in errors) < 5e-9:
            return c,r,t
        for x,idx in zip(errors,selected):
            bad=np.flatnonzero(x>2e-9)
            if len(bad):
                idx.update(bad[np.argsort(x[bad])[-6:]].tolist())
    raise RuntimeError('No convergence in constraint generation')


def adjust(c, r, S, U):
    # A small inward margin removes floating-point overshoot of the published lookup.
    shrink = min(1., (BUDGET-5e-11) / max(float((U@c).max()), float((S@r).max()), 1e-15))
    c, r = shrink*c, shrink*r
    return c,r,min((S@(c+r)).min(),(U@(c+r)).min())


def dependence(Sgrid,Sout,Ugrid,Uout,states5):
    # The diagonal block copies one marginal symbol n times.
    pure = [np.flatnonzero(states5[:,i]==5).item() for i in range(4)]
    def bank(law, cap):
        if cap==0: return law
        diagonal = np.zeros_like(law)
        diagonal[:,pure] = law @ (states5/5.)
        return np.vstack([law,(1-cap)*law+cap*diagonal])
    rows=[]
    for cap in (0.,.1,.25,.5,1.):
        S,U=bank(Sout,cap),bank(Uout,cap)
        c,r,_=optimize(S,U)
        c,r,lower=adjust(c,r,S,U)
        _,_,upper=optimize(bank(Sgrid,cap),bank(Ugrid,cap))
        rows.append(dict(rho_max=cap,D_lower=lower,D_upper=upper,err_unsafe=(U@c).max(),err_safe=(S@r).max()))
    return rows


def aggregate_registry(df,source):
    # Stage mixture is part of the estimand; weights are common to risk and evidence.
    pooled=df.groupby(["cell","policy"],as_index=False)[["qhi","lo","hi","lo0","hi0","lo1","hi1"]].mean()
    pooled["grade"]=np.select([pooled.hi<=.15,pooled.lo>=.35],["S","U"],default="?")
    assert len(pooled)==84
    output=[]
    for policy in ("pooled","uniform","skew_high","skew_low"):
        part=pooled if policy=="pooled" else pooled[pooled.policy==policy]
        s,u=[part[part.grade==g] for g in ("S","U")]
        row=dict(source=source,policy=policy,models=len(part),safe=len(s),unsafe=len(u),unresolved=len(part)-len(s)-len(u))
        if len(s) and len(u):
            sg,so,_=make_banks(s,5);ug,uo,_=make_banks(u,5)
            c,r,_=optimize(so,uo);_,_,lo=adjust(c,r,so,uo)
            row.update(D_lower=lo,D_upper=optimize(sg,ug)[2])
        output.append(row)
    return output, pooled.assign(source=source)


def main():
    OUT.mkdir(exist_ok=True)
    summaries=[];rules=[];counts=[];bins=[];stress=[];aggregation=[];cell_rows=[]
    for source,filename in [('missing','legacy_grades'),('confidence','legacy_confidence_sets')]:
        d=pd.read_csv(NASA/'results'/f'{filename}.csv',float_precision='round_trip')
        assert len(d)==1539 and d[['cell','stage']].drop_duplicates().shape[0]==513
        assert d[['cell','policy']].drop_duplicates().shape[0]==84
        agg,cell_table=aggregate_registry(d,source)
        aggregation.extend(agg);cell_rows.append(cell_table)
        for policy in ['pooled','uniform','skew_high','skew_low']:
            sub=d if policy=='pooled' else d[d.policy==policy]
            s,u=[sub[sub.grade==g] for g in ['S','U']]
            counts.append(dict(source=source,policy=policy,safe=len(s),unsafe=len(u),unresolved=len(sub)-len(s)-len(u),
                               cells_safe=s.cell.nunique(),cells_unsafe=u.cell.nunique(),rows=len(sub)))
            if s.empty or u.empty: continue
            for n in (1,5):
                st=states(n,4)
                H=[h_extremes(n,g.lo.min(),g.hi.max()) for g in [s,u]]
                hc,hr,ht=optimize(*H)
                hc,hr,ht=adjust(hc,hr,*H)
                ends=[np.unique(np.r_[g.lo,g.hi]) for g in [s,u]]
                hu=optimize(*[binom.pmf(np.arange(n+1),n,v[:,None]) for v in ends])[2]
                bins.append(dict(source=source,policy=policy,n=n,D_lower=ht,D_upper=hu,
                                 err_unsafe=(H[1]@hc).max(),err_safe=(H[0]@hr).max()))
                Sgrid,Sout,sm=make_banks(s,n)
                Ugrid,Uout,um=make_banks(u,n)
                if source=='confidence' and policy=='pooled' and n==5:
                    stress=dependence(Sgrid,Sout,Ugrid,Uout,st)
                methods=['lookup','LR','OOD','mass_rank'] if source=='confidence' and policy in ['pooled','skew_low'] else ['lookup']
                for method in methods:
                    c,r,t=optimize(Sout,Uout,method,(sm,um))
                    _,_,hi=optimize(Sgrid,Ugrid,method,(sm,um))
                    c,r,low=adjust(c,r,Sout,Uout)
                    a,b=(Uout@c).max(),(Sout@r).max()
                    assert max(a,b)<BUDGET+1e-8 and low<=hi+1e-8
                    summaries.append(dict(source=source,policy=policy,n=n,method=method,D_lower=low,D_upper=hi,
                                          err_unsafe=a,err_safe=b,grid_unsafe=(Ugrid@c).max(),grid_safe=(Sgrid@r).max()))
                    rules.extend(dict(source=source,policy=policy,n=n,method=method,low_no=int(z[0]),low_cut=int(z[1]),
                                      high_no=int(z[2]),high_cut=int(z[3]),certify=cv,reject=rv,alert=1-cv-rv)
                                 for z,cv,rv in zip(st,c,r))
                    print(source,policy,n,method,f'{low:.6f} {hi:.6f}',flush=True)
    whole=pd.read_csv(NASA/'results'/'whole_cell_classes.csv')
    rank_resolution=[]
    for grade in ('S','U'):
        training=len(whole[(whole.split=='train')&(whole.grade==grade)])
        rank_resolution.append(dict(grade=grade,max_calibration_cells=training,p_floor=1/(1+training),
                                    eligible_test_cells=len(whole[(whole.split=='test')&(whole.grade==grade)])))
    for name,rows in [('rank_resolution',rank_resolution),('registration',counts),('cutoff',bins),('comparison',summaries),('lookups',rules),('dependence',stress),('cell_policy_summary',aggregation),('cell_policy_grades',pd.concat(cell_rows))]:
        pd.DataFrame(rows).to_csv(OUT/f'{name}.csv',index=False,float_format='%.13g')


if __name__=='__main__':
    main()
