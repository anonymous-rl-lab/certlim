"""Recompute acquisition bounds, transfer geometry and design sensitivities."""
from itertools import product
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from scipy.optimize import linprog
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "NASA_chain_v2"
V21 = HERE.parent / "review_v21"
OUT = HERE / "results"
sys.path.insert(0, str(V21))
from run import make_banks, optimize
from legacy import h_extremes
from confidence import cs


def write(name, rows):
    pd.DataFrame(rows).to_csv(OUT / f"{name}.csv", index=False, float_format="%.13g")


def acquisition():
    fit = pd.read_csv(V21 / "results/comparison.csv").query("n == 5").set_index(["source","policy","method"])
    cut = pd.read_csv(V21 / "results/cutoff.csv").query("n == 5").set_index(["source","policy"])
    regs = pd.read_csv(V21 / "results/registration.csv")
    rows = []
    for row in regs.itertuples():
        item = {"source":row.source,"policy":row.policy,"safe":row.safe,"unsafe":row.unsafe,"unresolved":row.unresolved}
        if row.safe and row.unsafe:
            key = row.source,row.policy
            a,b = cut.loc[key],fit.loc[(*key,"lookup")]
            item.update(cutoff_U=a.D_upper,full_L=b.D_lower,
                        gain_L_pp=max(0,100*(b.D_lower-a.D_upper)),gain_U_pp=100*(b.D_upper-a.D_lower))
            if (*key,"LR") in fit.index:
                lr=fit.loc[(*key,"LR")]
                item.update(lr_L=lr.D_lower,lr_gap_U_pp=100*(b.D_upper-lr.D_lower))
                if lr.D_lower >= a.D_upper and b.D_lower > a.D_upper:
                    item["lr_gain_fraction_L"]=(lr.D_lower-a.D_upper)/(b.D_upper-a.D_lower)
        rows.append(item)
    write("procurement",rows)


def vertices(cells, split, grade):
    group=cells[(cells.split==split)&(cells.grade==grade)]
    assert group.qhi.eq(.5).all()
    points=np.array([[getattr(row,a+"0"),getattr(row,b+"1")]
                     for row in group.itertuples() for a,b in product(("lo","hi"),repeat=2)])
    return points[ConvexHull(points).vertices]


def directed_distance(source, target):
    # TV equals L1 in the two joint cutoff masses when the band mass is fixed.
    n=len(target)
    bound=np.vstack([np.c_[target.T,-np.eye(2)],np.c_[-target.T,-np.eye(2)]])
    objective=np.r_[np.zeros(n),1,1]
    distances=[]
    for point in source:
        sol=linprog(objective,A_ub=bound,b_ub=np.r_[point,-point],A_eq=[np.r_[np.ones(n),0,0]],
                    b_eq=[1],bounds=(0,None),method="highs")
        if not sol.success: raise RuntimeError(sol.message)
        distances.append(sol.fun)
    return max(distances)


def transfer():
    cells=pd.read_csv(BASE/"results/whole_cell_classes.csv")
    cert=pd.read_csv(BASE/"results/whole_cell_certificate.csv").set_index("scope")
    train,test=cert.loc["train14"],cert.loc["test14_frozen"]
    row=dict(source_delta=train.delta_test,target_delta=test.delta_test,
             unsafe_bound=test.unsafe_to_certify,safe_bound=test.safe_to_reject)
    for grade in ("S","U"):
        s,t=vertices(cells,"train",grade),vertices(cells,"test",grade)
        row[f"rho_{grade}"]=max(directed_distance(s,t),directed_distance(t,s))
    row["margin"]=row["source_delta"]-row["rho_S"]-row["rho_U"]
    assert 0 < row["margin"] <= row["target_delta"]
    write("transfer",[row])


def solve_five(safe,unsafe):
    s_grid,s_outer,_=make_banks(safe,5)
    u_grid,u_outer,_=make_banks(unsafe,5)
    cutoff=optimize(*[h_extremes(5,g.lo.min(),g.hi.max()) for g in (safe,unsafe)])[2]
    full=optimize(s_outer,u_outer)[2]
    upper=optimize(s_grid,u_grid)[2]
    assert -1e-8 < upper-full < 1e-7
    return dict(cutoff=cutoff,full=full,full_upper=upper,gain_pp=100*(full-cutoff))


def deletion():
    d=pd.read_csv(BASE/"results/legacy_grades.csv").query('policy=="skew_high"')
    rows=[]
    for cell in sorted(d.cell.unique()):
        subset=d[d.cell!=cell]
        vals=solve_five(subset[subset.grade=="S"],subset[subset.grade=="U"])
        rows.append(dict(deleted=cell,**vals))
    write("deletion",rows)


def regrade(data,context,voltage_weights):
    w=np.outer(voltage_weights,[.05,.20,.15,.60]).ravel()
    data=data.assign(voltage_bin=np.digitize(data[context],[3.55,3.70,3.85],right=True))
    rows=[]
    for (cell,stage),grp in data.groupby(["cell","stage"]):
        if len(grp)<150: continue
        ids=(4*grp.voltage_bin+grp.action-1).to_numpy()
        n=np.bincount(ids,minlength=16)
        y=np.bincount(ids,weights=(grp.Vend<=3.25),minlength=16)
        covered=n>=5
        lo=(w*covered*y/np.maximum(n,1)).reshape(4,4).sum(0)
        hi=lo+(w*(~covered)).reshape(4,4).sum(0)
        intervals=np.array([cs(int(k),int(h),int(stage),16) for k,h in zip(n,y)])
        cslo,cshi=w@intervals
        rows.append(dict(cell=cell,stage=stage,qhi=.75,lo=lo.sum(),hi=hi.sum(),
                         lo0=lo[:2].sum(),hi0=hi[:2].sum(),lo1=lo[2:].sum(),hi1=hi[2:].sum(),
                         cs_safe=cshi<=.15,cs_unsafe=cslo>=.35))
    return pd.DataFrame(rows)


def timing():
    d=pd.read_csv(BASE/"data/nasa_steps.csv.gz").sort_values(["cell","stage","step_k"])
    d["previous"]=d.groupby(["cell","stage"]).Vend.shift()
    d["action"]=d.I_med.round().clip(1,5).astype(int)
    original=d[(d.action<=4)&(d.V0<=4)]
    volt=np.digitize(original.loc[original.arm.str.startswith("uniform"),"V0"],[3.55,3.70,3.85],right=True)
    counts=np.bincount(volt,minlength=4)
    matched=original[original.previous<=4]
    rows=[]
    for name,column in (("matched_start","V0"),("matched_previous","previous")):
        table=regrade(matched,column,counts/counts.sum())
        safe=table[table.hi<=.15+1e-12]
        unsafe=table[table.lo>=.35-1e-12]
        rows.append(dict(context=name,retained_steps=len(matched),stages=len(table),safe=len(safe),unsafe=len(unsafe),
                         cs_safe=table.cs_safe.sum(),cs_unsafe=table.cs_unsafe.sum(),**solve_five(safe,unsafe)))
    write("timing",rows)
    sets=pd.read_csv(BASE/"results/legacy_confidence_sets.csv").query('policy=="skew_high"')
    arg=sets.loc[sets.hi.idxmin()]
    orig=pd.read_csv(BASE/"results/legacy_grades.csv")
    r=orig[(orig.cell==arg.cell)&(orig.stage==arg.stage)&(orig.policy==arg.policy)].iloc[0]
    write("grade_example",[dict(cell=r.cell,stage=r.stage,policy=r.policy,risk_lo=r.lo,risk_hi=r.hi,confidence_hi=arg.hi)])


if __name__=="__main__":
    OUT.mkdir(exist_ok=True)
    acquisition()
    transfer()
    deletion()
    timing()
