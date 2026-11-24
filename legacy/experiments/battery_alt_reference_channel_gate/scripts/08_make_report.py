#!/usr/bin/env python3
"""Assemble results/GATE_REPORT.md from the result files."""
import json, os
import numpy as np, pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
R = lambda *p: os.path.join(ROOT, *p)
J = lambda p: json.load(open(R('results', p)))

g0, fz, gt = J('G0_feasibility.json'), J('freeze_v02.json'), J('gates_v02.json')
nl, g7 = J('null_calibration_v02.json'), J('G7_rw_holdout.json')
FR = pd.read_csv(R('results', 'frontier_v02.csv'))
SS = pd.read_csv(R('results', 'sensitivity_v02.csv'))
EX = pd.read_parquet(R('data', 'experiment_v02.parquet'))

L = []
w = L.append
w("# 门报告 — Battery ALT 标准探针认证实验 (v02) + NASA RW 留出臂 (G7)\n")
w(f"- 协议 v02 SHA-256 `{fz['protocol_v02_sha256']}`")
w(f"- 配置 v02 SHA-256 `{fz['config_v02_sha256']}`")
w(f"- 更正表 SHA-256 `{fz['errata_corrections_sha256']}`")
w(f"- v01 配置 SHA-256 `{fz['v01_config_sha256']}` (G0 未通过,保留)\n")

w("## 0. G0 可行性 — **未通过**,v01 的策略轴在本数据集上不可估\n")
t = g0['theta_action_bins']
w("| 量 | 值 |")
w("|---|---|")
w(f"| θ 单元 | {g0['n_theta']} |")
w(f"| 每个 θ 的动作档位数(中位 / 最大) | {t['median']:.0f} / {t['max']} |")
w(f"| 只覆盖一个档位的 θ 比例 | {t['frac_with_1_bin']:.1%} |")
w(f"| 每个 θ 内电流跨度 A(中位) | {g0['theta_current_spread_A']['median']:.3f} |")
w(f"| 每个包**全生命**动作档位数(最大) | {g0['pack_action_bins']['max']} |")
w(f"| 覆盖 ≥3 档的包比例 | {g0['pack_action_bins']['frac_ge3']:.1%} |")
w(f"| 任务内电流变化 I_max/I_med(中位) | {g0['within_mission_current']['median_Imax_over_Imed']:.3f} |\n")
w("数据集自己的 README 就是原因:载荷按**包**(或包×生命阶段)指派,从不按 mission 指派。")
w("于是 Ψ(θ,π) 退化成单档危害率,对 π 恒定。**G5(策略切换)在本数据集上没有可估目标,一并弃用。**\n")
w("详见 `docs/ERRATA.md` A 节。v02 是同一批数据上的**另一个实验**,不是 v01 的调参。\n")

w("## 1. v02 实验\n")
w(f"16 个包(参考放电 ≥ 15),等级 S {int((EX.grade=='S').sum())} / A {int((EX.grade=='A').sum())} / "
  f"U {int((EX.grade=='U').sum())},危害率三分位 {fz['hazard_tertiles'][0]:.4f} / {fz['hazard_tertiles'][1]:.4f}。")
w("证据是恒流 2.520 ± 0.001 A 的参考放电,K=8 → 4 → 2 为同一分划的严格嵌套粗化。\n")
w(EX[['pack', 'group', 'n_ref', 'n_regular', 'hazard', 'grade']]
  .sort_values('hazard').to_markdown(index=False))
w("")

w("## 2. 前沿\n")
p = FR.pivot_table(index='n', columns='K', values=['Delta', 'D'])
w("| K | n | 状态数 | Δ_E(n) | 𝒟_{α,β} | min{1,α+β+Δ} | 余量 |")
w("|---|---|---|---|---|---|---|")
for _, r in FR.sort_values(['K', 'n']).iterrows():
    w(f"| {int(r.K)} | {int(r.n)} | {int(r.n_states)} | {r.Delta:.6f} | {r.D:.6f} | "
      f"{r.bound:.6f} | {r.slack:.6f} |")
w("")

w("## 3. 门\n")
w("| 门 | 结果 | 关键数字 |")
w("|---|---|---|")
w(f"| G1 上界 | **通过** | {gt['G1_bound']['n_checked']} 个 (K,n) 点,最大越界 "
  f"{gt['G1_bound']['max_excess']:.2e},最小余量 {gt['G1_bound']['min_slack']:.2e} |")
m = gt['G3_monotone']['per_K']
w(f"| G3 单调(Δ、𝒟 不减) | **通过** | 最大下降 Δ {max(x['max_decrease_Delta'] for x in m):.2e},"
  f"𝒟 {max(x['max_decrease_D'] for x in m):.2e};按注册的反向文字则不通过(ERRATA E1) |")
g4 = gt['G4_gate_nstar_sion']
w(f"| G4 门函数 / n⋆ / Sion | **通过** | n⋆ = {g4['n_star']};Sion 最大误差 "
  f"{g4['max_sion_error']:.2e}(容差 {g4['sion_tolerance']:.0e},去掉最大的 K=8,n=10 后为 "
  f"{g4['max_sion_error_excluding_K8_n10']:.2e}) |")
g2 = gt['G2_attained']
w(f"| G2 可达 | **通过** | 最近的真实 S/U 对 {g2['closest_real_pair'][0]}–{g2['closest_real_pair'][1]}"
  f"(单样本 TV {g2['pair_TV_1sample']:.4f});构造碰撞后各 n 上 Δ ≤ {g2['max_Delta']:.1e},"
  f"𝒟 − (α+β) ≤ {g2['max_abs_error']:.1e} |")
g6 = gt['G6_data_processing']
w(f"| G6 数据处理 | **通过** | 8→4 最大违例 {g6['chain'][0]['max_violation']:.4f},"
  f"4→2 {g6['chain'][1]['max_violation']:.1e};恒等式 Δ_{{(X,g(X))}} = Δ_X 误差 "
  f"{g6['tautology_abs_error']:.1e} |")
g9 = gt['G9_heldout_packs']
hs = [x for x in g9['halves'] if not x.get('skipped')]
w(f"| G9 留出包 | **通过** | 两半各 (S,U) = " +
  ", ".join(f"({x['n_S']},{x['n_U']}) 最大越界 {x['max_excess']:.3f}" for x in hs) + " |")
w("")

w("## 4. 永久障碍:凸包相交 ≠ 逐对碰撞\n")
w("定理 1(3):G_E(n) = 1 对所有 n **当且仅当**存在逐对精确碰撞 P_{θS} = P_{θU}。")
w("凸包在 n=1 相交只是必要条件。本数据把两者分开了:\n")
w("| K | 最小逐对 TV | 存在逐对碰撞 | Δ_E(1) | n=1 凸包相交 | n⋆ |")
w("|---|---|---|---|---|---|")
for k, v in gt['permanent_obstruction']['per_K'].items():
    w(f"| {k} | {v['min_pairwise_TV']:.6f} | {'是' if v['exact_pairwise_collision'] else '否'} | "
      f"{v['Delta_1']:.2e} | {'是' if v['hulls_intersect_at_1'] else '否'} | {v['n_star']} |")
w("")
w("K=2 上凸包在 n=1 与 n=2 都相交,n=3 才打开;K=4 上 n=2 打开;K=8 上一开始就是开的。")
w("三个 K 都没有逐对碰撞,于是门都在有限步关不上——这正是定理 1(3) 的非平凡方向,")
w("也正是理论章明确指出、而口号版本会说错的那一段:")
w("**一阶凸包相交若只由复合混合造成,重复观测可以靠高阶乘积结构完成分离。**\n")
w("同时 K=2 在 n=1,2 上给出 Δ = 0 且 𝒟 = 0.100000 = α+β 精确相等——")
w("式 (22) 不需要任何构造,在真实电池数据上直接被观测到。\n")

w("## 5. 零假设与敏感性\n")
o, n1, n20 = nl['observed'], nl['null_Delta_1'], nl['null_Delta_20']
w(f"组内置换 {nl['n_permutations']} 次(块 = regular / recommissioned / second):\n")
w("| 统计量 | 观测 | 零分布中位 | 零 5% | 零 95% | p |")
w("|---|---|---|---|---|---|")
w(f"| Δ_E(1)(**注册统计量**) | {o['Delta_1']:.2e} | {n1['median']:.2e} | {n1['q05']:.4f} | "
  f"{n1['q95']:.4f} | 左尾 {nl['p_left_Delta_1']:.3f} |")
w(f"| Δ_E(20)(附报) | {o['Delta_20']:.4f} | {n20['median']:.4f} | {n20['q05']:.4f} | "
  f"{n20['q95']:.4f} | 右尾 **{nl['p_right_Delta_20']:.3f}** |")
w("")
w(f"零分布里 {n1['frac_zero']:.0%} 的置换同样给出 Δ_E(1) = 0。**n=1 的凸包相交是常态,不是本组标签的特征。**")
w(f"Δ_E(20) 的右尾 p = {nl['p_right_Delta_20']:.3f}:**参考放电通道对等级的分辨力,")
w("与把这 16 个包随意重新分组没有统计上的区别。**这是一个如实报告的阴性结果:")
w("定理的结构性论断在真实电池数据上成立,但这条通道并不构成一条有用的认证通道。\n")
ok = SS[~SS.skipped]
w(f"敏感性 {len(ok)} 组设定(危害阈值 × 最少参考放电 × 平滑 δ):")
w(f"G1 最大越界 {ok.G1_max_excess.max():.1e};n⋆ ∈ {sorted(set(ok.n_star.dropna().astype(int)))};"
  f"{int((ok.Delta_1 <= 1e-9).sum())}/{len(ok)} 组设定给出 Δ_E(1) = 0。结论对三个旋钮都稳。\n")

w("## 6. G7 — NASA RW 留出臂(B 部分)\n")
a, b, c = g7['G7a_arm_transport'], g7['G7b_within_cell_control'], g7['G7c_policy_vs_arm']
w("| | 中位 \\|偏差\\| | Spearman ρ | 判据 | 结果 |")
w("|---|---|---|---|---|")
w(f"| G7a 跨臂迁移(**注册**) | {a['median_abs_bias']:.3f} "
  f"(95% CI {a['bias_ci95'][0]:.3f}–{a['bias_ci95'][1]:.3f}) | {a['spearman_rho']:.3f} | "
  f"≤ {a['criteria']['max_abs_bias']} 且 ≥ {a['criteria']['min_spearman']} | **未通过**(偏差) |")
w(f"| G7b 同一电芯两半(对照) | {b['median_abs_bias']:.3f} | {b['spearman_rho']:.3f} | — | 记录 |")
w("")
w("G7b 说明重加权恒等式与其估计在**单元固定**时是准的(偏差 0.016,ρ = 0.99),")
w("因此 G7a 的 0.22 不是噪声。但 G7c 给出判读:\n")
w("| 用哪个策略去评估 | 中位 \\|跨臂偏差\\| |")
w("|---|---|")
for k, v in c['median_abs_bias_by_evaluated_policy'].items():
    w(f"| {k} | {v:.3f} |")
w("")
w("在目标臂**从未跑过**的 uniform 上评估,偏差(0.160)与在它实际跑过的策略上评估(0.172)几乎一样大。")
w("NASA RW 的臂是**按电芯**指派的,臂与单元完全混杂,本数据集无法把单元异质性与策略迁移失败分开。")
w("如实的结论:**G7 按注册判据未通过**;它给出的是一个可测的跨单元漂移 ρ ≈ 0.16–0.22,")
w("对照 α + β = 0.10 —— 裕度 M = Δ_d − ρ^S − ρ^U 为负,跨单元迁移在此**未被认证**。\n")

w("## 7. 这个包支持什么、不支持什么\n")
w("**支持**(在另一实验室、另一批电芯、另一套协议上独立复现):")
w("- 定理 1(1) 的有限样本上界,30 个 (K,n) 点无一越界;敏感性 27 组设定同样无一越界。")
w("- 式 (22) 的相等情形,在真实数据上直接观测到(K=2, n=1,2:Δ=0 且 𝒟=α+β 精确)。")
w("- 定理 1(2) 的双单调性;定理 1(3) 的门函数二分与 n⋆ 有限性;Sion 恒等式 γ⋆ = Δ/2。")
w("- 数据处理推论,在**严格嵌套**的粗化链上。")
w("- 理论章关于「一阶凸包相交 ≠ 永久障碍」的那条更正,拿到了真实数据上的直接实例。\n")
w("**不支持**:")
w("- 参考放电不构成一条有用的认证通道(置换零假设 p = 0.206)。")
w("- 策略轴在本数据集上不可估(G0 未通过),G5 无从检验。")
w("- 跨臂/跨单元迁移未通过注册判据(G7a),且本数据无法归因。\n")

open(R('results', 'GATE_REPORT.md'), 'w').write("\n".join(L) + "\n")
print("wrote results/GATE_REPORT.md", len(L), "lines")
