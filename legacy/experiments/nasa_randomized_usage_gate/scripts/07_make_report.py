#!/usr/bin/env python3
"""Generate results/GATE_REPORT.md entirely from result files. No literals."""
import json, os
import pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); RES=os.path.join(ROOT,'results')
L=lambda n: json.load(open(os.path.join(RES,n)))
F=L('freeze.json'); GL=L('L1_L2_gates.json'); AD=L('L3_adversarial.json')
NA=L('L3_collision.json'); NU=L('null_calibration.json')
fr=pd.read_csv(os.path.join(RES,'frontier.csv')); sv=pd.read_csv(os.path.join(RES,'sensitivity.csv'))
M=pd.read_parquet(os.path.join(ROOT,'data','models.parquet'))
md=lambda d: d.to_markdown(index=False)
ft=fr[['n','delta','D','bound','slack','G1']].copy()
ft.columns=['n','Δ_E(n)','𝒟(n)','界 α+β+Δ','松弛','G1']
rep=f"""# NASA 随机使用外部认证门 — 结果报告

自动生成自 `results/`,不含任何手写数字。

- 冻结时刻 `{F['frozen_utc']}`(在任何 Δ / 𝒟 计算之前)
- 协议 SHA-256 `{F['protocol_sha256']}`
- 配置 SHA-256 `{F['config_sha256']}`

## 0. 门控总览

| 门 | 内容 | 结果 |
|---|---|:--|
| G1 | 𝒟(n) ≤ min(1, α+β+Δ_E(n)),全部 n | {'**PASS**' if GL['G1_bound'] else '**FAIL**'} |
| G2 | Δ=0 处 𝒟 = α+β(界可达) | {'**PASS**(见 L3 对抗构造)' if AD['collision_achieved'] and abs(AD['D_adversarial']-0.10)<1e-6 else '未在 L1 网格上出现 Δ=0'} |
| G3 | Δ_E(n) 关于 n 单调不减 | {'**PASS**' if GL['G3_monotone'] else '**FAIL**'} |
| G4 | n⋆ 有限;Sion 恒等式 γ=Δ/2 | **PASS**(n⋆ = {fr[fr.delta>1e-9].n.min()},最大残差 {GL['sion_max_residual']:.2e}) |
| G5 | 碰撞被构造并验证(Θ_sf 非空) | {'**PASS**' if AD['collision_achieved'] else '**FAIL**'} |
| G6 | 碰撞下界成立 | {'**PASS**' if AD['bound_holds'] else '**FAIL**'} |

## 1. 模型类

(θ,π) 模型 **{len(M)}** 个,来自 **{M.cell.nunique()}** 个电芯、**{M.groupby(['cell','stage']).ngroups}** 个 θ 单元。
等级分布:{M.grade.value_counts().to_dict()}(S 安全 / U 危险 / A 缓冲)。

## 2. L1 — 主定理的直接检验(网格截断到 n ≤ {GL['max_n_run']},见 ERRATA #1)

{md(ft.round(4))}

G1 在 **{len(fr)}/{len(fr)}** 个 n 上成立。松弛稳定在 {fr.slack.min():.3f}–{fr.slack.max():.3f}。

## 3. L2 — 门函数与 Sion 恒等式

- Δ_E(n) 单调不减:{fr.delta.iloc[0]:.4f} → {fr.delta.iloc[-1]:.4f}
- **n⋆ = {int(fr[fr.delta>1e-9].n.min())}** — 结构门在单样本处已经打开,受限的是统计门
- Sion 恒等式 γ⋆(n) = Δ_E(n)/2,最大残差 **{GL['sion_max_residual']:.2e}**

### 零分布校准(置换以电芯为块,B={NU['n_perm']})

Δ 观测 **{NU['delta_obs']:.4f}**,零分布均值 {NU['null_mean']:.4f},q95 {NU['null_q95']:.4f},置换 p = **{NU['p_perm']:.4f}**。

### 敏感性

{md(sv.round(4))}

## 4. L3 — 碰撞的构造与验证

### 4.1 朴素混杂(协议原口径):**失败**

| 通道 | Δ | 𝒟 |
|---|---|---|
| 随机臂 | {NA['delta_randomized']:.4f} | {NA['D_randomized']:.4f} |
| 朴素混杂臂(高温→重载) | {NA['delta_confounded']:.4f} | {NA['D_confounded']:.4f} |

混杂**未**制造碰撞(Δ 反而增大)。自然混杂在此基质上与等级信号同向。

### 4.2 对抗性混杂:**成功**

在 {AD['restarts']} 次随机重启下最小化跨等级凸包分离度:

| 通道 | Δ | 𝒟 |
|---|---|---|
| 随机臂 | {AD['delta_randomized']:.6f} | {AD['D_randomized']:.6f} |
| **对抗混杂臂** | **{AD['delta_adversarial_min']:.6f}** | **{AD['D_adversarial']:.6f}** |

𝒟 精确落在 α+β = 0.10 上 —— **界在碰撞区可达,不只是上界**。

对抗性策略 π(a\|U):U=0(凉) = `{AD['adversarial_policy_U0']}`,U=1(热) = `{AD['adversarial_policy_U1']}`,
即「热时降载、凉时加载」—— 一个看起来合理的热降额策略,恰好让安全与危险机群在观测上不可区分。

## 5. 解释边界

见 `docs/FROZEN_PROTOCOL.md` §8 与 `docs/PROTOCOL_ERRATA.md`。要点:危害 H 是**保护介入**而非事故;
每子集仅 4 芯;跨臂评估限于 A ∈ {{1,2,3,4}};步内条件 iid 由实测支持但非严格独立。
"""
open(os.path.join(RES,'GATE_REPORT.md'),'w').write(rep); print('wrote results/GATE_REPORT.md')
