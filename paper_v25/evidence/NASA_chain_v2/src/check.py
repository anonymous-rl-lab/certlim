from common import *
from hashlib import sha256
from scipy.stats import binom

def main():
    z=pd.read_csv(OUT/'corrected_frontier.csv');g=pd.read_csv(OUT/'legacy_grades.csv')
    assert len(z)==11 and len(g)==1539
    assert (g.grade.value_counts().reindex(['S','U','?']).to_numpy()==[443,528,568]).all()
    assert np.all(g.lo<=g.hi+1e-10)
    assert np.allclose(g.lo0+g.lo1,g.lo) and np.allclose(g.hi0+g.hi1,g.hi)
    assert np.all(z.four_D_lower<=z.four_D_upper+1e-8)
    assert np.all(z.four_D_lower>=z.cutoff_D-1e-8)
    assert abs(z.iloc[0].four_delta_lower-.20100531797)<1e-7
    lookup=pd.read_csv(OUT/'cutoff_lookup_all_orders.csv')
    ss=g[g.grade=='S'];uu=g[g.grade=='U']
    for k,row in z.set_index('n').iterrows():
        t=lookup[lookup.n==k].sort_values('hits')
        for d,j,lo,hi in [(ss,'S',ss.lo.min(),ss.hi.max()),(uu,'U',uu.lo.min(),uu.hi.max())]:
            laws=binom.pmf(np.arange(k+1),k,np.linspace(lo,hi,1001)[:,None])
            assert (laws@(t.reject if j=='S' else t.certify)).max()<=.05+1e-8
            assert (laws@(t.reject+t.certify)).min()>=row.cutoff_D-1e-8
    for p in [OUT,OUT/'fixed60']:
        b=pd.read_csv(p/'physical_blocks.csv');f=pd.read_csv(p/'physical_stages.csv')
        assert f.cell.nunique()==28 and set(f.split)=={'train','test'}
        assert f.groupby('cell').split.nunique().max()==1
        nn=b.groupby(['cell','stage','n']).size().rename('B').reset_index().merge(f,on=['cell','stage'])
        assert np.all(nn.B*(nn.n//4)==(nn[[f'n1_{j}' for j in range(4)]].min(axis=1)//(nn.n//4))*(nn.n//4))
        for file in ['ordered_lookups.csv','frozen_physical_rules.csv']:
            v=pd.read_csv(p/file);assert abs((v.certify+v.reject+v.alert)-1).max()<2e-8 and v[['certify','reject','alert']].min().min()>-1e-8
        v=pd.read_csv(p/'physical_stage_decisions.csv').query('validation=="locked_14"')
        assert set(v.cell).isdisjoint(f.query('split=="train"').cell)
    cert=pd.read_csv(OUT/'whole_cell_certificate.csv').set_index('scope')
    assert cert.loc['registered_28','D_min']>.1 and cert.loc['test14_frozen','unsafe_to_certify']>.05
    assoc=pd.read_csv(OUT/'legacy_block_test.csv').iloc[0];assert assoc.n_cells==28 and assoc.replicates==500
    print('PASS: grade bounds, 11-order frontier, lookup feasibility, physical block counts, cell splits, both endpoints, rule normalization, confidence and transfer.')
if __name__=='__main__':main()
