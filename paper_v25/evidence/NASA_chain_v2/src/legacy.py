from common import *
from scipy.stats import binom
from itertools import product

def build(s):
    s=s.copy()
    s['A']=s.I_med.round().clip(1,5).astype(int)
    s=s[(s.A<=4)&(s.V0<=4)].copy()
    s['H']=(s.Vend<=3.25).astype(int)
    s['Z']=np.digitize(s.V0,[3.55,3.7,3.85],right=True)
    pref=s[s.arm.str.startswith('uniform')].Z.value_counts(normalize=True).sort_index().to_numpy()
    out=[]
    for (cell,arm,temp,stage),g in s.groupby(['cell','arm','temp','stage']):
        if len(g)<150: continue
        a=(4*g.Z+g.A-1).to_numpy()
        N=np.bincount(a,minlength=16)
        H=np.bincount(a,weights=g.H,minlength=16)
        good=N>=5
        for pol,weights in POL.items():
            w=np.outer(pref,weights).ravel()
            t=(w*good*H/np.maximum(N,1)).reshape(4,4)
            m=(w*~good).reshape(4,4)
            l0=t[:,:2].sum();l1=t[:,2:].sum()
            lo=t.sum();hi=lo+m.sum()
            out.append(dict(cell=cell,arm=arm,temp=temp,stage=stage,policy=pol,steps=len(g),qhi=sum(weights[2:]),lo0=l0,hi0=l0+m[:,:2].sum(),lo1=l1,hi1=l1+m[:,2:].sum(),lo=lo,hi=hi,active=good.sum(),v19=grade(lo,lo).item(),grade=grade(lo,hi).item(),margin=fixed_design_margin(N,w,1539)))
    f=pd.DataFrame(out)
    f['grade_working95']=grade(f.lo-f.margin,f.hi+f.margin)
    write(f,'legacy_grades')
    assert (len(f),(f.grade=='S').sum(),(f.grade=='U').sum())==(1539,443,528)
    return f
def banks(g,coords):
    return np.vstack([p4(g.qhi.to_numpy(),(g.lo0+a*(g.hi0-g.lo0)).to_numpy(),(g.lo1+b*(g.hi1-g.lo1)).to_numpy()) for a,b in coords])
def permutation(f):
    parts=[]; rng=np.random.default_rng(SEED)
    for _,sub in f.groupby(['arm','temp']):
        ds=[v.sort_values(['stage','policy']) for _,v in sub.groupby('cell')]
        stages=sorted(set.intersection(*(set(v.stage) for v in ds)))
        ds=[v[v.stage.isin(stages)] for v in ds]
        parts.append((np.stack([banks(v,[(.5,.5)]) for v in ds]),np.stack([v.grade.to_numpy() for v in ds])))
    law=np.vstack([v.reshape(-1,4) for v,_ in parts])
    res=[]
    for i in range(501):
        gr=np.concatenate([g[(rng.permutation(4) if i else np.arange(4))].ravel() for _,g in parts])
        res.append(separation(law[gr=='S'],law[gr=='U']))
    write([dict(permutation=i,delta=d) for i,d in enumerate(res)],'legacy_block_permutation')
    write([dict(n_cells=28, common_model_rows=len(law),replicates=500,observed=res[0],p=(1+sum(np.array(res[1:])>=res[0]-1e-10))/501)],'legacy_block_test')
def h_extremes(n,lo,hi):
    # Bernstein coefficients of a binomial block under every p in [lo,hi].
    return np.array([np.convolve(binom.pmf(np.arange(k+1),k,hi),binom.pmf(np.arange(n-k+1),n-k,lo)) for k in range(n+1)])
def front(f):
    g=f[f.grade!='?']
    ss,uu=[g[g.grade==j] for j in ['S','U']]
    maxs=ss.hi.max();minu=uu.lo.min()
    old=pd.read_csv(ROOT/'data/v19_frontier.csv')
    rows=[]
    for n in old.n.astype(int):
        st=states(n,2)
        # Inner feasible hull and conservative outer hull for H-only, based on the two extreme ranges.
        ends=[np.unique(np.r_[d.lo,d.hi]) for d in [ss,uu]]
        thin=[lift(np.c_[1-p,p],st)[:,::-1] for p in ends]  # st orders count(H) n..0
        robust=[h_extremes(n,ss.lo.min(),maxs),h_extremes(n,minu,uu.hi.max())]
        c,r,lower=rule(*robust);upper=rule(*thin)[2]
        assert lower<=upper+1e-7
        rows.append(dict(n=n,D_lower=lower,D_upper=upper,delta_lower=separation(*robust),delta_upper=separation(*thin),old_four_D=old.loc[old.n==n,'D'].iloc[0]))
    write(rows,'legacy_H_all_orders')
    rows=[]
    for n in [1,2,5]:
        st=states(n,4)
        # Upper: true laws can take any stationary corner or midpoint. Lower: grid interpolation
        # for bounded test functions, with analytic second derivative remainder for each model.
        grid=np.linspace(0,1,5)
        pre=[]; err=[]
        for d in (ss,uu):
            Q=banks(d,product(grid,grid));pre.append(lift(Q,st))
            e=n*(n-1)/4*((d.hi0-d.lo0)**2+(d.hi1-d.lo1)**2)/(len(grid)-1)**2
            err.append(np.tile(e.to_numpy(),len(grid)**2))
        # Constraint generation. Start with midpoint and add maximally violated rows.
        c,r,upper=exchange(pre,err,False)
        cl,rl,lower=exchange(pre,err,True)
        assert lower<=upper+1e-7
        mid=[lift(banks(d,[(.5,.5)]),st) for d in [ss,uu]]
        dist=separation(*mid)
        if n==1:
            robust_delta=separation(*[banks(d,product([0.,1.],repeat=2)) for d in (ss,uu)])
            assert robust_delta>=.2-1e-8 and abs(lower-upper)<1e-7
        else: robust_delta=np.nan
        rows.append(dict(n=n,D_missing_lower=lower,D_missing_upper=upper,D_midpoint=rule(*mid)[2],delta_midpoint=dist,delta_robust_exact=robust_delta))
        write(pd.DataFrame({'certify':cl,'reject':rl,'alert':1-cl-rl}).join(pd.DataFrame(st,columns=['low_no','low_event','high_no','high_event'])),f'legacy_robust_rule_n{n}')
    write(rows,'legacy_four_symbol')
def exchange(pre,err,protect):
    S,U=pre; k=S.shape[1]
    eS,eU=err if protect else [np.zeros(len(a)) for a in pre]
    banks4=[U,S,S,U]; errs=[eU,eS,eS,eU]
    sel=[set([0,len(a)//2,len(a)-1]) for a in banks4]
    for iteration in range(300):
        matrices=[];bs=[]
        for j,(a,e,ids) in enumerate(zip(banks4,errs,sel)):
            idx=np.array(sorted(ids)); p=a[idx]; z=np.zeros_like(p)
            if j<2:
                matrices.append(np.c_[p if j==0 else z,z if j==0 else p,np.zeros(len(p))]);bs.extend(.05-e[idx])
            else:
                matrices.append(np.c_[-p,-p,np.ones(len(p))]);bs.extend(-e[idx])
        matrices.append(np.c_[np.eye(k),np.eye(k),np.zeros(k)]);bs.extend(np.ones(k))
        x=solve(np.r_[np.zeros(2*k),-1],np.vstack(matrices),np.array(bs))
        c,r=x[:k],x[k:2*k]
        vs=[U@c+eU-.05,S@r+eS-.05,x[-1]+eS-S@(c+r),x[-1]+eU-U@(c+r)]
        if max(v.max() for v in vs)<2e-8: return c,r,x[-1]
        for v,ids in zip(vs,sel):
            ii=np.flatnonzero(v>1e-8)
            ids.update(ii[np.argsort(v[ii])[-5:]])
    raise RuntimeError('LP failed to finish')
