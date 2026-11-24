"""Independent audit of the fixed primary list, reference capacity and model outputs."""
from pathlib import Path
from io import TextIOWrapper
import argparse,csv,hashlib,json,tarfile
import numpy as np,pandas as pd
from scipy.io import loadmat
from sklearn.ensemble import ExtraTreesRegressor
from frozen import HERE,features,digest

def run(mat,train_file,archive,output):
    spec=json.loads((HERE/'lock.json').read_text())
    if digest(mat)!=spec['original_mat_sha256'] or digest(train_file)!=spec['original_predictions_sha256']:
        raise ValueError('Historical source mismatch')
    raw=loadmat(mat)['unbalanced_data'][0,0]
    hist=pd.read_csv(train_file); train=hist.loc[hist.split=='train','record'].to_numpy()
    old=[]; xx=[]
    def stats(v,i,q):return [float(np.median(i)),float(v[-1]),float(q[-1]),len(v)]
    for j in train:
        v,i,q=[raw[k][j,0].ravel().astype(float) for k in ['Vp','Ip','Qp']]
        ft=features(v,i,q);xx.append([ft[k] for k in spec['features']]);old.append(stats(v,i,q))
    forest=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=8,max_features=1.,random_state=43,n_jobs=1)
    forest.fit(xx,raw['Capacity_labels'].ravel()[train]/15500)
    target=pd.read_csv(output/'cell_results.csv')
    source=[]; new=[]; derived=[];capacity=[]; endpoint_refs=[]
    with tarfile.open(archive) as tf:
        for row in target.itertuples(index=False):
            points=[]
            with TextIOWrapper(tf.extractfile(row.path),encoding='utf-8-sig') as stream:
                # Interpret numeric step numbers independently from the primary text filter.
                for r in csv.DictReader(stream):
                    points.append((int(r['工步号']),float(r['电压 (mV)']),float(r['电流 (mA)']),float(r['容量 (mAh)'])))
            a=np.array(points)
            v,i,q=a[a[:,0]==1,1:].T; vd,id_,qd=a[a[:,0]==3,1:].T
            assert len(qd)>=2 and np.any(a[a[:,0]==4])
            # Counter from machine; integration is an independent approximation using 3 s ticks.
            capacity.append(qd[-1]);derived.append(abs(np.trapezoid(id_,dx=3))/3600)
            endpoint_refs.append(vd[-1])
            ft=features(v,i,q);new.append([ft[k] for k in spec['features']]);source.append(stats(v,i,q))
    z=forest.predict(new);acts=np.where(z>spec['hi'],'PASS',np.where(z<spec['lo'],'FAIL','REFER'))
    assert np.array_equal(acts,target.action.to_numpy()) and np.array_equal(capacity,target.ref_mAh.to_numpy())
    ae=np.abs(np.asarray(capacity)-derived)
    def dist(array):
        arr=np.asarray(array); labels=['charge_median_current_mA','end_voltage_mV','charge_end_mAh','charge_rows']
        return {label:np.quantile(arr[:,n],[.05,.5,.95]).tolist() for n,label in enumerate(labels)}
    result=dict(target_rows=len(target),sha256_primary_cell_results=digest(output/'cell_results.csv'),
                absolute_score_delta_max=float(np.max(np.abs(z-target.score))),all_actions_reproduced=True,
                all_reference_capacities_reproduced=True,capacity_range_mAh=[min(capacity),max(capacity)],
                discharge_endpoint_mV_05_50_95=np.quantile(endpoint_refs,[.05,.5,.95]).tolist(),
                integrated_discharge_vs_counter_abs_error_mAh_50_95_max=np.quantile(ae,[.5,.95,1]).tolist(),
                label_agreement_integrated_discharge_at_10850=int(np.sum((np.array(capacity)>=10850)==(np.array(derived)>=10850))),
                original_train_05_50_95=dist(old),target_05_50_95=dist(source))
    (output/'independent_check.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('original_mat','original_predictions','public_tar'):p.add_argument(k,type=Path)
    p.add_argument('--out',type=Path,default=HERE/'public_results');a=p.parse_args();run(a.original_mat,a.original_predictions,a.public_tar,a.out)
