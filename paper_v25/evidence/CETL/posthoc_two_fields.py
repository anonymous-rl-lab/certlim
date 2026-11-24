from pathlib import Path
import sys
import numpy as np, pandas as pd
from scipy.io import loadmat
from scipy.stats import beta
from sklearn.ensemble import ExtraTreesRegressor
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.resolve()))
from run_pulsefree import thresholds, act
p=pd.read_csv(root/'results/predictions.csv')
if len(sys.argv) != 2:
 raise SystemExit('Usage: python posthoc_two_fields.py path/to/CETL-data.mat')
mat=loadmat(sys.argv[1])['unbalanced_data'][0,0]
ids=p.record.to_numpy();lab=mat['Capacity_labels'].ravel()[ids].astype(float)
x=np.array([[float(mat['Vp'][j,0].flat[0]),float(mat['Qp'][j,0].flat[-1])] for j in ids])
tr=(p.split=='train').to_numpy();ca=(p.split=='cal').to_numpy();te=(p.split=='test').to_numpy()
g=lab>=10850
for name,fs in [('published A control',[0]),('audit start V + final Q',[0,1])]:
 model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=8,max_features=1.,random_state=43,n_jobs=1)
 model.fit(x[tr][:,fs],lab[tr]/15500)
 sc=model.predict(x[:,fs]);lo,hi=thresholds(ca,g,sc); a=act(sc,lo,hi)
 if name.startswith('published'):
  assert (p.A==a).all()
 print(name,'thresholds',lo,hi,'actions',np.bincount(a[te]),'hours',p.loc[te&(a!=0),'discharge_h'].sum())
 for grade in (False,True):
  sel=te&(g==grade);yy=a[sel];err=int((yy==(1 if grade else 2)).sum());n=len(yy)
  print('grade',grade,'n',n,'errors',err,'upper',beta.ppf(.975,err+1,n-err),'decisions',(yy!=0).sum(),'rate',(yy!=0).mean())
 print('records comparison',pd.crosstab(p.loc[te,'B'],a[te]).to_dict())
