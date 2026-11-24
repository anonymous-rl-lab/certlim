from common import *
from physical import pmfs, per_stage, summarize
from itertools import product
from scipy.optimize import linprog

def fit_model(s,u,edges,tiebreak):
    k=s.shape[1];L=np.r_[s,u]
    A=list(np.r_[np.c_[u,np.zeros_like(u),np.zeros(len(u))],np.c_[np.zeros_like(s),s,np.zeros(len(s))],np.c_[-L,-L,np.ones(len(L))],np.c_[np.eye(k),np.eye(k),np.zeros(k)]])
    b=list(np.r_[np.full(len(L),.05),np.zeros(len(L)),np.ones(k)])
    for i,j in edges:
        row=np.zeros(2*k+1);row[j]=1;row[i]=-1
        A.append(row);b.append(0.)
        A.append(np.r_[np.zeros(k),-row[:k],0]);b.append(0.)
    x=solve(np.r_[np.zeros(2*k),-1],np.array(A),np.array(b))
    t=x[-1]
    if tiebreak:
        A.append(np.r_[np.zeros(2*k),-1]);b.append(-t+1e-9)
        x=solve(np.r_[-s.mean(axis=0),-u.mean(axis=0),0],np.array(A),np.array(b))
    return x[:k],x[k:2*k],t
def main():
    f=pd.read_csv(OUT/'physical_stages.csv');b=pd.read_csv(OUT/'physical_blocks.csv')
    output=[];lookup=[]
    ok=f[(f.grade!='?')&(f[[f'n1_{j}' for j in range(4)]].min(axis=1)>=5)]
    for n in [4,8]:
        probs=np.array([pmfs(row,n//4)[0] for row in ok[[f'p1_{j}' for j in range(4)]].to_numpy()])
        width=n//2+1;edges=[]
        for i,j in product(range(width),repeat=2):
            key=i*width+j
            if i+1<width:edges.append((key,key+width))
            if j+1<width:edges.append((key,key+1))
        for split in ['locked_14','LOCO_28']:
            folds=[list(f[f.split=='test'].cell.unique())] if split=='locked_14' else [[c] for c in sorted(f.cell.unique())]
            for test in folds:
                train=~ok.cell.isin(test);S=probs[train&(ok.grade=='S')];U=probs[train&(ok.grade=='U')]
                feed=b[b.cell.isin(test)&(b.n==n)&(b.grade!='?')]
                for mode,e,tie in [('plain_tiebreak',[],True),('ordered',edges,False),('ordered_tiebreak',edges,True)]:
                    c,r,t=fit_model(S,U,e,tie)
                    if len(feed):
                        g=per_stage(feed,{'load_and_cutoff':(c,r,t)});g['method']=mode;g['validation']=split;output.append(g)
                    if split=='locked_14':
                        for i in range(len(c)):lookup.append(dict(n=n,method=mode,state=i,certify=c[i],reject=r[i],alert=1-c[i]-r[i],training_D=t))
    d=pd.concat(output)
    write(d,'ordered_stage_decisions');write(lookup,'ordered_lookups')
    write(summarize(d,'missing_only')+summarize(d,'conditional95'),'ordered_summary')
if __name__=='__main__':main()
