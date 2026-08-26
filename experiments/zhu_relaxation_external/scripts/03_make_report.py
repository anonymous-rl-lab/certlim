#!/usr/bin/env python3
"""Generate the v01.1 report entirely from saved result files."""
from __future__ import annotations

import json
import os

import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(ROOT, "results")


def load_csv(name):
    return pd.read_csv(os.path.join(RES, name))


def load_json(name):
    with open(os.path.join(RES, name), encoding="utf-8") as handle:
        return json.load(handle)


def markdown(frame, columns=None):
    selected = frame[columns] if columns else frame
    selected = selected.copy()
    headers = [str(column).replace("|", "\\|") for column in selected.columns]
    rows = []
    for values in selected.itertuples(index=False, name=None):
        rows.append([("" if pd.isna(value) else str(value)).replace("|", "\\|")
                     for value in values])
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
        *("| " + " | ".join(row) + " |" for row in rows),
    ])


summary = load_json("summary.json")
freeze = load_json("freeze.json")
registered = load_json("as_registered_gates.json")
corrected = load_json("corrected_diagnostics.json")
domains = load_csv("domains.csv")
deltas = load_csv("delta_menus.csv")
paired = load_csv("paired_menu_nulls.csv")
pairing = load_csv("relax_pairing_summary.csv")
pairwise = load_csv("pairwise_vs_hull.csv")
leave = load_csv("leave_one_domain.csv")
geometry_null = load_csv("geometry_permutation_summary.csv")
support = load_csv("support_sensitivity.csv")
thresholds = load_csv("threshold_sensitivity.csv")
transfer = load_csv("transfer_legacy.csv")
nesting = load_csv("nesting_check.csv")
bootstrap = load_json("low_support_bootstrap_summary.json")
raw_reproduction = load_json("raw_feature_reproduction.json")
eol_audit = load_json("eol_sensitivity_audit.json")
eol_path = os.path.join(RES, "eol_sensitivity_summary.csv")
eol = pd.read_csv(eol_path) if os.path.exists(eol_path) else None


gate_rows = []
for name, item in registered.items():
    if name == "overall":
        continue
    gate_rows.append({
        "gate": name,
        "nominal": item["nominal_pass"],
        "inferential_status": item["status"],
        "validity": item["validity"],
    })

k4 = deltas[deltas.K == summary["registered_primary_K"]]
k8 = deltas[deltas.K == 8]
k4_pair = pairing[pairing.K == summary["registered_primary_K"]].iloc[0]
k8_pair = pairing[pairing.K == 8].iloc[0]
geo4 = geometry_null[geometry_null.K == summary["registered_primary_K"]].set_index("metric")
geo8 = geometry_null[geometry_null.K == 8].set_index("metric")
low = leave[(leave.K == 8) & (leave.dropped_safe_domain == "NCA_T35_C0.5")].iloc[0]

eol_section = ""
if eol is not None:
    primary = eol[(eol.window == 11) & (eol.factor == 0.5) & (eol.persistence_k == 3)]
    eol_section = f"""
## 8. 冻结 EOL 3×3×3 敏感性

已执行 {eol_audit['variants']} 个端点变体；主设置逐电芯复现 =
{eol_audit['all_primary_endpoints_reproduced']}。相对主设置，域等级变化数的最大值为
{eol_audit['maximum_domain_grade_changes']}。

主设置的三种分辨率：

{markdown(primary.round(4))}

完整 27×3 表见 `results/eol_sensitivity_summary.csv`，逐电芯端点见
`results/eol_sensitivity_cells.csv`。
"""

report = f"""# Zhu 2022 电压弛豫外部认证门 — v01.1 纠偏报告

本报告由结果文件自动生成。冻结协议和冻结配置均未改写。

- 冻结时刻：`{freeze['frozen_utc']}`
- 协议 SHA-256：`{freeze['protocol_sha256']}`
- 配置 SHA-256：`{freeze['config_sha256']}`
- 注册主分辨率：K={summary['registered_primary_K']}

## 0. 裁决

**注册结论：{registered['overall']['status']}**  
**事后纠偏层：{corrected['overall']['status']}**

这两个层次不得合并成一个布尔 `overall_pass`。v01 的原始结果完整保存在
`results/legacy_v01/`。

{markdown(pd.DataFrame(gate_rows))}

## 1. 数据完整性

- 电芯数：{summary['n_cells']}
- 有 EOL@90：{summary['n_with_eol90']}
- 进入风险分类：{summary['n_labelled']}
- 剔除中断周期：{summary['aborted_cycles_removed']}
- Spearman(EOL@90,EOL@95)：{summary['eol90_eol95_spearman']:.4f}
- 域身份对 log10(EOL) 的 eta²：{summary['eta_squared_domain']:.4f}
- 原始 CSV 重提取：{raw_reproduction['status']}，最大数值差
  {raw_reproduction['max_numeric_absolute_difference']:.3g}

{markdown(domains.round(4))}

## 2. 注册主分析：K=4

注册 K=4 下，最小逐对 TV 为 {summary['registered_K4']['min_pairwise_tv']:.4f}，
但凸包 Delta 为 {summary['registered_K4']['hull_delta']:.4f}：**所有逐对均分离，
复合凸包却发生精确碰撞**。该逐对—凸包差的置换 p=
{geo4.loc['pairwise_minus_hull','p_upper']:.4f}。这是注册分辨率上的事后几何诊断，
不是原冻结门之一。

{markdown(k4.round(4))}

域内弛豫配对置换实际执行 {int(k4_pair.n_permutations)} 次：观测增益
{k4_pair.observed_gain:+.4f}，置换 p={k4_pair.p_upper:.4f}，注册 G3 为
**{registered['G3_P3_channel_gain']['status']}**。

## 3. K=8 分辨率敏感性：逐对几何与凸包几何分离

K=8 下，最小逐对 TV 为 {summary['exploratory_K8']['min_pairwise_tv']:.4f}，
凸包 Delta 为 {summary['exploratory_K8']['hull_delta']:.4f}，比值
{summary['exploratory_K8']['pairwise_over_hull']:.2f}×。这是**冻结的分辨率敏感性结果**；
逐对—凸包对比本身属于事后诊断。

K=4/K=8 全局行置换校准：

{markdown(geometry_null.round(4))}

K=8 绝对 Delta 的 p={geo8.loc['hull_delta','p_upper']:.4f}，未建立总体分离；
逐对减凸包差的 p={geo8.loc['pairwise_minus_hull','p_upper']:.4f}，支持“逐对距离
可显著高估复合可分离度”这一经验诊断。

{markdown(pairwise[pairwise.K == 8].drop(columns=['K', 'hull_delta']).round(4))}

## 4. 新通道、冗余管线与置换对照

K=8 时，加入弛豫列的表观增益为
{float(k8.set_index('menu').loc['summary_relax','delta'] - k8.set_index('menu').loc['summary','delta']):+.4f}；
加入同维数确定性派生列的管线增益为
{float(k8.set_index('menu').loc['summary_derived','delta'] - k8.set_index('menu').loc['summary','delta']):+.4f}。
弛豫增益没有超过该管线底线；域内配对置换 p={k8_pair.p_upper:.4f}。

结论是：**当前管线下，弛豫通道的额外增益尚未建立**。这不是“弛豫通道
没有信息”的证伪结论。各菜单独立压缩，故该对照同时包含分区改变效应。

{markdown(pairing.round(4))}

配对域标签零分布：

{markdown(paired.round(4))}

## 5. 严格嵌套粗化仅作为代码恒等式

{markdown(nesting.round(4))}

该单调性由同一 K=8 分区的确定性粗化保证，是实现检查，不作为原注册
`g_summary` 门的外部验证。

## 6. 低支持域杠杆

删除 `{low.dropped_safe_domain}`（n={int(low.n_cells)}）后，K=8 Delta 从
{low.delta_full:.4f} 升至 {low.delta_without:.4f}，置换 p=
{geo8.loc['leave_one_shift','p_upper']:.4f}。

固定量化器的域内自助结果：shift 中位数 {bootstrap['shift_median']:.4f}，
95% 区间 [{bootstrap['shift_q025']:.4f},{bootstrap['shift_q975']:.4f}]。
它说明有限样本复合几何对低支持成员高度敏感，不能直接外推为总体定理。

{markdown(support.round(4))}

## 7. 阈值与迁移线

阈值敏感性严格恢复为主设置 (100,150) 及冻结的三组
(100,200)、(110,160)、(100,140)：

{markdown(thresholds.round(4))}

G4 明确列为 `NOT_EVALUABLE`。G5 同样不评分：v01 使用一次随机拆分与一个
无条件残差半径，不是注册的留一交叉拟合，也不能提供两类条件侧错误保证。
下表仅为原 v01 数值溯源：

{markdown(transfer.round(4))}
{eol_section}
## 9. 最终科学边界

1. 注册外部门没有通过；结论为 `NOT_ESTABLISHED`，不是 PASS。
2. 注册 K=4 上出现“逐对全部分离、凸包精确碰撞”；K=8 上同一差异仍存在。
3. K=8 的绝对 Delta 未高于置换零分布，不能声称总体正分离。
4. 弛豫增益无法与当前量化管线造成的冗余分区效应区分。
5. 低支持域效应真实但属于有限样本杠杆诊断。
"""

with open(os.path.join(RES, "GATE_REPORT.md"), "w", encoding="utf-8") as handle:
    handle.write(report)
print("wrote results/GATE_REPORT.md")
