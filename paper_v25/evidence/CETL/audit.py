"""Independently check all test actions, reference labels, physical files and end-to-end referrals."""
import sys, hashlib, json, math
from pathlib import Path
import numpy as np,pandas as pd
from scipy.io import loadmat
from scipy.stats import binom, spearmanr
from scipy.optimize import brentq
from sklearn.ensemble import ExtraTreesRegressor
from run_pulsefree import features
ROOT=Path(__file__).resolve().parent
O=ROOT/'results'
def hi(k,n):
    return 1. if k==n else brentq(lambda p:binom.cdf(k,n,p)-.025,0,1,xtol=1e-14)
def main():
    d=loadmat(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'cache/CETL-data.mat')['unbalanced_data'][0,0]
    labels=d['Capacity_labels'].ravel()
    ss=json.loads((O/'summary.json').read_text())
    p=pd.read_csv(O/'predictions.csv');met=pd.read_csv(O/'metrics.csv')
    bs=sorted(range(200),key=lambda b:hashlib.sha256(f'CETL-TII-01|{b}'.encode()).digest())
    test_blocks=set(bs[130:]);ids=[r for r in range(len(labels)) if r//20 in test_blocks]
    target=p[p.split=='test'].set_index('record'); assert set(target.index).issubset(ids)
    # Count initial zeros anywhere before changing input QA decisions. No refitting.
    gp=[];zeros={}
    for r in range(len(labels)):
        assert abs(float(d['Qd'][r,0].ravel()[-1])-labels[r])<1e-8
        v=d['Vp'][r,0].ravel();vd=d['Vd'][r,0].ravel()
        if min(v)==0:
            j=np.flatnonzero(v==0);a='only_initial_charge_zero' if len(j)==1 and j[0]==0 else 'other_charge_zero';zeros[a]=zeros.get(a,0)+1
        if min(vd)==0:zeros['discharge_trace_zero']=zeros.get('discharge_trace_zero',0)+1
    # The full-cohort audit can route using only charge-side inputs. One held-out
    # record was originally excluded by reference-waveform QC alone. Apply the
    # same trained rule to it without consulting that future waveform at triage.
    extra={}
    for r in ids:
        if r in target.index: continue
        v,i,q=[d[f][r,0].ravel().astype(float) for f in ['Vp','Ip','Qp']]
        if len(v)>1 and len(v)==len(i)==len(q) and np.all(np.isfinite(np.r_[v,i,q])) and min(v)>0:
            extra[r]=features(v,i,q)
    train=p[p.split=='train']
    feats=pd.DataFrame([features(*[d[f][int(r),0].ravel().astype(float) for f in ['Vp','Ip','Qp']]) for r in train.record])
    extra_actions={};j=0;work={}

    for tag in ['A','B']:
        f=ss['fits'][j];j+=1
        lo=f['lo'] if f['lo'] is not None else -np.inf;up=f['hi'] if f['hi'] is not None else np.inf
        # For near-threshold ties, rely on stored actions and separately check rounded-score ties.
        q=target[tag+'_score'].to_numpy();a=target[tag].to_numpy()
        clear=(abs(q-lo)>2e-11)&(abs(q-up)>2e-11)
        assert np.all(a[clear]==np.where(q[clear]>up,2,np.where(q[clear]<lo,1,0)))
        fs=f['features']
        model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=8,max_features=1.,random_state=43,n_jobs=1)
        model.fit(feats[fs],train.label_mAh.to_numpy()/15500)
        extra_actions[tag]={}
        if extra:
            scores=model.predict(pd.DataFrame.from_dict(extra,orient='index')[fs])
            extra_actions[tag]={int(r):(2 if score>up else 1 if score<lo else 0) for r,score in zip(extra,scores)}
        for scope,indices in [('complete',target.index),('refer_on_charge_invalid',ids)]:
            table=np.array([(labels[r]>=10850,int(target.loc[r,tag]) if r in target.index else extra_actions[tag].get(r,0),(len(d['Vd'][r,0])-1)*3./3600) for r in indices])
            for g,wrong in [(1,1),(0,2)]:
                z=table[table[:,0]==g];err=sum(z[:,1]==wrong);n=len(z);h=hi(err,n)
                gp.append(dict(scope=scope,channel=tag,grade='P' if g else 'F',n=n,errors=err,error_U=h,decisions=int(sum(z[:,1]!=0)),decisive=np.mean(z[:,1]!=0)))
                if scope=='complete':
                    m=met[(met.split=='test')&(met.channel==tag)&(met.grade==('P' if g else 'F'))].iloc[0]
                    assert m.n==n and m.errors==err and abs(m.error_U-h)<1e-10
            h=sum(table[table[:,1]!=0,2])
            if scope=='complete':assert abs(h-ss['gross_discharge_hours'][tag])<1e-7
            work[f'{scope}_{tag}']=h
    pd.DataFrame(gp).to_csv(O/'audit_all_heldout.csv',index=False,float_format='%.12g')
    excluded_count=int((~np.isin(ids,target.index)).sum())
    details=dict(additional_actions_without_reference_QC=extra_actions,zero_patterns=zeros,total=len(labels),valid=len(p),raw_heldout=len(ids),invalid_heldout=excluded_count,
                 source_order_capacity_spearman=float(spearmanr(np.arange(len(labels)),labels).statistic),
                 test_grade_block_counts={str(k):int(v) for k,v in target.groupby('grade').block.nunique().items()},
                 gross_hours_saved_B_minus_A=work['complete_B']-work['complete_A'],
                 break_even_minutes_per_complete_cell=60*(work['complete_B']-work['complete_A'])/len(target),
                 break_even_minutes_per_all_heldout=60*(work['refer_on_charge_invalid_B']-work['refer_on_charge_invalid_A'])/len(ids))
    (O/'audit.json').write_text(json.dumps(details,indent=2)+'\n')
if __name__=='__main__':main()
