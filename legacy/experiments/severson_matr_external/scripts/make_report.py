#!/usr/bin/env python3
"""Create the frozen-result audit report and one publication-style figure."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "results" / "full"


def percent(value: float) -> str:
    return f"{100 * value:.1f}%"


def main() -> None:
    metrics = pd.read_csv(FULL / "menu_metrics.csv")
    permutations = pd.read_csv(FULL / "negative_control_permutations.csv")
    predictions = pd.read_csv(FULL / "external_predictions.csv")
    summary = json.loads((FULL / "summary.json").read_text(encoding="utf-8"))
    by_menu = metrics.set_index("menu")

    permutation_stats = {}
    for menu in ("curve5", "curve100"):
        observed = float(by_menu.loc[menu, "external_mape"])
        permuted = permutations.loc[
            permutations["menu"] == f"{menu}_permuted", "external_mape"
        ].to_numpy()
        permutation_stats[menu] = {
            "observed_mape": observed,
            "median_permuted_mape": float(np.median(permuted)),
            "improvement_vs_median": float(1.0 - observed / np.median(permuted)),
            "one_sided_randomization_p": float((1 + np.sum(permuted <= observed)) / (1 + len(permuted))),
        }

    decision_counts = (
        predictions.groupby(["menu", "decision"]).size().unstack(fill_value=0)
        .reindex(metrics["menu"]).fillna(0).astype(int)
    )
    for decision in ("Reject", "Alert", "Certify"):
        if decision not in decision_counts:
            decision_counts[decision] = 0

    # Figure: all panels use only locked external results.
    labels = ["Protocol", "Scalar-5", "Scalar-100", "Curve-5", "Curve-100"]
    colors = ["#8a94a6", "#64748b", "#475569", "#2563eb", "#0f766e"]
    fig, axes = plt.subplots(1, 3, figsize=(14.2, 4.6), constrained_layout=True)
    x = np.arange(len(metrics))
    axes[0].bar(x, 100 * metrics["external_mape"], color=colors)
    axes[0].set_xticks(x, labels, rotation=30, ha="right")
    axes[0].set_ylabel("External MAPE (%)")
    axes[0].set_title("A. Point prediction")
    axes[0].grid(axis="y", alpha=0.25)

    axes[1].bar(x, 100 * metrics["external_interval_coverage"], color=colors)
    axes[1].axhline(80, color="#b91c1c", linestyle="--", linewidth=1.5, label="Nominal 80%")
    axes[1].axhline(75, color="#ea580c", linestyle=":", linewidth=1.5, label="Gate 75%")
    axes[1].set_xticks(x, labels, rotation=30, ha="right")
    axes[1].set_ylim(0, 100)
    axes[1].set_ylabel("External interval coverage (%)")
    axes[1].set_title("B. Transported uncertainty")
    axes[1].legend(frameon=False, fontsize=8)
    axes[1].grid(axis="y", alpha=0.25)

    reject = decision_counts.loc[metrics["menu"], "Reject"].to_numpy()
    alert = decision_counts.loc[metrics["menu"], "Alert"].to_numpy()
    certify = decision_counts.loc[metrics["menu"], "Certify"].to_numpy()
    axes[2].bar(x, reject, color="#b91c1c", label="Reject")
    axes[2].bar(x, alert, bottom=reject, color="#f59e0b", label="Alert")
    axes[2].bar(x, certify, bottom=reject + alert, color="#15803d", label="Certify")
    axes[2].set_xticks(x, labels, rotation=30, ha="right")
    axes[2].set_ylabel("External cells (n=40)")
    axes[2].set_title("C. Three-decision outputs")
    axes[2].legend(frameon=False, fontsize=8)
    axes[2].grid(axis="y", alpha=0.25)

    fig.suptitle("Severson/MATR locked batch-3 evidence and certification audit", fontsize=14)
    fig.savefig(FULL / "evidence_gate_audit.png", dpi=220)
    fig.savefig(FULL / "evidence_gate_audit.pdf")
    plt.close(fig)

    gates = summary["gates"]
    scalar100_mape = float(by_menu.loc["scalar100", "external_mape"])
    curve5_mape = float(by_menu.loc["curve5", "external_mape"])
    curve100_mape = float(by_menu.loc["curve100", "external_mape"])
    curve5_gain = 1.0 - curve5_mape / scalar100_mape
    curve100_gain = 1.0 - curve100_mape / scalar100_mape
    gate_rows = [
        ("G0", "数据、拆分与时间顺序完整", gates["G0_integrity"]),
        ("G1", "5-cycle 曲线优于 100-cycle 标量遥测至少 10%", gates["G1_curve5_beats_scalar100"]),
        ("G2", "5-cycle 曲线优于置换负控至少 5%", gates["G2_curve5_beats_permuted"]),
        ("G3", "侧误差与 balanced decisiveness 达标", gates["G3_nonvacuous_certification"]),
        ("G4", "外部区间覆盖率至少 75%", gates["G4_transport_calibration"]),
    ]
    gate_table = "\n".join(
        f"| {name} | {description} | {'PASS' if value else 'FAIL'} |"
        for name, description, value in gate_rows
    )
    metric_table = "\n".join(
        "| {menu} | {mape} | {rmse:.1f} | {coverage} | {decisive} | {fc} | {fr} |".format(
            menu=row.menu,
            mape=percent(row.external_mape),
            rmse=row.external_rmse_cycles,
            coverage=percent(row.external_interval_coverage),
            decisive=percent(row.balanced_decisiveness),
            fc=percent(row.unsafe_false_certification_rate),
            fr=percent(row.safe_false_rejection_rate),
        )
        for row in metrics.itertuples()
    )
    curve5_perm = permutation_stats["curve5"]
    curve100_perm = permutation_stats["curve100"]
    report = f"""# Severson/MATR 第二外部门实验报告

## 结论

**注册总门：FAIL。** G0、G1、G3 通过；G2 与 G4 失败。不得把本实验表述为“外部安全认证已经成立”。

实验给出一个更有价值的分解结论：结构化电压曲线确实改善了跨批次点预测，但早至第 5 周期的曲线增益没有通过配对置换负控；到第 100 周期，曲线信号变得明确，而从源域校准的 conformal 置信区间仍在外部批次严重失配。**更多或更好的预测信息，不自动等于可运输的认证置信度。**

## 注册门结果

| 门 | 冻结判据 | 结果 |
|---|---|---|
{gate_table}

## 锁定外部批次指标

| 证据菜单 | MAPE | RMSE（周期） | 80% 区间覆盖 | balanced decisiveness | unsafe→Certify | safe→Reject |
|---|---:|---:|---:|---:|---:|---:|
{metric_table}

外部集含 40 个独立电芯：6 个 unsafe（≤800）、15 个缓冲带、19 个 safe（≥1000）。

![外部门审计图](results/full/evidence_gate_audit.png)

## 逐门解释

### 1. “少量新结构证据”在点预测上击败了“更多旧标量数据”

`curve5` 的外部 MAPE 为 {percent(curve5_mape)}，`scalar100` 为 {percent(scalar100_mape)}，相对降低 {percent(curve5_gain)}，超过注册的 10% 门槛。`curve100` 进一步降到 {percent(curve100_mape)}，相对 `scalar100` 降低 {percent(curve100_gain)}。

这支持一个受限陈述：在该数据集和该冻结模型下，电压-容量曲线变化包含标量容量、温度、内阻与充电时间汇总没有保留的跨批次寿命信息。

### 2. 5-cycle “新证据”没有击穿负控

`curve5` 的 200 次曲线列置换负控中位 MAPE 为 {percent(curve5_perm['median_permuted_mape'])}；真实配对只改善 {percent(curve5_perm['improvement_vs_median'])}，未达到注册的 5% 门，单侧随机化 p={curve5_perm['one_sided_randomization_p']:.4f}。因此不能把 G1 的全部改善归因于第 5 周期曲线与电芯寿命之间的稳定配对关系。

作为**注册后诊断而非改门**，`curve100` 相对其置换中位数改善 {percent(curve100_perm['improvement_vs_median'])}，单侧随机化 p={curve100_perm['one_sided_randomization_p']:.4f}。这表明“正确证据何时成熟”本身存在时间门：第 5 周期尚弱，第 100 周期明确。

### 3. 置信度运输失败

所有菜单的外部 80% 区间覆盖率都低于注册目标；最好的是 `protocol` 的 {percent(by_menu.loc['protocol', 'external_interval_coverage'])}，`curve100` 仅 {percent(by_menu.loc['curve100', 'external_interval_coverage'])}。源域 fit/calibration 中 safe 电芯分别只有 4/6 个，而外部批次有 19 个，并伴随约一年的日历老化差异；校准残差不可交换，split-conformal 的源域有限样本保证不能直接运输到 batch 3。

### 4. G3 的技术通过不能误读成双向认证成功

`curve100` 按冻结的“balanced decisiveness + 双侧错误上限”形式满足 G3，但五个正式菜单在外部集都输出 **0 个 `Certify`**。`curve100` 的 8 个决定性输出全部是 `Reject`，其中 1 个落在真实 safe 侧。因此 G3 是一个偏向拒绝侧的技术通过；实验没有展示可用的正向安全认证能力。这个诊断不追溯修改已冻结的 G3，而是收紧论文中的结论语言。

## 科学含义

1. 证据类型可以形成强关联，但必须靠“真实配对优于同边际置换”来审计；仅看模型误差下降不够。
2. 证据价值具有成熟时间：本实验没有确认第 5 周期曲线的稳定价值，却确认了第 100 周期曲线的强信号。
3. 统计置信度是独立的一道门。即使 `curve100` 的 MAPE 显著改善，外域区间覆盖仍崩溃，点预测前沿与认证前沿不能混同。
4. 本结果支持理论主线的“必要性”部分，但不提供“已经可部署认证”的正面实证。

## 可复现性与边界

- 数据拆分、特征菜单、阈值、模型、种子、置换次数与门槛见 `docs/FROZEN_PROTOCOL.md`。
- `data/processed/registered_features.csv` 是由官方原始 MATLAB v7.3 文件按固定脚本生成的轻量派生表。
- 原始约 8.2 GB 数据不随代码包再分发；`data/RAW_MANIFEST.sha256` 记录来源、字节数与 SHA-256。
- 周期是同一电芯的重复观测；所有误差与拆分均以电芯为单位。
- 充电策略不是在本实验中识别的因果处理；本报告不声称充电策略的因果效应。
"""
    (ROOT / "SEVERSON_EXTERNAL_GATE_REPORT.md").write_text(report, encoding="utf-8")
    (FULL / "posthoc_diagnostics.json").write_text(
        json.dumps({
            "permutation_stats": permutation_stats,
            "decision_counts": decision_counts.to_dict(orient="index"),
            "note": "Diagnostics do not alter frozen gates.",
        }, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
