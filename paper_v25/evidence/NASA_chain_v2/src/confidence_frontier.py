from common import *
from legacy import h_extremes
from extend import boundary_sample
from scipy.stats import binom

def main():
    f=pd.read_csv(OUT/'legacy_confidence_sets.csv',float_precision='round_trip')
    S,U=[f[f.grade==j] for j in ['S','U']]
    p,q=boundary_sample(S,'S'),boundary_sample(U,'U')
    exact=float(pd.read_csv(OUT/'confidence_summary.csv').query('scope=="legacy"').D_n1.iloc[0])
    rows=[];look=[]
    for n in pd.read_csv(OUT/'corrected_frontier.csv').n:
        sr,ur=[h_extremes(n,d.lo.min(),d.hi.max()) for d in [S,U]]
        c,r,hlo=rule(sr,ur)
        ends=[np.unique(np.r_[d.lo,d.hi]) for d in (S,U)]
        live=[binom.pmf(np.arange(n+1),n,v[:,None]) for v in ends]
        hhi=rule(*live)[2]
        st=states(n,4)
        fourhi=rule(lift(p,st),lift(q,st))[2] if n>1 else exact
        fourlo=hlo if n>1 else exact
        assert hlo<=hhi+1e-7 and fourlo<=fourhi+1e-7
        rows.append(dict(n=n,CS_safe=len(S),CS_unsafe=len(U),H_D_lower=hlo,H_D_upper=hhi,four_D_lower=fourlo,four_D_upper=fourhi))
        for k in range(n+1):look.append(dict(n=n,hits=k,certify=c[k],reject=r[k],alert=1-c[k]-r[k]))
    write(rows,'confidence_frontier');write(look,'confidence_cutoff_lookups')
if __name__=='__main__':main()
