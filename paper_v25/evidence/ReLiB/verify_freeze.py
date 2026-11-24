from pathlib import Path
import argparse, json, sys, shutil
from tempfile import TemporaryDirectory
import numpy as np, pandas as pd, sklearn
from scipy.io import loadmat
from sklearn.ensemble import ExtraTreesRegressor
base=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description="Reconstruct frozen CETL-B in a temporary directory and check released bytes.")
parser.add_argument("cetl_mat",type=Path)
raw=parser.parse_args().cetl_mat
scratch=TemporaryDirectory()
dest=Path(scratch.name)
shutil.copyfile(base/'frozen.py',dest/'frozen.py')
sys.path.insert(0,str(dest))
from frozen import Rule, features, digest, trace_digest, valid
old=base.parent/'CETL'
assert digest(raw)==json.loads((base/'lock.json').read_text())['original_mat_sha256']
data=loadmat(raw)['unbalanced_data'][0,0]
labels=data['Capacity_labels'].ravel()
p=pd.read_csv(old/'results/predictions.csv')
f=json.loads((old/'results/summary.json').read_text())['fits'][1]
def trace(index):
    return tuple(data[k][index,0].ravel().astype(float) for k in ['Vp','Ip','Qp'])
matrices={}; hashes=set()
for j in range(len(labels)):
    v,i,q=trace(j);hashes.add(trace_digest(v,i,q))
    if valid(v,i,q):
        feat=features(v,i,q);matrices[j]=[feat[k] for k in f['features']]
X=np.array([matrices[j] for j in p.record]); train=(p.split=='train').to_numpy()
model=ExtraTreesRegressor(n_estimators=200,min_samples_leaf=8,max_features=1.,random_state=43,n_jobs=1)
model.fit(X[train],labels[p.record[train].to_numpy()]/15500)
nodes={k:[] for k in ('left','right','feature','threshold','value')}; roots=[];offset=0
for tree in model.estimators_:
    t=tree.tree_;roots.append(offset)
    for side,children in [('left',t.children_left),('right',t.children_right)]:
        nodes[side].extend(np.where(children>=0,children+offset,children).tolist())
    nodes['feature'].extend(t.feature.tolist());nodes['threshold'].extend(t.threshold.tolist())
    nodes['value'].extend(t.value[:,0,0].tolist());offset+=t.node_count
np.savez_compressed(dest/'forest.npz',roots=roots,**nodes)
(dest/'historical_trace_hashes.txt').write_text('\n'.join(sorted(hashes))+'\n')
lock=dict(rule='CETL-B',features=f['features'],lo=f['lo'],hi=f['hi'],capacity_mAh_inclusive=10850,
          nameplate_mAh=15500,upper_error_budget_each=.05,simultaneous_alpha=.05,
          component_sha256={k:digest(dest/k) for k in ['forest.npz','frozen.py','historical_trace_hashes.txt']},
          original_mat_sha256=digest(raw),original_predictions_sha256=digest(old/'results/predictions.csv'),
          original_generator_sha256=digest(old/'run_pulsefree.py'),original_threshold_file_sha256=digest(old/'results/summary.json'),
          build_sklearn=sklearn.__version__)
(dest/'lock.json').write_text(json.dumps(lock,indent=2)+'\n')
rule=Rule();sc=rule.predict_matrix(X)
assert np.array_equal(model.predict(X),sc)
err=max(abs(sc-p.B_score));assert err<6e-12
actions={0:'REFER',1:'FAIL',2:'PASS'}
for s,a in zip(sc,p.B): assert rule.action(s)==actions[a]
ids=[j for j in range(len(labels)) if j//20 in set(p.loc[p.split=='test','block'])]
audit=json.loads((old/'results/audit.json').read_text())
oldact=dict(zip(p.loc[p.split=='test','record'],p.loc[p.split=='test','B']))
oldact.update({int(k):int(v) for k,v in audit['additional_actions_without_reference_QC']['B'].items()})
keys=[j for j in ids if j in matrices];new=dict(zip(keys,map(rule.action,rule.predict_matrix([matrices[j] for j in keys]))))
routes=[new.get(j,'REFER') for j in ids]
assert all(r==actions[oldact.get(j,0)] for r,j in zip(routes,ids))
auditout=dict(original_training_rows=int(train.sum()),original_calibration_rows=int((p.split=='cal').sum()),
       reference_rows=len(p),identical_binary64_scores_to_reconstructed_sklearn=len(p),
       max_abs_difference_vs_published_rounded_scores=err,identical_published_actions=len(p),
       complete_test_rows=int((p.split=='test').sum()),charge_only_heldout_routes_matched=len(ids),
       charge_only_heldout_actions={k:routes.count(k) for k in actions.values()},
       feature_count=len(f['features']),trees=len(roots),total_nodes=offset,
       equality_thresholds_refer=all(rule.action(a)=='REFER' for a in (f['lo'],f['hi'])),
       known_raw_records=len(labels),unique_historical_charge_hashes=len(hashes),
       measured_new_cell_outcomes=None,work_order_confirmed_skips=None)
(dest/'equivalence.json').write_text(json.dumps(auditout,indent=2)+'\n')
print(json.dumps(auditout))

for name in ['forest.npz','lock.json','historical_trace_hashes.txt','equivalence.json']:
    assert (dest/name).read_bytes()==(base/name).read_bytes(), name
scratch.cleanup()
print('PASS: reconstructed forest, rule lock, trace hashes and equivalence results match released bytes.')
