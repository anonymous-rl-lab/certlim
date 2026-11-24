"""Read-only CETL-B inference. Input is the original charge-side full trace."""
from pathlib import Path
import hashlib
import json
import numpy as np

HERE = Path(__file__).resolve().parent
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def trace_digest(v, i, q):
    return hashlib.sha256(b''.join(np.asarray(a, dtype='<f8').tobytes() for a in (v, i, q))).hexdigest()

def valid(v, i, q):
    return (len(v) >= 2 and len(v) == len(i) == len(q)
            and all(np.isfinite(a).all() for a in (v, i, q)) and v.min() > 0)

# Feature function copied verbatim from the locked generator below.
def features(v,i,q):
    out={'initial_mv':v[0],'charge_samples':len(v),'final_q':q[-1],'range_q':np.ptp(q)}
    for f in (0,.1,.25,.5,.75,.9,1):
        j=round(f*(len(v)-1));out[f'v_{f}']=v[j];out[f'i_{f}']=i[j]
    for threshold in (3300,3350,3400,3450,3500,3550,3600):
        js=np.flatnonzero(v>=threshold)
        out[f'first_s_{threshold}']=int(js[0]*3) if len(js) else -1
        out[f'q_{threshold}']=q[js[0]] if len(js) else -1
    for k,a in [('v',v),('i',i)]:
        out.update({k+'_mean':np.mean(a),k+'_sd':np.std(a),k+'_min':np.min(a),k+'_max':np.max(a)})
    return out

class Rule:
    def __init__(self):
        self.spec = json.loads((HERE / 'lock.json').read_text())
        for name, expected in self.spec['component_sha256'].items():
            if digest(HERE / name) != expected:
                raise ValueError('Frozen component hash mismatch: ' + name)
        with np.load(HERE / 'forest.npz', allow_pickle=False) as archive:
            self.nodes = dict(archive)

    def predict_matrix(self, rows):
        x = np.asarray(rows, dtype=np.float32)
        trees = self.nodes
        scores = np.zeros(len(x))
        for root in trees['roots']:
            pos = np.full(len(x), root)
            while True:
                active = np.flatnonzero(trees['left'][pos] >= 0)
                if not len(active):
                    break
                node = pos[active]
                left = x[active, trees['feature'][node]] <= trees['threshold'][node]
                pos[active] = np.where(left, trees['left'][node], trees['right'][node])
            scores += trees['value'][pos]
        return scores / len(trees['roots'])

    def action(self, score):
        if score > self.spec['hi']:
            return 'PASS'
        if score < self.spec['lo']:
            return 'FAIL'
        return 'REFER'

    def infer(self, v, i, q):
        if not valid(v, i, q):
            return None, 'REFER'
        f = features(v, i, q)
        score = float(self.predict_matrix([[f[k] for k in self.spec['features']]])[0])
        return score, self.action(score)
