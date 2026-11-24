"""Independent ZIP/XML verification of archived phase counters, masks, actions and hours."""
import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd
import numpy as np

N = {'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
     'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def direct(outer, path):
    with zipfile.ZipFile(io.BytesIO(outer.read(path))) as book:
        wb=ET.fromstring(book.read('xl/workbook.xml'))
        rid=next(x.get('{'+N['r']+'}id') for x in wb.findall('.//x:sheet',N) if x.get('name')=='CycleStatistics')
        rel=next(x.get('Target') for x in ET.fromstring(book.read('xl/_rels/workbook.xml.rels')) if x.get('Id')==rid)
        sheet=ET.fromstring(book.read(rel.lstrip('/') if rel.startswith('/') else 'xl/'+rel))
        strings=[]
        if 'xl/sharedStrings.xml' in book.namelist():
            for item in ET.fromstring(book.read('xl/sharedStrings.xml')):
                strings.append(''.join(t.text or '' for t in item.iter('{'+N['x']+'}t')))
        rows=[]
        for row in sheet.findall('.//x:row',N):
            values={}
            for c in row.findall('x:c',N):
                v=c.find('x:v',N);text=v.text if v is not None else ''.join(t.text or '' for t in c.findall('.//x:t',N))
                values[''.join(k for k in c.attrib['r'] if k.isalpha())]=strings[int(text)] if c.get('t')=='s' else text
            rows.append(values)
        hdr=rows[0]
        for row in rows[1:]:
            x={hdr[k]:v for k,v in row.items()}
            if str(x['CycleNumber'])=='2':
                return (float(x['TotalChargeCapacity(mAh)'])/1000,
                        float(x['TotalDischargeCapacity(mAh)'])/1000,
                        pd.Timedelta(x['TotalDischargeTime(Sec)']).total_seconds()/3600)
        return np.nan,np.nan,np.nan

def assign(x):
    if x>24.375:return 'PASS'
    if x<21.125:return 'FAIL'
    return 'REFER'

def measures(p,action):
    rows=[]
    for grade,wrong in [('qualified','FAIL'),('below','PASS')]:
        g=p[p.grade==grade]; acts=g[action]
        rows.append(dict(grade=grade,n=len(g),cells=g.cell.nunique(),packs=g.pack.nunique(),
                         pass_n=int((acts=='PASS').sum()),fail_n=int((acts=='FAIL').sum()),refer_n=int((acts=='REFER').sum()),
                         wrong=int((acts==wrong).sum()),decisive=int((acts!='REFER').sum()),hours=float(g.loc[acts.ne('REFER'),'reference_h'].sum())))
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument('archive',type=Path);p.add_argument('out',type=Path)
    a=p.parse_args()
    t=pd.read_csv(a.out/'traces.csv',dtype={'cell':str})
    b=pd.read_csv(a.out/'paired.csv',dtype={'cell':str})
    t['pack']=np.where(t.cell=='2.1','Leaf Gen 2','Leaf Gen 1')
    assert t[['cell','date']].duplicated().sum()==0
    b=b.merge(t[['cell','visit','pack']],on=['cell','visit'],validate='one_to_one')
    with zipfile.ZipFile(a.archive) as author:
        stats=[direct(author,k) for k in t.file]
    t[['summary_c','summary_d','summary_h']]=stats
    ok=t[t.reference_ok]; e=(ok.summary_d-ok.reference_Ah).abs().max(); h=(ok.summary_h-ok.reference_h).abs().max()
    c=(t[t.charge_ok].summary_c-t.loc[t.charge_ok,'charge_Ah']).abs().max()
    assert e<.01 and c<.01 and h<.025
    for x in b.itertuples():
        g=t[t.cell.eq(x.cell)]
        odd=g[g.visit.eq(x.visit-1)].iloc[0];ev=g[g.visit.eq(x.visit)].iloc[0]
        assert odd.date<ev.date and x.previous==(assign(odd.summary_d) if odd.reference_ok else 'REFER')
        assert x.same_visit==(assign(ev.summary_c) if ev.charge_ok else 'REFER')
        if ev.reference_ok:
            assert x.grade==('qualified' if ev.summary_d>=22.75 else 'below')
    compare=b.groupby(['pack','cell','grade','previous','same_visit'],as_index=False).agg(n=('date','size'),discharge_h=('reference_h','sum'))
    compare.to_csv(a.out/'by_cell_pack.csv',index=False)
    first=b.groupby('cell',sort=False).head(1)
    time_h=lambda df,mask:float(df.loc[mask,'reference_h'].sum())
    grade_b=b[b.grade!='unknown']
    data=dict(actual_sources=2,cells=int(t.cell.nunique()),date_range=[t.date.min(),t.date.max()],distinct_visits=len(t),optional=len(b),
              anchors=len(t)-len(b),reference_known_on_optional=len(grade_b),unknown_optional=int(b.grade.eq('unknown').sum()),
              optional_primary=measures(b,'previous'),optional_secondary=measures(b,'same_visit'),
              first_optional_primary=measures(first,'previous'),same_visit_all=measures(t,'same_visit'),
              total_discharge_h=time_h(t,t.reference_ok),eligible_discharge_h=time_h(b,b.grade.ne('unknown')),
              early_discharge_h_primary=time_h(b,b.previous.ne('REFER')&b.grade.ne('unknown')),
              unique_pairs_action_diff=int(b.previous.ne(b.same_visit).sum()),full_cohort_handled=int(b.previous.ne('REFER').sum()),
              primary_grade_events_by_pack=b.groupby(['pack','grade']).size().to_dict(),
              max_deviation_archive_step_Ah=float(e),max_deviation_archive_charge_Ah=float(c),max_deviation_archive_step_h=float(h),
              max_integration_gap_Ah=float((ok.reference_Ah-ok.integration_Ah).abs().max()))
    data['primary_grade_events_by_pack']={' / '.join(k):v for k,v in data['primary_grade_events_by_pack'].items()}
    (a.out/'summary.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))

if __name__=='__main__':
    main()
