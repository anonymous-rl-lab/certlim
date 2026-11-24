"""Run the prelocked charge-trace audit with a separate full-discharge reference."""
from pathlib import Path
import sys, hashlib, json
from collections import Counter
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor
from scipy.io import loadmat
from scipy.stats import beta,binomtest
from scipy.optimize import linprog
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'
def key(x):return hashlib.sha256(('CETL-TII-01|'+str(x)).encode()).hexdigest()
def conf(k,n,tail,upper):
    if n==0:return 1. if upper else 0.
    if upper:return 1. if k==n else float(beta.ppf(1-tail,k+1,n-k))
    return 0. if k==0 else float(beta.ppf(tail,k,n-k+1))
def features(v,i,q):
    out={'initial_mv':v[0],'charge_samples':len(v),'final_q':q[-1],'range_q':np.ptp(q)}
    for f in (0,.1,.25,.5,.75,.9,1):
        j=round(f*(len(v)-1));out[f'v_{f}']=v[j];out[f'i_{f}']=i[j]
    for threshold in (3300,3350,3400,3450,3500,3550,3600):
        js=np.flatnonzero(v>=threshold)
        out[f'first_s_{threshold}']=int(js[0]*3) if len(js) else -1
        out[f'q_{threshold}']=q[js[0]] if len(js) else -1
    for k,a in [('v',v),('i',i)]:
        out.update({k+'_mean':np.mean(a),k+'_sd':np.std(a),k+'_min':np.min(a),k+'_max':np.max(a)})
    return out
def extract(p):
    data=loadmat(p)['unbalanced_data'][0,0]
    labels=data['Capacity_labels'].ravel()
    blocks=sorted(set(np.arange(len(labels))//20),key=key);bn=len(blocks);out=[];qc=[]
    split={j:('train' if k<int(.4*bn) else 'cal' if k<int(.65*bn) else 'test') for k,j in enumerate(blocks)}
    for k,label in enumerate(labels):
        v,i,q=[data[f][k,0].ravel().astype(float) for f in ['Vp','Ip','Qp']]
        vd,qd=[data[f][k,0].ravel() for f in ['Vd','Qd']]
        if (len(v)<2 or len(v)!=len(i) or len(v)!=len(q) or len(vd)<2 or len(vd)!=len(qd) or
                not np.all(np.isfinite(np.r_[v,i,q,vd,qd,label])) or min(v)<=0 or min(vd)<=0 or label<=0):
            qc.append({'record':k,'reason':'incomplete/nonphysical'});continue
        digest=hashlib.sha256(b''.join(a.astype('<f8').tobytes() for a in (v,i,q))).hexdigest()
        out.append(dict(record=k,block=k//20,split=split[k//20],trace_sha=digest,label_mAh=label,
                        discharge_end_mAh=qd[-1],discharge_h=(len(vd)-1)*3/3600,charge_h=(len(v)-1)*3/3600,
                        **features(v,i,q)))
    d=pd.DataFrame(out);bad=d.groupby('trace_sha').split.nunique().loc[lambda x:x>1].index
    for k in d.loc[d.trace_sha.isin(bad),'record']:qc.append({'record':k,'reason':'duplicate trace across splits'})
    d=d[~d.trace_sha.isin(bad)].copy()
    pd.DataFrame(qc,columns=['record','reason']).to_csv(OUT/'excluded.csv',index=False)
    return d
def thresholds(cal,g,score):
    cand=[]
    for ispass in [False,True]:
        vals=np.sort(score[cal&(g==ispass)])
        n=len(vals);ks=[k for k in range(n) if conf(k,n,.025,True)<=.05]
        if not ks:
            cand.append(-np.inf if ispass else np.inf);continue
        k=max(ks)
        cand.append(vals[k] if ispass else vals[-1-k])
    upper,lower=cand
    if lower>upper:lower=upper=(lower+upper)/2
    return lower,upper
def act(score,lower,upper):return np.where(score>upper,2,np.where(score<lower,1,0))
def bootstrap(t):
    cols=[];blocks=sorted(t.block.unique())
    for b in blocks:
        sub=t[t.block==b];row=[]
        for grade in [False,True]:
            sel=sub[sub.grade==grade];row.extend([len(sel),int((sel.A!=0).sum()),int((sel.B!=0).sum())])
        row.append(np.sum(sub.discharge_h*((sub.B!=0).astype(int)-(sub.A!=0).astype(int))))
        cols.append(row)
    vals=np.array(cols);ids=np.random.default_rng(43).integers(0,len(vals),size=(10000,len(vals)))
    r=vals[ids].sum(1)
    valid=(r[:,0]>0)&(r[:,3]>0)
    rr=r[valid]
    delta=np.minimum(rr[:,2]/rr[:,0],rr[:,5]/rr[:,3])-np.minimum(rr[:,1]/rr[:,0],rr[:,4]/rr[:,3])
    return {'draws_with_both_grades':int(sum(valid)),'draws':len(r),'gain_interval':np.quantile(delta,[.025,.975]).tolist(),'hours_interval':np.quantile(r[:,6],[.025,.975]).tolist()}
def extreme(box,v,maxi):
    lo,hi=box;p=lo.copy()
    for j in np.argsort(-v if maxi else v):p[j]+=min(max(0.,1.-sum(p)),hi[j]-p[j])
    return p
def coarse_design(d,t):
    cut=np.quantile(d.loc[d.split=='train','initial_mv'],[.25,.5,.75]);idx=np.searchsorted(cut,t.initial_mv,side='right')
    K=4;tail=.025/(2*2*K);boxes=[]
    for g in [False,True]:
        cnt=np.bincount(idx[t.grade==g],minlength=K);n=sum(cnt)
        boxes.append(tuple(np.array([conf(k,n,tail,u) for k in cnt]) for u in [False,True]))
    low=np.maximum(boxes[0][0],boxes[1][0]);high=np.minimum(boxes[0][1],boxes[1][1])
    intersect=bool(np.all(low<=high) and sum(low)<=1<=sum(high))
    # Enumerate interval-simplex vertices (one free coordinate) for exact robust optimum.
    from itertools import product
    def verts(box):
        lo,hi=box;p=[]
        for j in range(K):
            others=np.flatnonzero(np.arange(K)!=j)
            for mask in product([0,1],repeat=K-1):
                s=lo.copy();s[others]=np.where(mask,hi[others],lo[others]);s[j]=1.-sum(s[others])
                if lo[j]-1e-12<=s[j]<=hi[j]+1e-12:p.append(s)
        return np.array(p)
    V=[verts(box) for box in boxes];base=np.eye(K);rows=list(np.c_[base,base,np.zeros(K)]);rhs=[1.]*K
    for j,vs in enumerate(V):
        for v in vs:
            rows.extend([np.r_[v if j==0 else np.zeros(K),v if j==1 else np.zeros(K),0],np.r_[-v,-v,1]])
            rhs.extend([.05,0.])
    prob=np.r_[np.zeros(2*K),-1]
    opt=linprog(prob,A_ub=rows,b_ub=rhs,bounds=(0,1),method='highs')
    assert opt.success
    dual=np.array(opt.ineqlin.marginals).clip(max=0)
    # Weak-duality upper bound on maximum D, with box residual correction for finite precision.
    dualU=-float(np.dot(rhs,dual)+np.minimum(0,prob-np.asarray(rows).T@dual).sum())
    if intersect:assert abs(dualU-.1)<1e-7
    rich_error=[];rich_dec=[]
    for g,wrong in [(False,2),(True,1)]:
        x=t[t.grade==g].B
        rich_error.append(conf(sum(x==wrong),len(x),.025/4,True));rich_dec.append(conf(sum(x!=0),len(x),.025/4,False))
    return dict(cutpoints_mV=cut.tolist(),overlap=intersect,A_robust_optimum=opt.x[-1],A_robust_upper=dualU,
                B_joint_error_U=rich_error,B_joint_decisive_L=rich_dec,
                strict_gap_L=min(rich_dec)-dualU if max(rich_error)<=.05 else None)
def main():
    OUT.mkdir(exist_ok=True)
    d=extract(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'cache/CETL-data.mat')
    train=(d.split=='train').to_numpy();cal=(d.split=='cal').to_numpy();g=(d.label_mAh>=10850).to_numpy()
    d['grade']=g
    feat=[c for c in d.columns[d.columns.get_loc('initial_mv'): ] if c!='grade'];fits=[]
    for code,fs in [('A',['initial_mv']),('B',feat)]:
        model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=8,max_features=1.,random_state=43,n_jobs=1)
        model.fit(d.loc[train,fs],d.loc[train,'label_mAh']/15500)
        sc=model.predict(d[fs]);lower,upper=thresholds(cal,g,sc)
        d[code+'_score']=sc;d[code]=act(sc,lower,upper)
        fits.append(dict(channel=code,features=fs,lo=lower if np.isfinite(lower) else None,hi=upper if np.isfinite(upper) else None))
    t=d[d.split=='test'].copy();metrics=[]
    for scope in ['train','cal','test']:
        sub=d[d.split==scope]
        for code in ['A','B']:
            for grade,wrong in [(False,2),(True,1)]:
                x=sub[sub.grade==grade][code];err=sum(x==wrong);n=len(x);dec=sum(x!=0)
                metrics.append(dict(split=scope,channel=code,grade='P' if grade else 'F',n=n,
                                    pass_n=sum(x==2),fail_n=sum(x==1),refer_n=sum(x==0),errors=err,error_U=conf(err,n,.025,True),decisive=dec/n if n else None))
    def paired(grade):
        z=t[t.grade==grade];wins=sum((z.B!=0)&(z.A==0));loss=sum((z.A!=0)&(z.B==0))
        return dict(n=len(z),wins=int(wins),loss=int(loss),p=binomtest(wins,wins+loss,.5,alternative='greater').pvalue if wins+loss else 1.)
    summ=dict(n=len(d),n_test=len(t),n_blocks_test=t.block.nunique(),fits=fits,
              counts=d.groupby('split').grade.agg(['count','sum']).to_dict('index'),
              label_check_max_abs_mAh=float(np.max(abs(d.discharge_end_mAh-d.label_mAh))),
              label_check_over_1_mAh=int(sum(abs(d.discharge_end_mAh-d.label_mAh)>1)),
              heldout_hours_all=float(t.discharge_h.sum()),
              gross_discharge_hours={c:float(t.loc[t[c]!=0,'discharge_h'].sum()) for c in ['A','B']},
              paid_charge_hours=float(t.charge_h.sum()),paired=[paired(False),paired(True)],bootstrap=bootstrap(t),coarse_design=coarse_design(d,t))
    d[['record','block','split','trace_sha','initial_mv','label_mAh','discharge_end_mAh','grade','charge_h','discharge_h','A_score','B_score','A','B']].to_csv(OUT/'predictions.csv',index=False,float_format='%.12g')
    pd.DataFrame(metrics).to_csv(OUT/'metrics.csv',index=False,float_format='%.12g')
    pd.DataFrame([dict(block=b,grade=grade,method=c,n=len(z),errors=sum(z[c]==wrong),decisions=sum(z[c]!=0)) for (b,grade),z in t.groupby(['block','grade']) for c in ['A','B'] for wrong in [1 if grade else 2]]).to_csv(OUT/'blocks.csv',index=False)
    (OUT/'summary.json').write_text(json.dumps(summ,indent=2,default=lambda x:x.item())+'\n')
if __name__=='__main__':main()
