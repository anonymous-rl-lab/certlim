#!/usr/bin/env python3
"""Raw battery_alt CSVs -> data/missions.parquet (one row per discharge mission block)."""
import argparse, json, os, glob, sys, warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore')
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
MS=CFG['mission']
COLS=['time','mode','voltage_load','current_load','temperature_battery','mission_type']
GROUPS={'recommissioned_batteries':'recommissioned','regular_alt_batteries':'regular',
        'second_life_batteries':'second'}
def blocks(path):
    d=pd.read_csv(path,usecols=COLS,low_memory=False)
    for c in COLS:
        if c!='mode': d[c]=pd.to_numeric(d[c],errors='coerce')
    d=d[d['mode']==-1].dropna(subset=['current_load','voltage_load']).reset_index(drop=True)
    brk=(d.time.diff()>MS['gap_seconds'])|(d.mission_type.diff()!=0)
    d['blk']=brk.cumsum()
    g=d.groupby('blk').agg(t0=('time','min'),dur=('time',lambda s:s.max()-s.min()),
        I=('current_load','median'),I_max=('current_load','max'),
        V_min=('voltage_load','min'),V_med=('voltage_load','median'),
        T_max=('temperature_battery','max'),T_0=('temperature_battery','first'),
        T_med=('temperature_battery','median'),mt=('mission_type','first'),n=('time','size'))
    return g[g.n>=MS['min_points']].reset_index(drop=True)
def main(raw):
    out=[]
    for folder,grp in GROUPS.items():
        for f in sorted(glob.glob(os.path.join(raw,folder,'battery*.csv'))):
            b=blocks(f); b['pack']=os.path.basename(f)[:-4]; b['group']=grp; out.append(b)
    M=pd.concat(out,ignore_index=True)
    M['stage']=M.groupby('pack').t0.transform(lambda s: pd.qcut(s,4,labels=False,duplicates='drop'))
    M.to_parquet(os.path.join(ROOT,'data','missions.parquet'))
    print(f"mission 块 {len(M)}  包 {M.pack.nunique()}  regular {int((M.mt==1).sum())}  reference {int((M.mt==0).sum())}")
    print(M.groupby('group').agg(packs=('pack','nunique'),regular=('mt',lambda s:(s==1).sum()),
                                 reference=('mt',lambda s:(s==0).sum())).to_string())
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--raw',required=True); a=p.parse_args(); main(a.raw)
