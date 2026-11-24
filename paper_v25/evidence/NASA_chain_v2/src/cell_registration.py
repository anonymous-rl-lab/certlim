from common import *
from itertools import product
from legacy import banks

def sequential_bounds(count,hit):
    # Ville + Jensen for the Bernoulli conditional MGF. The confidence event is
    # uniform in the number of visits, selections must precede their outcomes.
    if count==0:return (0.,1.)
    grid=2.**(np.arange(-12,5)/2)
    budget=np.log(28*4*2*2*len(grid)/.05)
    def edge(lam):
        return np.expm1(lam*(hit/count)-budget/count)/np.expm1(lam)
    return max(0.,edge(grid).max()),min(1.,edge(-grid).min())
def main():
    # The cell-life confidence target includes all stages. Selecting visits from
    # stages using their eventual length would make inclusion depend on the future.
    f=read_steps()
    gp=f.groupby(['cell','stage'],sort=False)
    f['previous']=gp.Vend.shift()
    f['ordinal']=gp.cumcount()
    f=f[f.previous.notna()&(f.ordinal%25!=0)].copy()
    f['a']=np.where(abs(f.I_med-1.5)<=.06,0,np.where(abs(f.I_med-3)<=.06,1,-1))
    f=f[f.a>=0].copy()
    f['stratum']=2*f.a+(f.previous>3.55)
    f['half']=(f.ordinal//25)%2
    f['hit']=(f.Vend<=3.25)
    if OUT.name=='fixed60':
        assert not ((f.dur_s<60)&~f.hit).any()
        f['hit']&=f.dur_s<=60
    out=[]
    for (arm,temp),d in f.groupby(['arm','temp']):
      cells=sorted(d.cell.unique(),key=lambda c:int(c[2:]))
      for cell,g in d.groupby('cell'):
        split='train' if cell in cells[:2] else 'test'
        row=dict(cell=cell,split=split,arm=arm,temp=temp,stages=g.stage.nunique(),qhi=.5)
        for h,part in [(0,'ref'),(1,'ev')]:
            selected=g[g.half==h]
            counts=np.bincount(selected.stratum,minlength=4)
            hits=np.bincount(selected.stratum,weights=selected.hit,minlength=4)
            band=np.array([sequential_bounds(n,y) for n,y in zip(counts,hits)])
            lo,hi=band.mean(axis=0)
            row.update({part+'_lo':lo,part+'_hi':hi,part+'_grade':grade(lo,hi).item(),part+'_n':counts.sum(),part+'_rate':np.mean(hits/counts)})
            if h==1:
                row.update(lo0=band[:2,0].sum()/4,hi0=band[:2,1].sum()/4,lo1=band[2:,0].sum()/4,hi1=band[2:,1].sum()/4)
        row['grade']=row['ref_grade'];out.append(row)
    d=pd.DataFrame(out);write(d,'whole_cell_classes')
    def get(g):
        return [banks(g[g.grade==j],product([0.,1.],repeat=2)) for j in ['S','U']]
    def audit(c,r,S,U):
        return dict(unsafe_to_certify=max(U@c),safe_to_reject=max(S@r),D_min=min(min(U@(c+r)),min(S@(c+r))))
    summary=[];look=[]
    for name,train,test in [('registered_28',d,d),('train14',d[d.split=='train'],d[d.split=='train']),('test14_frozen',d[d.split=='train'],d[d.split=='test'])]:
        a=dict(scope=name,S=sum(test.grade=='S'),U=sum(test.grade=='U'),withheld=sum(test.grade=='?'))
        if set(train.grade)>={'S','U'} and set(test.grade)>={'S','U'}:
            S,U=get(train);s,u=get(test)
            c,r,t=rule(S,U)
            a.update(delta_test=separation(s,u),D_train=t,**audit(c,r,s,u))
            for mode in ['four_symbol','H_only']:
                if mode=='H_only':
                    agg=lambda v:np.c_[v[:,0]+v[:,2],v[:,1]+v[:,3]]
                    cc,rr,dt=rule(agg(S),agg(U));cc=cc[[0,1,0,1]];rr=rr[[0,1,0,1]]
                    a.update({'H_'+k:v for k,v in audit(cc,rr,s,u).items()})
                else:cc,rr=c,r
                for i in range(4):look.append(dict(scope=name,method=mode,state=i,certify=cc[i],reject=rr[i],alert=1-cc[i]-rr[i]))
        summary.append(a)
    write(summary,'whole_cell_certificate');write(look,'whole_cell_lookups')
if __name__=='__main__':main()
