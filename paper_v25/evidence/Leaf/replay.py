"""Replay scheduled certification on eight intact Stanford donor-pack cells."""
import argparse
import hashlib
import io
import json
import re
import warnings
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from openpyxl import load_workbook

SHA = 'a4952be5b9d960c57b208a523b90ef9923f65ee92767b46b6b1b88560a62c98c'
LO, GRADE, HI = 21.125, 22.75, 24.375

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def plan(path):
    if sha(path) != SHA:
        raise ValueError('Published archive checksum mismatch')
    records = {}
    with zipfile.ZipFile(path) as z:
        for f in z.namelist():
            if not f.endswith('.xlsx') or Path(f).name.startswith('._'):
                continue
            match = re.search(r'\(1_1_([12])_([1-4])\).*\((20\d\d-\d\d-\d\d) (\d\d_\d\d_\d\d)\)', f)
            if not match: raise ValueError(f)
            a,b,date,tm=match.groups()
            cell=a+'.'+b
            folder=re.search(r'Cell ([12])p([1-4])',f)
            if folder and '.'.join(folder.groups())!=cell:raise ValueError(f)
            key=cell,date,tm
            if key in records and z.read(records[key])!=z.read(f): raise ValueError('Duplicate changed file: '+f)
            records[key]=f
    d=pd.DataFrame([dict(cell=k[0],date=k[1],time=k[2],file=f) for k,f in sorted(records.items())])
    d['visit']=d.groupby('cell').cumcount()+1
    return d

def sheet(w,name):
    s=w[name]
    s.reset_dimensions()
    it=iter(s.values)
    return pd.DataFrame(it,columns=next(it))

def read_trace(args):
    path, row, blind=args
    with zipfile.ZipFile(path) as z:
        buf=z.read(row['file'])
    warnings.filterwarnings('ignore',message='Workbook contains no default style')
    w=load_workbook(io.BytesIO(buf),read_only=True,data_only=True)
    d=sheet(w,'TestData')
    d['stage']=d.StepType.ne(d.StepType.shift()).cumsum()
    groups=[(g.StepType.iloc[0],g) for _,g in d.groupby('stage',sort=False)]
    cc=[i for i,(k,g) in enumerate(groups) if k=='ConstCurrentCharge']
    # Keep the first 3->4 V charge: if invalid, automatically refer.
    record=dict(row,public_sha256=hashlib.sha256(buf).hexdigest(),charge_Ah=np.nan,charge_ok=False)
    empty=dict(reference_Ah=np.nan,reference_h=np.nan,reference_ok=False,ref_report_Ah=np.nan,
               integration_Ah=np.nan,discharge_start_V=np.nan,discharge_end_V=np.nan)
    cutoff=cc[0] if cc else -1
    if cutoff<0:
        return {**record,**empty}
    reset=[g for k,g in groups[:cutoff] if k=='ConstCurrentDischarge']
    end=cutoff+1 if cutoff+1<len(groups) and groups[cutoff+1][0]=='ConstVoltageCharge' else cutoff
    g=groups[end][1]
    curr=groups[cutoff][1]['SampleCurrent(mA)'].median()/1000
    endv=g['SampleVoltage(mV)'].iloc[-1]/1000
    charge=g['Capacity(mAh)'].iloc[-1]/1000
    resetv=reset[-1]['SampleVoltage(mV)'].iloc[-1]/1000 if reset else np.nan
    charge_ok=abs(resetv-3.)<=.03 and abs(endv-4.)<=.02 and abs(curr-1.55)<=.0775 and np.isfinite(charge) and charge>0
    record.update(charge_Ah=charge,charge_ok=bool(charge_ok),charge_end_V=endv,initial_endpoint_V=resetv)
    if blind and row['visit']%2==0:
        return {**record,**empty}
    after=[g for k,g in groups[end+1:] if k=='ConstCurrentDischarge']
    if not after:
        return {**record,**empty}
    g=after[0]
    v=g['SampleVoltage(mV)'].to_numpy(float)/1000
    t=pd.to_timedelta(g['SampleTime']).dt.total_seconds().to_numpy(float)
    current=-g['SampleCurrent(mA)'].to_numpy(float)/1000
    raw=g['Capacity(mAh)'].iloc[-1]/1000
    sm=sheet(w,'CycleStatistics')
    rpt=sm.loc[sm.CycleNumber.eq(g.CycleCount.iloc[0]),'TotalDischargeCapacity(mAh)']
    rpt=rpt.iloc[0]/1000 if len(rpt) else np.nan
    ah=float(np.trapezoid(current,t)/3600)
    elapsed=(t[-1]-t[0])/3600
    ok=charge_ok and v[0]>=3.95 and abs(v[-1]-3.)<=.03 and abs(np.median(current)-1.55)<=.0775 and np.isfinite(ah) and raw>0 and abs(raw-ah)<=max(.05,.01*raw) and abs(rpt-raw)<=.01 and min(np.diff(t))>=0
    return dict(record,reference_Ah=raw,reference_h=elapsed,reference_ok=bool(ok),
                ref_report_Ah=rpt,integration_Ah=ah,discharge_start_V=v[0],discharge_end_V=v[-1])

def action(x,ok):
    if not ok or not np.isfinite(x):return 'REFER'
    if x>HI:return 'PASS'
    if x<LO:return 'FAIL'
    return 'REFER'

def score(traces):
    prior={}
    decisions=[]
    for r in traces:
        if r['visit']%2:
            prior[r['cell']]=r
            continue
        prev=prior[r['cell']]
        decisions.append(dict(cell=r['cell'],visit=r['visit'],date=r['date'],anchor_date=prev['date'],
                              prior_Ah=prev['reference_Ah'],prior_ok=prev['reference_ok'],
                              current_charge_Ah=r['charge_Ah'],charge_ok=r['charge_ok'],
                              previous=action(prev['reference_Ah'],prev['reference_ok']),
                              same_visit=action(r['charge_Ah'],r['charge_ok'])))
    return pd.DataFrame(decisions)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',choices=['score','adjudicate'])
    ap.add_argument('archive',type=Path)
    ap.add_argument('out',type=Path)
    args=ap.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    d=plan(args.archive)
    d.to_csv(args.out/'visits.csv',index=False)
    with ProcessPoolExecutor(max_workers=6) as pool:
        rows=list(pool.map(read_trace,[(args.archive,r,args.mode=='score') for r in d.to_dict('records')]))
    blind=args.out/'actions.csv'
    if args.mode=='score':
        score(rows).to_csv(blind,index=False,float_format='%.15g')
        (args.out/'blind.sha256').write_text(sha(blind)+'  actions.csv\n')
        print('Sealed',len(rows),'visits.')
    else:
        assert sha(blind)==(args.out/'blind.sha256').read_text().split()[0]
        actions=pd.read_csv(blind,dtype={'cell':str})
        assert actions.to_csv(index=False,float_format='%.12g')==score(rows).to_csv(index=False,float_format='%.12g')
        t=pd.DataFrame(rows)
        t['grade']=np.where(~t.reference_ok,'unknown',np.where(t.reference_Ah>=GRADE,'qualified','below'))
        t['same_visit']= [action(a,b) for a,b in zip(t.charge_Ah,t.charge_ok)]
        t.to_csv(args.out/'traces.csv',index=False)
        out=actions.merge(t[['cell','visit','grade','reference_Ah','reference_h']],on=['cell','visit'],validate='one_to_one')
        out.to_csv(args.out/'paired.csv',index=False)
        print('Checked',len(out),'pairs.',t.grade.value_counts().to_dict())

if __name__=='__main__':
    main()
