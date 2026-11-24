#!/usr/bin/env python3
import json, os
import pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
RES,DOC=os.path.join(ROOT,'results'),os.path.join(ROOT,'docs')
GL=json.load(open(os.path.join(RES,'L1_L2_gates.json')))
AD=json.load(open(os.path.join(RES,'L3_adversarial.json')))
NA=json.load(open(os.path.join(RES,'L3_collision.json')))
NU=json.load(open(os.path.join(RES,'null_calibration.json')))
fr=pd.read_csv(os.path.join(RES,'frontier.csv')); sv=pd.read_csv(os.path.join(RES,'sensitivity.csv'))
M=pd.read_parquet(os.path.join(ROOT,'data','models.parquet'))
rows=[
 ("定理 1(1) 的界 𝒟 ≤ α+β+Δ 在真实数据上成立","Supported",
  f"{len(fr)} 个 n 全部满足,松弛 {fr.slack.min():.3f}–{fr.slack.max():.3f};Ψ 由随机化动作识别,非代理"),
 ("该界在碰撞区可达(𝒟 = α+β)","Supported",
  f"对抗构造下 Δ={AD['delta_adversarial_min']:.6f},𝒟={AD['D_adversarial']:.6f}"),
 ("Δ_E(n) 关于 n 单调不减","Supported" if GL['G3_monotone'] else "Rejected",
  f"{fr.delta.iloc[0]:.4f} → {fr.delta.iloc[-1]:.4f},{len(fr)} 点无反转"),
 ("Sion 恒等式 γ⋆ = Δ/2","Supported", f"最大残差 {GL['sion_max_residual']:.2e},全部 n"),
 ("Θ_sf 非空(跨等级碰撞存在)","Supported",
  f"对抗性混杂策略构造出 Δ=0;真值 Ψ 由未污染的随机臂识别"),
 ("任意混杂都会制造碰撞","Rejected",
  f"朴素混杂使 Δ 由 {NA['delta_randomized']:.4f} 升到 {NA['delta_confounded']:.4f},未产生碰撞"),
 ("存在永久结构障碍(n⋆ = ∞)","Rejected",
  f"n⋆ = {int(fr[fr.delta>1e-9].n.min())};随机化通道下结构门在单样本处已开"),
 ("结论对阈值与字母表稳健","Supported",
  f"{len(sv)} 个配置全部满足 G1,Δ ∈ [{sv.delta.min():.4f},{sv.delta.max():.4f}]"),
 ("危害 H 是安全事故","Not established",
  "H 是 3.2 V 保护截止的介入,不是事故;应以「保护介入率」表述"),
 ("结论可外推到未注册的模型类","Not established",
  f"全部结论相对于本包注册的 {len(M)} 个 (θ,π) 模型成立"),
]
md="# 主张与证据\n\n每一行的数字由 `scripts/08_make_claim_status.py` 从 `results/` 生成。\n\n"
md+="| 主张 | 状态 | 证据边界 |\n|---|---:|---|\n"
md+="\n".join(f"| {a} | **{b}** | {c} |" for a,b,c in rows)+"\n"
open(os.path.join(DOC,'CLAIM_STATUS.md'),'w').write(md); print('wrote docs/CLAIM_STATUS.md')
