from common import *
from legacy import banks,h_extremes
from itertools import product
from scipy.spatial.distance import cdist

def boundary_sample(d,kind):
    # Each selected completion belongs to the class, yielding upper bounds.
    # Include easy as well as difficult rates; an easy end can bind decisiveness.
    edge='hi' if kind=='S' else 'lo'
    parts=[]
    for _,g in d.groupby('policy'):
        z=g.sort_values(edge,ascending=kind!='S')
        parts.extend([z.head(4),z.tail(2)])
    g=pd.concat(parts).drop_duplicates()
    return np.unique(banks(g,product([0.,1.],repeat=2)),axis=0)
def main():
    f=pd.read_csv(OUT/'legacy_grades.csv',float_precision='round_trip')
    # CSV bounds are rounded on disk. Rebuild inputs at full precision.
    from legacy import build
    f=build(read_steps())
    ss,uu=[f[f.grade==g] for g in ['S','U']]
    h=pd.read_csv(OUT/'legacy_H_all_orders.csv');q=pd.read_csv(OUT/'legacy_four_symbol.csv').set_index('n')
    S,U=boundary_sample(ss,'S'),boundary_sample(uu,'U')
    out=[];look=[]
    for v in h.itertuples():
        n=v.n;st=states(n,4)
        s,u=lift(S,st),lift(U,st)
        c,r,t=rule(h_extremes(n,ss.lo.min(),ss.hi.max()),h_extremes(n,uu.lo.min(),uu.hi.max()))
        for k in range(n+1): look.append(dict(n=n,hits=k,certify=c[k],reject=r[k],alert=1-c[k]-r[k]))
        d_hi=rule(s,u)[2];sep_hi=separation(s,u)
        d_lo=t;sep_lo=v.delta_lower
        if n in q.index:
            row=q.loc[n];d_hi=min(d_hi,row.D_missing_upper);d_lo=max(t,row.D_missing_lower)
            if n==1: sep_lo=sep_hi=row.delta_robust_exact
            else: sep_hi=min(sep_hi,row.delta_midpoint)
        assert d_lo<=d_hi+1e-7 and sep_lo<=sep_hi+1e-7
        out.append(dict(n=n,cutoff_D=t,four_D_lower=d_lo,four_D_upper=d_hi,max_action_gain_pp=100*(d_hi-t),four_delta_lower=sep_lo,four_delta_upper=sep_hi))
        print(out[-1],flush=True)
    write(out,'corrected_frontier');write(look,'cutoff_lookup_all_orders')
if __name__=='__main__':main()
