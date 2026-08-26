#!/usr/bin/env python3
"""G0 feasibility audit of the v01 (theta,pi) design.

The v01 protocol assumed a per-mission assigned action A (5 current bins) with
within-theta variation, so that Psi(theta,pi) = sum_a pi(a) P(H | theta, a) would
be a non-trivial function of the policy pi.  This script measures the actual
action support inside each theta and decides G0.  It writes results/G0_feasibility.json
and does NOT modify the frozen v01 config.
"""
import json, os
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CFG = json.load(open(os.path.join(ROOT, 'config', 'registered.json')))
BINS = CFG['action_bins_A']
MS = CFG['mission']

M = pd.read_parquet(os.path.join(ROOT, 'data', 'missions.parquet'))
R = M[M.mt == 1].copy()
R['A'] = pd.cut(R.I, BINS, labels=False)

# --- within-theta = (pack, stage) action support -----------------------------
g = R.groupby(['pack', 'stage'])
th = g.agg(n=('I', 'size'), Imin=('I', 'min'), Imax=('I', 'max'),
           Imed=('I', 'median'), nbin=('A', 'nunique'))
th['spread'] = th.Imax - th.Imin
th['nbin5'] = g.A.apply(lambda s: int((s.value_counts() >= 5).sum()))

# --- within-pack (pooling all life stages) -----------------------------------
gp = R.groupby('pack')
pk = gp.agg(n=('I', 'size'), nbin=('A', 'nunique'))
pk['nbin5'] = gp.A.apply(lambda s: int((s.value_counts() >= 5).sum()))

# --- within-mission current variation ----------------------------------------
ratio = (R.I_max / R.I)

out = dict(
    design='v01 (theta=(pack,stage), pi over 5 current bins)',
    n_theta=int(len(th)), n_packs=int(R.pack.nunique()), n_missions=int(len(R)),
    theta_action_bins={
        'median': float(th.nbin.median()), 'max': int(th.nbin.max()),
        'frac_with_1_bin': float((th.nbin == 1).mean()),
        'median_bins_with_ge5': float(th.nbin5.median()),
        'max_bins_with_ge5': int(th.nbin5.max())},
    theta_current_spread_A={
        'median': float(th.spread.median()), 'p75': float(th.spread.quantile(.75)),
        'max': float(th.spread.max())},
    pack_action_bins={'median': float(pk.nbin.median()), 'max': int(pk.nbin.max()),
                      'frac_ge3': float((pk.nbin >= 3).mean())},
    within_mission_current={'median_Imax_over_Imed': float(ratio.median()),
                            'p95_Imax_over_Imed': float(ratio.quantile(.95))},
    dataset_readme_statement=(
        'regular_alt_batteries: cycled at the same load level or load range throughout '
        'lifetime; recommissioned_batteries: cycled at different load levels at varying '
        'life stages; second_life_batteries: constant current. '
        'i.e. the load is assigned per pack (or per pack x life stage), never per mission.'),
)

# G0 criterion, registered here explicitly: the policy axis is estimable only if a
# majority of theta units support >=3 action bins with >=5 missions each.
crit = {'rule': 'median over theta of (#action bins with >=5 missions) >= 3',
        'observed': out['theta_action_bins']['median_bins_with_ge5']}
out['G0'] = dict(criterion=crit,
                 passed=bool(crit['observed'] >= 3),
                 consequence=('Psi(theta,pi) is constant in pi by construction; the '
                              'policy axis, and with it G5 (policy switch), is not '
                              'estimable on this dataset.'))
json.dump(out, open(os.path.join(ROOT, 'results', 'G0_feasibility.json'), 'w'), indent=2)

print(f"theta 单元 {out['n_theta']}  包 {out['n_packs']}  regular mission {out['n_missions']}")
print(f"每个 theta 的动作 bin 数: 中位 {out['theta_action_bins']['median']:.0f}  "
      f"最大 {out['theta_action_bins']['max']}  只有1个bin的比例 "
      f"{out['theta_action_bins']['frac_with_1_bin']:.3f}")
print(f"每个 theta 内电流跨度(A): 中位 {out['theta_current_spread_A']['median']:.3f}  "
      f"最大 {out['theta_current_spread_A']['max']:.3f}")
print(f"每个 pack 全生命周期动作 bin 数: 中位 {out['pack_action_bins']['median']:.0f}  "
      f"最大 {out['pack_action_bins']['max']}  >=3 个bin的比例 "
      f"{out['pack_action_bins']['frac_ge3']:.3f}")
print(f"任务内电流变化 I_max/I_med: 中位 {out['within_mission_current']['median_Imax_over_Imed']:.3f}")
print(f"\nG0 判据 {crit['rule']}: 观测 {crit['observed']:.1f} -> "
      f"{'PASS' if out['G0']['passed'] else 'FAIL'}")
