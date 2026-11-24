"""Conditional confidence sequences, with simultaneous coverage across registered strata."""
from common import *
from functools import lru_cache
from scipy.optimize import brentq
from scipy.special import betaln,xlogy,xlog1py
from legacy import banks
from itertools import product
@lru_cache(maxsize=None)
def cs(n,y,stage,k):
    if n<5: return (0.,1.)
    p=y/n
    alpha=.05/(28*k*(stage+1)*(stage+2))
    offset=betaln(y+.5,n-y+.5)-betaln(.5,.5)+np.log(alpha)
    def value(x):return offset-xlogy(y,x)-xlog1py(n-y,-x)
    return (brentq(value,0.,p) if y else 0.,brentq(value,p,1.) if y<n else 1.)
def legacy_conf(s):
    s=s.copy();s['A']=s.I_med.round().clip(1,5).astype(int)
    s=s[(s.A<=4)&(s.V0<=4)].copy();s['z']=np.digitize(s.V0,[3.55,3.7,3.85],right=True)
    pref=s[s.arm.str.startswith('uniform')].z.value_counts(normalize=True).sort_index().to_numpy()
    out=[]
    for (cell,stage),d in s.groupby(['cell','stage']):
        if len(d)<150:continue
        ids=(4*d.z+d.A-1).to_numpy()
        nn=np.bincount(ids,minlength=16);hh=np.bincount(ids,weights=(d.Vend<=3.25),minlength=16)
        interval=np.array([cs(int(n),round(y),int(stage),16) for n,y in zip(nn,hh)]).reshape(4,4,2)
        for pol,weights in POL.items():
            q=(np.outer(pref,weights)[:,:,None]*interval).sum(axis=0)
            lo,hi=q.sum(axis=0)
            out.append(dict(cell=cell,stage=stage,policy=pol,qhi=sum(weights[2:]),lo=lo,hi=hi,grade=grade(lo,hi).item(),lo0=q[:2,0].sum(),hi0=q[:2,1].sum(),lo1=q[2:,0].sum(),hi1=q[2:,1].sum()))
    f=pd.DataFrame(out);write(f,'legacy_confidence_sets')
    return f
def main():
    f=legacy_conf(read_steps())
    p=pd.read_csv(OUT/'physical_stages.csv')
    rows=[]
    for row in p.itertuples(index=False):
        q=[cs(int(getattr(row,f'n0_{j}')),round(getattr(row,f'p0_{j}')*getattr(row,f'n0_{j}')),row.stage,4) for j in range(4)]
        lo,hi=np.mean(q,axis=0)
        rows.append(dict(cell=row.cell,stage=row.stage,split=row.split,lo=lo,hi=hi,grade=grade(lo,hi).item()))
    phys=pd.DataFrame(rows);write(phys,'physical_confidence_sets')
    out=[]
    for name,d in [('legacy',f),('physical_train',phys[phys.split=='train']),('physical_test',phys[phys.split=='test'])]:
        o=dict(scope=name,S=sum(d.grade=='S'),U=sum(d.grade=='U'),withheld=sum(d.grade=='?'),cells_S=d[d.grade=='S'].cell.nunique(),cells_U=d[d.grade=='U'].cell.nunique())
        if name=='legacy' and o['S'] and o['U']:
            S,U=[banks(d[d.grade==j],product([0.,1.],repeat=2)) for j in ['S','U']]
            c,r,t=rule(S,U);o.update(delta_n1=separation(S,U),D_n1=t)
            write(pd.DataFrame({'state':['low_no','low_event','high_no','high_event'],'certify':c,'reject':r,'alert':1-c-r}),'confidence_rule_n1')
        out.append(o)
    write(out,'confidence_summary')
if __name__=='__main__':main()
