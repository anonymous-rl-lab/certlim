from common import *
from scipy.spatial.distance import cdist
def main():
    s=read_steps()
    group=s.groupby(['cell','stage'],sort=False)
    s['prevT']=group.Tmax.shift(1)
    # At time t, baseline is computed through t-2, with five earlier observations.
    s['past_median']=s.groupby(['cell','stage'],sort=False).Tmax.transform(lambda v:v.shift(2).expanding(min_periods=5).median())
    s['a']=s.I_med.round().clip(1,5).astype(int)
    s=s[(s.a<=4)&(s.V0<=4)].copy()
    s['z']=np.digitize(s.V0,[3.55,3.7,3.85],right=True)
    pref=s[s.arm.str.startswith('uniform')].z.value_counts(normalize=True).sort_index().to_numpy()
    s=s[s.past_median.notna()].copy();s['u']=(s.prevT>s.past_median).astype(int)
    grade_df=pd.read_csv(OUT/'legacy_grades.csv').query('policy=="uniform" and grade!="?"')
    s=s.merge(grade_df[['cell','stage','grade']],on=['cell','stage'])
    policies={'uniform_control':np.ones((2,4))*.25,'past_temperature_derating':np.array([[.0457,.0839,.7609,.1095],[.7523,.2272,.0203,.0002]])}
    rows=[]; vertices={k:{g:[] for g in "SU"} for k in policies}
    for (cell,stage,gr),d in s.groupby(['cell','stage','grade']):
        ids=(8*d.z+4*d.u+d.a-1).to_numpy()
        N=np.bincount(ids,minlength=32).reshape(4,2,4)
        H=np.bincount(ids,weights=(d.Vend<=3.25),minlength=32).reshape(4,2,4)
        den=N.sum(axis=(1,2))
        Pu=np.divide(N.sum(axis=2),den[:,None],out=np.full((4,2),.5),where=den[:,None]>0)
        for name,pi in policies.items():
            pi=pi/pi.sum(axis=1,keepdims=True)
            w=pref[:,None,None]*Pu[:,:,None]*pi[None,:,:]
            loss=np.sum(w*(N<5))
            # For entirely unobserved voltage bins this midpoint also uses prevalence 1/2.
            pr=np.divide(H,N,out=np.full((4,2,4),.5),where=N>=5)
            q=np.array([np.sum((w*(1-pr))[:,:,:2]),np.sum((w*pr)[:,:,:2]),np.sum((w*(1-pr))[:,:,2:]),np.sum((w*pr)[:,:,2:])])
            assert abs(q.sum()-1)<1e-10
            # For observed voltage bins the high-current marginal is fixed. Unknown
            # hazards let the two event masses vary on a rectangle. For missing
            # voltage bins, even the hot fraction is free, so high-current mass
            # lies between the two derating policies' high-current probabilities.
            knownw=w*(den>0)[:,None,None]
            basehigh=knownw[:,:,2:].sum()
            seen_event=knownw*(N>=5)*pr
            missing=knownw*(N<5)
            m=pref[den==0].sum()
            vv=[]
            for a in (0,1):
                for b in (0,1):
                    x=seen_event[:,:,:2].sum()+a*missing[:,:,:2].sum()
                    y=seen_event[:,:,2:].sum()+b*missing[:,:,2:].sum()
                    base=np.array([1-m-basehigh-x,x,basehigh-y,y])
                    for high in np.unique(pi[:,2:].sum(axis=1)):
                        for low_h in (0,1):
                            for high_h in (0,1):
                                zlaw=np.array([(1-high)*(1-low_h),(1-high)*low_h,high*(1-high_h),high*high_h])
                                vv.append(base+m*zlaw)
            vertices[name][gr].extend(np.unique(np.round(vv,14),axis=0))
            rows.append(dict(cell=cell,stage=stage,grade=gr,channel=name,missing_mass=loss,missing_z_mass=pref[den==0].sum(),**{f'p{i}':q[i] for i in range(4)}))
    v=pd.DataFrame(rows);write(v,'thermal_models')
    out=[]
    for name,g in v.groupby('channel'):
        s,u=[g[g.grade==j][[f'p{i}' for i in range(4)]].to_numpy() for j in ['S','U']]
        for n in [1,2,5]:
            st=states(n,4);S,U=lift(s,st),lift(u,st)
            out.append(dict(channel=name,n=n,S=len(S),U=len(U),delta_midpoint=separation(S,U),D_midpoint=rule(S,U)[2],min_pair_TV=cdist(S,U,metric='cityblock').min()/2,median_missing=g.missing_mass.median(),complete_S=sum((g.grade=='S')&(g.missing_mass<1e-12)),complete_U=sum((g.grade=='U')&(g.missing_mass<1e-12))))
    write(out,'thermal_summary')
    w=[]
    for ch,data in vertices.items():
        S,U=[np.array(data[j]) for j in 'SU']
        w.append(dict(channel=ch,delta_all_completions_n1=separation(S,U),D_all_completions_n1=rule(S,U)[2]))
    write(w,'thermal_missing_robust')
if __name__=='__main__':main()
