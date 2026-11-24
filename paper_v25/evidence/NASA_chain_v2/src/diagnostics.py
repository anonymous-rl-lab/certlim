from common import *
from scipy.stats import hypergeom
from itertools import product

def main():
    d=pd.read_csv(OUT/'whole_cell_classes.csv')
    train=d[(d.split=='train')&(d.grade!='?')]
    mapping=train.groupby(['arm','temp']).grade.agg(lambda x: x.iloc[0] if x.nunique()==1 else '?').to_dict()
    d['arm_prediction']=[mapping.get((a,t),'?') for a,t in zip(d.arm,d.temp)]
    write(d.sort_values('cell')[['cell','arm','temp','split','grade','arm_prediction']],'arm_only_cells')
    fs=pd.read_csv(OUT/'physical_stages.csv')
    stages=fs[(fs.split=='test')&(fs.grade!='?')].copy()
    br=pd.read_csv(OUT/'physical_blocks.csv').query('n==4')[['cell','stage']].drop_duplicates()
    stages=stages.merge(br,on=['cell','stage'])
    tr=fs[(fs.split=='train')&(fs.grade!='?')].groupby(['arm','temp']).grade.agg(lambda x:x.iloc[0] if x.nunique()==1 else '?').to_dict()
    stages['arm_prediction']=[tr.get((a,t),'?') for a,t in zip(stages.arm,stages.temp)]
    rows=[]
    for name,data in [('whole_cell_CS',d[d.split=='test']),('stage_monitor',stages)]:
        for grade_name,g in data[data.grade!='?'].groupby('grade'):
            lab=g.arm_prediction
            rows.append(dict(task=name,grade=grade_name,n=len(g),cells=g.cell.nunique(),correct=sum(lab==grade_name),opposite=sum((lab!='?')&(lab!=grade_name)),alert=sum(lab=='?')))
    write(rows,'arm_only_summary')
    # Preserve each benchmark's trace rows, stratum counts and lookup.
    # Compare rank-aligned observed blocks to exact random re-pairing of those rows.
    src=read_steps()
    grouped=src.groupby(['cell','stage'])
    src['previous']=grouped.Vend.shift();src['ordinal']=grouped.cumcount()
    src=src[src.previous.notna()&(src.ordinal%25!=0)&((src.ordinal//25)%2==1)].copy()
    src['a']=np.where(abs(src.I_med-1.5)<=.06,0,np.where(abs(src.I_med-3)<=.06,1,-1))
    src=src[src.a>=0].copy();src['strat']=2*src.a+(src.previous>3.55)
    src['h']=(src.Vend<=3.25).astype(int)
    if OUT.name=='fixed60': src['h']*=src.dur_s<=60
    raw=src.groupby(['cell','stage'])
    look=pd.read_csv(OUT/'frozen_physical_rules.csv')
    obs=pd.read_csv(OUT/'physical_stage_decisions.csv').query('validation=="locked_14"')
    detail=[]
    for (cell,stage,n),g in obs.groupby(['cell','stage','n']):
        v=raw.get_group((cell,stage));B=int(g.blocks.iloc[0]);k=n//4
        laws=[]
        for j in range(4):
            yy=v.loc[v.strat==j,'h'].to_numpy()[:B*k]
            assert len(yy)==B*k
            laws.append(hypergeom.pmf(np.arange(k+1),B*k,yy.sum(),k))
        lo=np.convolve(*laws[:2]);hi=np.convolve(*laws[2:])
        for row in g.itertuples():
            rule_tab=look[(look.n==n)&(look.method==row.method)].sort_values('state')
            p=np.outer(lo,hi).ravel() if row.method=='load_and_cutoff' else np.convolve(lo,hi)
            pc=p@rule_tab.certify;pr=p@rule_tab.reject
            detail.append(dict(cell=cell,stage=stage,n=n,grade=row.grade,method=row.method,blocks=B,paired_decisive=row.decisive,random_pair_decisive=pc+pr,paired_error=row.certify if row.grade=='U' else row.reject,random_pair_error=pc if row.grade=='U' else pr))
    q=pd.DataFrame(detail);write(q,'pairing_stages')
    cols=['paired_decisive','random_pair_decisive','paired_error','random_pair_error']
    v=q.groupby(['n','grade','method','cell'],as_index=False)[cols].mean().groupby(['n','grade','method'],as_index=False)[cols].mean()
    write(v,'pairing_summary')
if __name__=='__main__':main()
