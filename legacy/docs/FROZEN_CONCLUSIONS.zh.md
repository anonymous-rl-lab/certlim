# 冻结结论与证据边界

本表是每个实验层的冻结裁决与其可支持主张的对照，与论文正文和 Supplementary Information 的
claim-to-artifact crosswalk 一一对应。英文摘要见仓库根目录 README。

## 冻结结论

| 实验层 | 状态 | 可支持的主张 |
|---|---:|---|
| 合成 smoke | **PASS，8/8** | v04 代数、概率和 LP 地标闭合 |
| 合成 small | **PASS，12/12** | 精确前沿、有限样本率和注册 Monte Carlo 闭合 |
| Jones 数据/时序 | **PASS** | 48 个电芯、5,118 个完整循环，解析记录时序一致率 100% |
| Jones 受控外部容量预测 | **诊断性支持** | 真实 EIS 相对同种子置乱 EIS 的配对中位 RMSE 改善为 8.2%/13.1% |
| Jones 严格三决策认证 | **FAIL** | 修复退化阈值后，Unsafe→Certify 中位错误仍为 52.1% |
| MATR 数据/时序 | **PASS** | 124 个独立电芯；41 fit、43 calibration、40 locked external；物理周期索引闭合 |
| MATR 结构证据价值 | **部分通过** | Curve-100 外测 MAPE 25.8%，Scalar-100 为 42.9%；配对置换诊断 p=0.005 |
| MATR 注册总门 | **FAIL** | Curve-5 负控门和外部置信覆盖门失败；全部菜单输出 0 个 Certify |
| Zhu 原始数据与标签审计 | **PASS** | 118 芯特征可由原始 CSV 逐列精确重建；EOL 3×3×3 共 27 个变体，域等级最大变化为 0 |
| Zhu 注册外部门 | **NOT ESTABLISHED** | G2 失败；G1/G4/G5 在冻结实现下不可评价，不合成为事后 PASS |
| Zhu 复合几何诊断 | **诊断性支持** | 注册 K=4 下最小逐对 TV=0.25、凸包 Δ=0，差值置换 p=0.0075；K=8 结果仅作分辨率敏感性 |
| Zhu 弛豫额外增益 | **未建立** | K=8 增益 +0.0714，小于冗余管线底 +0.1481；域内配对置换 p=0.398 |
| PulseBat 数据/抽样单位 | **PASS** | 151 块独立物理电池、每芯 10 个 SOC 记录；推断与重采样均以电池为单位 |
| PulseBat 化学标签控制碰撞 | **构造性 PASS** | 原“铭牌/历史”实现实际只含化学体系点质量；数据没有物理形式和历史用途字段。该控制对所有 n 有 Δ=0、D=0.10 |
| PulseBat SOC=5% 局部脉冲门 | **PASS，局部有效** | 0.5C 脉冲 Δ(1)=0.5273、D(1)=0.2517；置换 p=0.001，整电池 Bootstrap 95% CI [0.3455, 0.7227] |
| PulseBat SOC×菜单纠偏 | **诊断性支持** | SOC=10% OCV Δ(1)=0.6273、p=0.001、CI [0.4455, 0.7980]；相对 SOC=5% 脉冲的配对差值 CI [−0.1864, 0.3773]，未证明谁更优 |
| PulseBat 复合几何 | **退化为逐对** | 所有菜单与注册 n 上凸包 Δ 等于最小化学体系逐对 TV，最大数值差 5.40e-9；注册前沿由 17 块 LFP35 电池承重 |
| PulseBat 物理 Pareto | **跨 SOC 未建立** | 冻结成本表未按 SOC 登记，且时间包含预处理而应力列排除预处理；只保留 SOC=5% 内 0.5C 相对 1C/1.5C 的局部比较 |
| NASA RW 主定理直接检验 | **PASS，11/11** | Δ(n) 由 0.1494 单调升至 0.5558；主界无越界；Sion 最大残差 4.32e-8 |
| NASA RW 碰撞处可达 | **PASS** | 对抗性热降额策略使 Δ=0、D=0.10=α+β；朴素混杂反而提高 Δ，未制造碰撞 |
| Battery ALT 结构复现 | **PASS，30/30** | 三个量化分辨率的有限样本界均成立；n★ 随 K=2/4/8 为 3/2/1；严格嵌套数据处理门通过 |
| Battery ALT 通道有效性 | **未建立** | 参考放电通道的 Δ(20) 置换右尾 p=0.206；上界成立不等于通道有用 |
| Battery ALT 策略轴 | **FAIL / 不可估** | 83.7% 的 θ 仅覆盖一个动作档位，注册策略切换目标不存在；未事后修补 |

六个真实系统共同限定了结论边界。Jones、MATR 与 Zhu 给出跨域失败、配对和复合几何诊断；PulseBat 给出工况感知的证据采购实例；NASA RW 与 Battery ALT 则把主界、碰撞处可达性和有限阶凸包分离直接落到两个独立电池基质上：

> 正确的新实验可以改善经验分离，但逐对距离、复合凸包距离、预测增益和可运输置信度是不同的门。NASA RW 说明主界可在随机化识别的风险真值上检验并在碰撞处取等；Battery ALT 说明一阶凸包相交不等于永久障碍；PulseBat 说明证据实验必须连同 SOC 与激励共同注册，增加测试应力并不保证增加认证信息。

## 目录

```text
repo_v6/
├── docs/
│   ├── MASTER_EXPERIMENT_REPORT.md
│   ├── CLAIM_STATUS.md
│   ├── DATA_PROVENANCE.md
│   ├── THEORY_CHAPTER_v05_1.md
│   └── TII_MAIN_MANUSCRIPT_v02.md
├── experiments/
│   ├── synthetic_gates/
│   ├── jones_eis_external/
│   ├── severson_matr_external/
│   ├── zhu_relaxation_external/
│   ├── pulsebat_procurement_external/
│   ├── pulsebat_procurement_correction_v02/
│   ├── nasa_randomized_usage_gate/
│   └── battery_alt_reference_channel_gate/
├── scripts/
│   ├── run_repository_checks.py
│   ├── build_manifest.py
│   └── verify_manifest.py
├── tests/
├── MANIFEST.sha256
├── requirements.txt
└── VERSION
```

## 快速审计

Python 3.11+：

```bash
python -m pip install -r requirements.txt
python scripts/run_repository_checks.py
python scripts/verify_manifest.py
```

重跑注册合成实验：

```bash
cd experiments/synthetic_gates
python -m unittest discover -s tests -v
python scripts/run_gates.py smoke
python scripts/run_gates.py small
```

Jones、MATR、Zhu、PulseBat 与两个 NASA 实验的原始归档均不在本包中。下载、校验与重建方法见 `docs/DATA_PROVENANCE.md`。审计所需的轻量派生表、冻结结果和勘误随包提供；NASA RW 的 389,307 步派生表与 Battery ALT 的 mission/model 表也完整保留。

## 结果入口

- 总报告：`docs/MASTER_EXPERIMENT_REPORT.md`
- 主张边界：`docs/CLAIM_STATUS.md`
- 合成生死门：`experiments/synthetic_gates/EXPERIMENT_CONCLUSION.md`
- Jones 报告：`experiments/jones_eis_external/JONES_EIS_GATE_REPORT.md`
- MATR 报告：`experiments/severson_matr_external/SEVERSON_EXTERNAL_GATE_REPORT.md`
- Zhu v01.1 报告：`experiments/zhu_relaxation_external/results/GATE_REPORT.md`
- Zhu 协议勘误：`experiments/zhu_relaxation_external/docs/PROTOCOL_ERRATA.md`
- PulseBat 冻结报告：`experiments/pulsebat_procurement_external/results/REPORT.md`
- PulseBat 纠偏报告：`experiments/pulsebat_procurement_correction_v02/AUDIT_REPORT.md`
- PulseBat 纠偏主张：`experiments/pulsebat_procurement_correction_v02/docs/CLAIM_CORRECTIONS.md`
- PulseBat 40 点证书：`experiments/pulsebat_procurement_correction_v02/results/full/soc_menu_uncertainty.csv`
- NASA RW 正式报告：`experiments/nasa_randomized_usage_gate/results/GATE_REPORT.md`
- Battery ALT 正式报告：`experiments/battery_alt_reference_channel_gate/results/GATE_REPORT.md`
- 两实验主张汇总：`docs/certification_limits_evidence_bundle_v01/CLAIMS_VS_EVIDENCE.md`
- 两实验门编号对照：`docs/certification_limits_evidence_bundle_v01/GATE_CROSSWALK.md`
