#!/usr/bin/env python3
"""Generate a conservative claim-to-evidence ledger for v01.1."""
from __future__ import annotations

import json
import os

import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES, DOC = os.path.join(ROOT, "results"), os.path.join(ROOT, "docs")


def load_json(name):
    with open(os.path.join(RES, name), encoding="utf-8") as handle:
        return json.load(handle)


summary = load_json("summary.json")
registered = load_json("as_registered_gates.json")
raw_reproduction = load_json("raw_feature_reproduction.json")
deltas = pd.read_csv(os.path.join(RES, "delta_menus.csv"))
geometry_all = pd.read_csv(os.path.join(RES, "geometry_permutation_summary.csv"))
geometry4 = geometry_all[geometry_all.K == summary["registered_primary_K"]].set_index("metric")
geometry8 = geometry_all[geometry_all.K == 8].set_index("metric")
pairing = pd.read_csv(os.path.join(RES, "relax_pairing_summary.csv")).set_index("K")
leave = pd.read_csv(os.path.join(RES, "leave_one_domain.csv"))
eol_path = os.path.join(RES, "eol_sensitivity_summary.csv")

k8 = deltas[deltas.K == 8].set_index("menu")
gain = float(k8.loc["summary_relax", "delta"] - k8.loc["summary", "delta"])
floor = float(k8.loc["summary_derived", "delta"] - k8.loc["summary", "delta"])
low = leave[(leave.K == 8) & (leave.dropped_safe_domain == "NCA_T35_C0.5")].iloc[0]

rows = [
    ("原始 CSV 可逐列重建发布特征表", "Supported",
     f"status={raw_reproduction['status']}, max numeric difference="
     f"{raw_reproduction['max_numeric_absolute_difference']:.3g}"),
    ("冻结注册外部门通过", "Not established",
     registered["overall"]["reason"]),
    ("注册 K=4 下逐对分离但复合凸包碰撞", "Supported diagnostic",
     f"min pairwise={summary['registered_K4']['min_pairwise_tv']:.4f}, "
     f"hull Delta={summary['registered_K4']['hull_delta']:.4f}, "
     f"gap permutation p={geometry4.loc['pairwise_minus_hull','p_upper']:.4f}; "
     "registered resolution but post-hoc contrast"),
    ("K=8 下逐对 TV 高估凸包可分离度", "Supported diagnostic",
     f"min pairwise={summary['exploratory_K8']['min_pairwise_tv']:.4f}, "
     f"hull Delta={summary['exploratory_K8']['hull_delta']:.4f}, "
     f"gap permutation p={geometry8.loc['pairwise_minus_hull','p_upper']:.4f}; K=8 是分辨率敏感性"),
    ("K=8 绝对凸包 Delta 高于置换零分布", "Not established",
     f"Delta={geometry8.loc['hull_delta','observed']:.4f}, p={geometry8.loc['hull_delta','p_upper']:.4f}"),
    ("弛豫通道提供超出冗余管线的可分离度增益", "Not established",
     f"relax gain={gain:+.4f}, pipeline floor={floor:+.4f}, "
     f"within-domain pairing p={pairing.loc[8,'p_upper']:.4f}"),
    ("弛豫通道没有信息", "Not tested",
     "负结果只针对当前有限样本量化管线，不能证伪通道信息"),
    ("严格粗化使 Delta 单调不增", "Code invariant",
     "同一 K=8 分区粗化为 K=4/K=2；结构上必然成立，不是外部实证"),
    ("低支持安全域显著影响经验凸包", "Supported diagnostic",
     f"drop {low.dropped_safe_domain}(n={int(low.n_cells)}): "
     f"Delta {low.delta_full:.4f}->{low.delta_without:.4f}, "
     f"permutation p={geometry8.loc['leave_one_shift','p_upper']:.4f}; population claim not made"),
    ("迁移侧错误界被外部验证", "Not evaluable",
     "v01 calibration is unconditional and does not implement the registered class-conditional procedure"),
    ("弛豫是理论意义上的独立因果代理", "Not established",
     "仅为非派生测量通道；没有验证条件独立性或完备性"),
    ("跨化学因果认证得到验证", "Not established",
     f"domain identity explains {100*summary['eta_squared_domain']:.1f}% of log10(EOL) variance"),
]

if os.path.exists(eol_path):
    eol = pd.read_csv(eol_path)
    rows.append(("EOL 3x3x3 稳健性网格已执行", "Completed",
                 f"27 variants; maximum domain-grade changes={int(eol.n_domain_grade_changes_vs_primary.max())}"))
else:
    rows.append(("EOL 3x3x3 稳健性网格已执行", "Missing",
                 "requires raw data; run scripts/05_run_eol_sensitivity.py"))

text = "# 主张与证据 — v01.1\n\n"
text += "注册结果与事后诊断严格分层；`Supported diagnostic` 不等于确认性门通过。\n\n"
text += "| 主张 | 状态 | 证据边界 |\n|---|---:|---|\n"
text += "\n".join(f"| {claim} | **{status}** | {evidence} |"
                  for claim, status, evidence in rows) + "\n"
with open(os.path.join(DOC, "CLAIM_STATUS.md"), "w", encoding="utf-8") as handle:
    handle.write(text)
print("wrote docs/CLAIM_STATUS.md")
