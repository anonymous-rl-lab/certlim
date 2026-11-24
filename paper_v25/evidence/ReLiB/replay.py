"""Public, outcome-blind CETL-B application followed by discharge-only adjudication."""
from pathlib import Path
import argparse
import csv
import hashlib
import json
import tarfile
from collections import Counter
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.stats import beta
from frozen import HERE, Rule, digest, features, valid, trace_digest

V, I, Q = '电压 (mV)', '电流 (mA)', '容量 (mAh)'
STEP, TYPE = '工步号', '工步名称'

def signature(v,i,q):
    if min(map(len,(v,i,q))) < 40 or not all(np.isfinite(a).all() for a in (v,i,q)):
        return ''
    idx=np.round(np.linspace(3,len(v)-4,33)).astype(int)
    return hashlib.sha256(np.concatenate([np.rint(a[idx]) for a in (v,i,q)]).astype('<i8').tobytes()).hexdigest()

def interval(i,q):
    if len(i)<21: return np.nan
    current=np.lib.stride_tricks.sliding_window_view(i[1:],20)
    good=np.min(current,axis=1)>1000
    if not good.any(): return np.nan
    mean=current[good].mean(axis=1)
    return float(np.median((q[20:]-q[:-20])[good]*180/mean))

def make_signatures(mat):
    if digest(mat)!=json.loads((HERE/'lock.json').read_text())['original_mat_sha256']:
        raise ValueError('Unknown historical MAT bytes')
    d=loadmat(mat)['unbalanced_data'][0,0]
    values={signature(*(d[k][j,0].ravel().astype(float) for k in ['Vp','Ip','Qp'])) for j in range(len(d['Vp']))}
    (HERE/'historical_signatures.txt').write_text('\n'.join(sorted(values-{''}))+'\n')

def catalog(tar):
    paths=[v.name for v in tar if v.isfile() and v.name.endswith('.csv')]
    if len(paths)!=len(set(paths)): raise ValueError('Nonunique paths')
    return sorted(paths,key=lambda x:hashlib.sha256(x.encode()).hexdigest())

def write_csv(frame,file):
    frame.to_csv(file,index=False,float_format='%.17g',lineterminator='\n')

def score(archive,out,census=False):
    rule=Rule()
    original=set((HERE/'historical_trace_hashes.txt').read_text().splitlines())
    original_sig=set((HERE/'historical_signatures.txt').read_text().splitlines())
    seen=set(); seen_sig=set(); dataset=[]; matrix=[]; indices=[]
    with tarfile.open(archive) as tf:
        paths=catalog(tf)
        for path in (paths if census else paths[:1024]):
            # Filter in source order; neither the discharge curve nor its label enters any feature.
            df=pd.read_csv(tf.extractfile(path),usecols=[V,I,Q,STEP,TYPE])
            ch=df[(df[STEP]==1)&(df[TYPE]=='恒流恒压充电')]
            v,i,q=(ch[col].to_numpy(dtype=float) for col in (V,I,Q))
            h=trace_digest(v,i,q); s=signature(v,i,q)
            known=h in original or bool(s and s in original_sig)
            duplicate=h in seen or bool(s and s in seen_sig)
            seen.add(h);seen_sig.add(s)
            ix=len(dataset)
            row=dict(path=path,filename_date=Path(path).stem.rsplit('-',1)[-1][:8],charge_samples=len(v),
                     trace_sha256=h,signature=s,raw_historical_match=h in original,
                     rounded_historical_match=bool(s and s in original_sig),within_sample_repeat=duplicate,
                     cohort_eligible=not (known or duplicate),inferred_step_seconds=interval(i,q),
                     valid_charge=valid(v,i,q),score=np.nan,action='REFER')
            if row['valid_charge']:
                feat=features(v,i,q);matrix.append([feat[k] for k in rule.spec['features']]);indices.append(ix)
            dataset.append(row)
    if indices:
        for ix,s in zip(indices,rule.predict_matrix(matrix)):
            dataset[ix].update(score=float(s),action=rule.action(s))
    path=out/'blind_decisions.csv';write_csv(pd.DataFrame(dataset),path)
    (out/'blind_lock.json').write_text(json.dumps(dict(blind_decisions_sha256=digest(path),
              tar_sha256=digest(archive),selection=('full 15.5Ah archive, post-primary census' if census else 'SHA256(full archive member path ascending), first 1024'),
              population_csv_count=len(paths),selected=len(dataset),lock_sha256=digest(HERE/'lock.json')),indent=2)+'\n')

def bounds(k,n):
    if not n: return None
    return 1. if k==n else float(beta.ppf(.975,k+1,n-k))

def table(d):
    return dict(total=len(d),pass_n=int((d.action=='PASS').sum()),fail_n=int((d.action=='FAIL').sum()),
                refer_n=int((d.action=='REFER').sum()),observed_references=int(d.ref_mAh.notna().sum()))

def adjudicate(archive,out):
    seal=json.loads((out/'blind_lock.json').read_text())
    if digest(out/'blind_decisions.csv')!=seal['blind_decisions_sha256'] or digest(archive)!=seal['tar_sha256']:
        raise ValueError('Frozen decision list or archive mismatch')
    df=pd.read_csv(out/'blind_decisions.csv',dtype={'filename_date':str});refs=[]
    with tarfile.open(archive) as tf:
        for path in df.path:
            src=pd.read_csv(tf.extractfile(path),usecols=[STEP,TYPE,Q])
            mask=(src[STEP]==3)&(src[TYPE]=='恒流放电'); ref=src.loc[mask,Q]
            done=(len(ref)>=2 and (src.loc[src.index>ref.index[-1],STEP]>3).any() and np.isfinite(ref.iloc[-1]) and ref.iloc[-1]>0)
            refs.append(float(ref.iloc[-1]) if done else np.nan)
    df['ref_mAh']=refs; df['grade']=np.where(df.ref_mAh.isna(),'unknown',np.where(df.ref_mAh>=10850,'qualified','below'))
    write_csv(df,out/'cell_results.csv')
    d=df[df.cohort_eligible]
    bygrade={}
    for g,wrong in [('below','PASS'),('qualified','FAIL')]:
        grp=d[d.grade==g]; k=int((grp.action==wrong).sum());n=len(grp)
        bygrade[g]=dict(**table(grp),wrong=k,empirical_error=k/n if n else None,upper_97_5_iid_only=bounds(k,n))
    dates=[]
    for date,group in d.groupby('filename_date'):
        dates.append(dict(filename_date=date,**table(group),below_n=int((group.grade=='below').sum()),
                     qualified_n=int((group.grade=='qualified').sum()),wrong_pass=int(((group.grade=='below')&(group.action=='PASS')).sum()),
                     wrong_fail=int(((group.grade=='qualified')&(group.action=='FAIL')).sum())))
    write_csv(pd.DataFrame(dates),out/'by_filename_date.csv')
    time_step=df.inferred_step_seconds
    result=dict(**seal,selected_records=table(df),raw_matches=int(df.raw_historical_match.sum()),
                signature_matches=int(df.rounded_historical_match.sum()),in_sample_duplicate=int(df.within_sample_repeat.sum()),
                scoped_records=table(d),invalid_charge=int((~d.valid_charge).sum()),filename_dates=len(dates),
                time_check=dict(n=int(time_step.notna().sum()),within_2_9_to_3_1=int(time_step.between(2.9,3.1).sum()),
                                median_seconds=float(time_step.median())),
                by_grade=bygrade,potential_skips=int((d.action!='REFER').sum()),observed_saved_by_this_rule=None,
                confirmed_original_pack_ids=None,confirmed_arrival_batch_ids=None,confirmed_cell_serials=None)
    (out/'public_summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['signature','score','census-score','adjudicate'])
    p.add_argument('archive',type=Path);p.add_argument('--out',type=Path,default=HERE/'public_results');a=p.parse_args()
    a.out.mkdir(exist_ok=True,parents=True)
    if a.mode=='signature':make_signatures(a.archive)
    elif a.mode in ('score','census-score'):score(a.archive,a.out,a.mode=='census-score')
    else:adjudicate(a.archive,a.out)
