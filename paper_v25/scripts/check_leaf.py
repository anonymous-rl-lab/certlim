"""Reconstruct the three published Leaf schedules directly from the frozen visit and action ledgers."""
import csv
import hashlib
from collections import Counter
from pathlib import Path
from check_capacity import read_table

ROOT = Path(__file__).resolve().parents[1]
LEAF = ROOT / 'evidence' / 'Leaf'


def read(relative_path):
    with (LEAF / relative_path).open(newline='') as stream:
        return list(csv.DictReader(stream))


def check(main, si):
    for manifest in ('LOCK.sha256', 'SHA256SUMS', 'results/blind.sha256'):
        file = LEAF / manifest
        for line in file.read_text().splitlines():
            digest, name = line.split(maxsplit=1)
            assert hashlib.sha256((file.parent / name).read_bytes()).hexdigest() == digest, name
    visits = read('results/traces.csv')
    def key(row):
        return (row['cell'], int(row['visit']))
    def act(value):
        if value > 24.375:
            return 'PASS'
        if value < 21.125:
            return 'FAIL'
        return 'REFER'
    by_visit = {key(row): row for row in visits}
    sealed = {key(row): row for row in read('results/actions.csv')}
    optional = [row for row in visits if int(row['visit']) % 2 == 0]
    assert len(by_visit) == len(visits) == 88 and len(set(row['cell'] for row in visits)) == 8
    assert set(sealed) == set(map(key, optional))
    for row in visits:
        assert row['reference_ok'] == row['charge_ok'] == 'True'
        assert row['grade'] == ('qualified' if float(row['reference_Ah']) >= 22.75 else 'below')
        assert row['same_visit'] == act(float(row['charge_Ah']))
        if key(row) in sealed:
            cell, visit = key(row)
            prior = by_visit[cell, visit - 1]
            assert prior['date'] < row['date']
            assert act(float(prior['reference_Ah'])) == sealed[key(row)]['previous'] == row['same_visit']
    def prior(row):
        return sealed[key(row)]['previous'] if key(row) in sealed else 'REFER'
    def current(row):
        return row['same_visit']
    table = read_table(main, '**TABLE III.')
    assert len(table) == 3
    for printed, (label, cohort, action) in zip(table, [
        ('Prior capacity, optional visits', optional, prior),
        ('Prior capacity, all visits', visits, prior),
        ('Same-visit charge, all visits', visits, current)], strict=True):
        decided = [row for row in cohort if action(row) != 'REFER']
        n = Counter(row['grade'] for row in cohort)
        d = Counter(row['grade'] for row in decided)
        assert all((action(row) == 'PASS') == (row['grade'] == 'qualified') for row in decided)
        hours = sum(float(row['reference_h']) for row in decided)
        assert printed == [label, f"{d['qualified']}/{n['qualified']}", f"{d['below']}/{n['below']}",
                           f'{len(decided)}/{len(cohort)}', f'{hours:.2f}']
    additions = [row for row in visits if prior(row) == 'REFER' and current(row) != 'REFER']
    assert len(additions) == 34 and all(key(row)[1] % 2 == 1 for row in additions)
    assert '34 additional decisions' in main and '34 additional decisions' in si
    all_hours = sum(float(row['reference_h']) for row in visits)
    assert f'{all_hours:,.2f}' in si
    for gen2, expected in [(False, (22,2,56,55)), (True,(10,8,0,0))]:
        pack = [row for row in visits if (row['cell'] == '2.1') == gen2]
        counts = [sum(row['grade']==grade and (not only_decided or current(row)!='REFER') for row in pack)
                  for grade in ('qualified','below') for only_decided in (False,True)]
        assert tuple(counts) == expected
    assert '2/22' in main and '0/56 and 0/32' in si


if __name__ == '__main__':
    check((ROOT/'TII_MAIN_MANUSCRIPT_v25.md').read_text(), (ROOT/'SUPPLEMENTARY_INFORMATION_v25.md').read_text())
    print('PASS: Leaf sealed protocols/actions, visit chronology, Table III, reference hours and pack denominators.')
