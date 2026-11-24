"""Cross-check the printed outcomes from source records, reference tests and the 56-state rule."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'evidence'
def read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))

def read_table(doc, marker):
    part = doc.split(marker,1)[1].split('\n\n',2)[1]
    return [[cell.strip() for cell in row.strip('|').split('|')] for row in part.splitlines()[2:]]

def check_nasa(main, si):
    probs = read(SRC/'NASA_chain_v2/results/legacy_confidence_sets.csv')
    row = next(r for r in probs if (r['cell'],r['stage'],r['policy'])==('RW10','53','skew_low'))
    safe = [r for r in probs if r['grade']=='S']
    assert len(safe)==26 and all(r['policy']=='skew_low' for r in safe)
    counts = Counter(r['policy'] for r in probs if r['grade']=='U')
    assert counts['skew_low']==37 and sum(counts.values())-counts['skew_low']==213
    assert row['grade']=='U'
    q, low, high = (float(row[k]) for k in ('qhi','lo0','lo1'))
    law = [1-q-low,low,q-high,high]
    states = [r for r in read(SRC/'review_v21/results/lookups.csv')
              if (r['source'],r['policy'],r['method'],r['n'])==('confidence','pooled','lookup','5')]
    assert len(states)==56
    actions = dict.fromkeys(['certify','reject','alert'],0.)
    for r in states:
        counts = [int(r[k]) for k in ('low_no','low_cut','high_no','high_cut')]
        mass = math.factorial(5)*math.prod(p**c/math.factorial(c) for p,c in zip(law,counts))
        for k in actions: actions[k] += mass*float(r[k])
    assert math.isclose(sum(actions.values()),1.,abs_tol=1e-10)
    ratio=actions['certify']/(actions['certify']+actions['reject'])
    assert all(f'{100*v:.4f}%' in si for v in actions.values())
    assert all(f'{100*v:.2f}%' in main for v in [*actions.values(),ratio])
    return actions

def check_capacity(main,si):
    cetl = SRC/'CETL/results'
    rows = [r for r in read(cetl/'predictions.csv') if r['split']=='test']
    table = read_table(main,'**TABLE II.')
    hours = []
    for j,channel in enumerate(('A','B')):
        freq = Counter(int(r[channel]) for r in rows)
        fp = sum(int(r[channel])==2 and r['grade']=='False' for r in rows)
        fr = sum(int(r[channel])==1 and r['grade']=='True' for r in rows)
        nf = sum(r['grade']=='False' for r in rows); nq = len(rows)-nf
        row = table[j]
        assert row[:2] == [f'Complete {len(rows):,}, {channel}', ' / '.join(f'{freq[i]:,}' for i in (2,1,0))]
        assert row[2].split()[0]==f'{fp}/{nf}' and row[3].split()[0]==f'{fr}/{nq}'
        hours.append(sum(float(r['discharge_h']) for r in rows if int(r[channel])!=0))
    assert f'{hours[1]-hours[0]:.2f}' in main and f'{60*(hours[1]-hours[0])/len(rows):.2f}' in si
    for line in read_table(si,'**Table S19.'):
        tag,ch=line[0].split()
        scope='complete' if tag=='Complete' else 'refer_on_charge_invalid'
        pair = {r['grade']:r for r in read(cetl/'audit_all_heldout.csv') if r['channel']==ch and r['scope']==scope}
        num = lambda g,k:f'{int(pair[g][k]):,}/{int(pair[g]["n"]):,}'
        assert line[1:]==[num(g,'errors')+f' ({100*float(pair[g]["error_U"]):.4f})' for g in ('F','P')]+[
                 num(g,'decisions') for g in ('F','P')]+[f'{100*min(float(r["decisive"]) for r in pair.values()):.2f}']
    assert len(table) == 4
    for j, (scope, title) in enumerate([('complete','Complete'), ('refer_on_charge_invalid','All')]):
        for k, channel in enumerate(('A','B')):
            grades = {row['grade']:row for row in read(cetl/'audit_all_heldout.csv')
                      if row['scope']==scope and row['channel']==channel}
            below, qual = grades['F'], grades['P']
            total = sum(int(row['n']) for row in grades.values())
            fp, fr = int(below['errors']), int(qual['errors'])
            passed = int(qual['decisions']) - fr + fp
            rejected = int(below['decisions']) - fp + fr
            actions = f'{passed:,} / {rejected:,} / {total-passed-rejected:,}'
            errs = [f"{int(row['errors'])}/{int(row['n']):,} ({100*float(row['error_U']):.4f})" for row in (below,qual)]
            mind = min(float(row['decisive']) for row in grades.values())
            assert table[2*j+k] == [f'{title} {total:,}, {channel}', actions, *errs, f'{100*mind:.2f}']
    scopes = [('public_results','ReLiB primary, B'),('public_census','ReLiB census, B')]
    primary=set()
    for j,(scope,label) in enumerate(scopes):
        path=SRC/'ReLiB'/scope
        seal=json.loads((path/'blind_lock.json').read_text())
        assert hashlib.sha256((path/'blind_decisions.csv').read_bytes()).hexdigest()==seal['blind_decisions_sha256']
        data=read(path/'cell_results.csv')
        outcomes={(r['path'],r['action'],r['ref_mAh']) for r in data}
        if j: assert primary<=outcomes
        else: primary=outcomes
        good=[r for r in data if r['ref_mAh'] and float(r['ref_mAh'])>=10850]
        low=[r for r in data if r['ref_mAh'] and float(r['ref_mAh'])<10850]
        assert not low
        rejects=sum(r['action']=='FAIL' for r in good)
        actions=' / '.join(f'{sum(r["action"]==a for r in data):,}' for a in ('PASS','FAIL','REFER'))
        assert f'{rejects:,}' in main and f'{len(good):,}' in main
        if j:
            assert f'{100*rejects/len(good):.2f}%' in main
            assert f'{len(data):,}' in main and f'{len(data)-len(good)}' == '2'
            assert all(value in main for value in actions.split(' / ')[1:])
        srow=read_table(si,'**Table S20.')[j]
        assert srow[1:]==[f'{len(data):,}',f'{len(good):,} / 0 / {len(data)-len(good)}',actions,f'{100*rejects/len(good):.2f}']

def check(main,si):
    check_nasa(main,si)
    check_capacity(main,si)

if __name__=='__main__':
    check((ROOT/'TII_MAIN_MANUSCRIPT_v25.md').read_text(),(ROOT/'SUPPLEMENTARY_INFORMATION_v25.md').read_text())
    print('PASS: two NASA review computations, CETL and ReLiB action/error denominators, discharge cost, Tables II/S19/S20.')
