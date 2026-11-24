from common import *
from scipy.stats import binom
from itertools import product

def extract(s, endpoint):
    g=s.groupby(['cell','stage'],sort=False)
    s=s.assign(previous=g.Vend.shift(),ordinal=g.cumcount(),size=g.step_k.transform('size'))
    s=s[s.previous.notna()&(s['size']>=150)&(s.ordinal%25!=0)].copy()
    s['a']=np.where(abs(s.I_med-1.5)<=.06,0,np.where(abs(s.I_med-3)<=.06,1,-1))
    s=s[s.a>=0].copy()
    s['z']=(s.previous>3.55).astype(int)
    event=s.Vend<=3.25
    if endpoint=='fixed60':
        assert not ((s.dur_s<60)&~event).any()
        event=event&(s.dur_s<=60)
    s['h']=event.astype(int)
    s['stratum']=2*s.a+s.z
    s['half']=(s.ordinal//25)%2
    rows=[];replay=[]
    for (cell,arm,temp,stage),d in s.groupby(['cell','arm','temp','stage']):
        counts=[];rates=[]
        for half in (0,1):
            ds=d[d.half==half]
            ns=np.bincount(ds.stratum,minlength=4)
            hs=np.bincount(ds.stratum,weights=ds.h,minlength=4)
            counts.append(ns);rates.append(hs/np.maximum(ns,1))
        good=counts[0]>=5
        lo=np.dot(rates[0],good)/4;hi=lo+sum(~good)/4
        rows.append(dict(cell=cell,arm=arm,temp=temp,stage=stage,lo=lo,hi=hi,grade=grade(lo,hi).item(),**{f'n{h}_{j}':counts[h][j] for h,j in product(range(2),range(4))},**{f'p{h}_{j}':rates[h][j] for h,j in product(range(2),range(4))}))
        ds=d[d.half==1]
        h=[ds.loc[ds.stratum==j,'h'].to_numpy() for j in range(4)]
        for k in (1,2):
            b=min(map(len,h))//k
            if not b: continue
            v=np.vstack([v[:b*k].reshape(b,k).sum(axis=1) for v in h])
            for i in range(b):
                replay.append((cell,stage,4*k,i,int(v[0,i]+v[1,i]),int(v[2,i]+v[3,i])))
    f=pd.DataFrame(rows)
    nn=f[[f'n0_{j}' for j in range(4)]].to_numpy()
    mar=fixed_design_margin(nn,np.full_like(nn,.25,dtype=float),len(f))
    f['grade_working95']=grade(f.lo-mar,f.hi+mar)
    folds={}
    for _,v in f.groupby(['arm','temp']):
        cells=sorted(v.cell.unique(),key=lambda c:int(c[2:]))
        assert len(cells)==4
        folds.update({c:('train' if i<2 else 'test') for i,c in enumerate(cells)})
    f['split']=f.cell.map(folds)
    write(f,'physical_stages')
    b=pd.DataFrame(replay,columns=['cell','stage','n','block','low_hits','high_hits'])
    b=b.merge(f[['cell','stage','grade','grade_working95','split','arm','temp']],on=['cell','stage'],validate='many_to_one')
    write(b,'physical_blocks')
    return f,b

def pmfs(p,k):
    low=np.convolve(binom.pmf(range(k+1),k,p[0]),binom.pmf(range(k+1),k,p[1]))
    high=np.convolve(binom.pmf(range(k+1),k,p[2]),binom.pmf(range(k+1),k,p[3]))
    return np.outer(low,high).ravel(),np.convolve(low,high)
def fit(train,n):
    modes=['load_and_cutoff','cutoff_count']
    ok=train[(train.grade!='?')&(train[[f'n1_{j}' for j in range(4)]].min(axis=1)>=5)]
    outcomes=[pmfs(row,n//4) for row in ok[[f'p1_{j}' for j in range(4)]].to_numpy()]
    rs={}
    for j,mode in enumerate(modes):
        laws=np.array([v[j] for v in outcomes])
        c,r,t=rule(laws[ok.grade=='S'],laws[ok.grade=='U'])
        rs[mode]=(c,r,t)
    # For any joint law on the four (or eight) observations, linear lookup in the
    # fraction of hits has expectation fixed by its mean. All-equal Bernoulli
    # outcomes also show this is the optimal value under a mean-only specification.
    pS=np.array([[1.,0.],[.85,.15]])
    pU=np.array([[.65,.35],[0.,1.]])
    c,r,t=rule(pS,pU)
    q=np.linspace(0,1,n+1)
    rs['mean_only_robust']=((1-q)*c[0]+q*c[1],(1-q)*r[0]+q*r[1],t)
    return rs,ok
def per_stage(b,rs):
    out=[]
    for mode,(c,r,t) in rs.items():
        keys=(b.low_hits*(int(b.n.iloc[0])//2+1)+b.high_hits) if mode=='load_and_cutoff' else b.low_hits+b.high_hits
        d=b.copy()
        d['certify']=c[keys];d['reject']=r[keys]
        d['decisive']=d.certify+d.reject
        g=d.groupby(['cell','arm','temp','stage','grade','grade_working95','n'],as_index=False).agg(blocks=('decisive','size'),certify=('certify','mean'),reject=('reject','mean'),decisive=('decisive','mean'))
        g['method']=mode;g['train_D']=t;out.append(g)
    return pd.concat(out)
def fit_replay(f,b):
    out=[];look=[];train_log=[]
    for split in ['locked_14','LOCO_28']:
        folds=[list(f[f.split=='test'].cell.unique())] if split=='locked_14' else [[c] for c in sorted(f.cell.unique())]
        for tested in folds:
            train=f[~f.cell.isin(tested)]
            for n in [4,8]:
                rs,ok=fit(train,n)
                train_log.append(dict(split=split,test=','.join(tested),n=n,train_S=sum(ok.grade=='S'),train_U=sum(ok.grade=='U')))
                feed=b[(b.cell.isin(tested))&(b.n==n)&(b.grade!='?')]
                if len(feed):
                    g=per_stage(feed,rs);g['validation']=split;out.append(g)
                if split=='locked_14':
                    for mode,(c,r,t) in rs.items():
                        for i in range(len(c)):
                            look.append(dict(method=mode,n=n,state=i,certify=c[i],reject=r[i],alert=1-c[i]-r[i],training_worst_decisive=t))
    out=pd.concat(out,ignore_index=True)
    write(look,'frozen_physical_rules');write(train_log,'physical_training_counts');write(out,'physical_stage_decisions')
    return out
def summarize(df,scope):
    d=df[(df.grade_working95==df.grade)] if scope=='conditional95' else df
    out=[]
    for (split,mode,n),v in d.groupby(['validation','method','n']):
        for grade_name,g in v.groupby('grade'):
            err='certify' if grade_name=='U' else 'reject'
            cell=g.groupby(['cell','arm','temp'],as_index=False).agg(error=(err,'mean'),decisive=('decisive','mean'))
            out.append(dict(scope=scope,validation=split,method=mode,n=n,grade=grade_name,cells=len(cell),stages=len(g),blocks=g.blocks.sum(),cell_equal_error=cell.error.mean(),cell_equal_decisive=cell.decisive.mean(),cell_equal_alert=1-cell.decisive.mean(),pooled_block_error=np.average(g[err],weights=g.blocks),worst_stage_error=g[err].max(),worst_cell_error=cell.error.max(),min_stage_decisive=g.decisive.min(),cell_errors_over_5pct=(cell.error>.0500001).sum()))
    return out
def intervals(df,f):
    rng=np.random.default_rng(SEED+2);out=[]
    for (s,n),group in df.groupby(['validation','n']):
        pop=f if s=='LOCO_28' else f[f.split=='test']
        groups=[np.unique(g.cell) for _,g in pop.groupby(['arm','temp'])]
        # Sample whole cells; use the same cell draws for every method and grade.
        ids=np.array(sum([list(g) for g in groups],[])); pos={v:i for i,v in enumerate(ids)}
        picks=np.hstack([rng.choice([pos[c] for c in g],size=(5000,len(g))) for g in groups])
        for grade_name,g in group.groupby('grade'):
            err='certify' if grade_name=='U' else 'reject'
            by=g.groupby(['method','cell'])[[err,'decisive']].mean()
            results={}
            for method,d in by.groupby(level=0):
                a=d.droplevel(0).reindex(ids).to_numpy(); draws=a[picks]
                den=np.isfinite(draws[:,:,0]).sum(1); estimates=np.nansum(draws,axis=1)/np.maximum(den[:,None],1)
                estimates[den==0]=np.nan;results[method]=(np.nanmean(a,axis=0),estimates)
            for method,(mean,est) in results.items():
                for j,key in enumerate(['error','decisive']):
                    lo,hi=np.nanquantile(est[:,j],[.025,.975])
                    out.append(dict(validation=s,n=n,grade=grade_name,method=method,metric=key,estimate=mean[j],lo=lo,hi=hi,valid_boot=np.isfinite(est[:,j]).sum()))
            ma,ea=results['load_and_cutoff'];mb,eb=results['cutoff_count']
            for j,key in enumerate(['error','decisive']):
                lo,hi=np.nanquantile((ea-eb)[:,j],[.025,.975])
                out.append(dict(validation=s,n=n,grade=grade_name,method='load_minus_count',metric=key,estimate=(ma-mb)[j],lo=lo,hi=hi,valid_boot=np.isfinite((ea-eb)[:,j]).sum()))
    write(out,'physical_cell_bootstrap')
def independent_association(f):
    v=f[(f[[f'n0_{i}' for i in range(4)]].min(axis=1)>=5)&(f[[f'n1_{i}' for i in range(4)]].min(axis=1)>=5)].copy()
    v['ref']=v[[f'p0_{i}' for i in range(4)]].mean(axis=1);v['evi']=v[[f'p1_{i}' for i in range(4)]].mean(axis=1)
    c=v.groupby(['arm','temp','cell'],as_index=False)[['ref','evi']].mean()
    write(c,'physical_cell_association_inputs')
    c[['x','y']]=c[['ref','evi']]-c.groupby(['arm','temp'])[['ref','evi']].transform('mean')
    rng=np.random.default_rng(SEED+1);G=[d.index.to_numpy() for _,d in c.groupby(['arm','temp'])]
    x=c.x.to_numpy();y=c.y.to_numpy();st=x@y/np.linalg.norm(x)/np.linalg.norm(y)
    hits=0
    for i in range(9999):
        yy=y.copy()
        for ix in G: yy[ix]=rng.permutation(y[ix])
        hits+=x@yy/np.linalg.norm(x)/np.linalg.norm(y)>=st-1e-12
    write([dict(cells=len(c),stages=len(v),r=st,permutations=9999,p=(1+hits)/10000)],'physical_cell_association')
def main(endpoint):
    f,b=extract(read_steps(),endpoint);g=fit_replay(f,b)
    write(summarize(g,'missing_only')+summarize(g,'conditional95'),'physical_summary')
    intervals(g,f);independent_association(f)
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--endpoint',choices=['step','fixed60'],default='step')
    main(parser.parse_args().endpoint)
