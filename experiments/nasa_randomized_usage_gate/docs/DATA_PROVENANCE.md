# 数据溯源

## 上游

| 项 | 值 |
|---|---|
| 数据集 | NASA PCoE *Randomized Battery Usage Data Set* |
| DOI | `10.5281/zenodo.15277374` |
| 许可 | CC BY 4.0 |
| 引用 | B. Bole, C. Kulkarni, M. Daigle, "Adaptation of an Electrochemistry-based Li-Ion Battery Model to Account for Deterioration Observed Under Randomized Use," *Annual Conf. PHM Society*, 2014 |
| 下载 | `scripts/00_download_and_extract.sh`(Zenodo 直连) |

## 七个子集(全部使用)

| 归档 | 动作分布 | 温度 | 电芯 |
|---|---|---|---|
| 1. Battery_Uniform_Distribution_Charge_Discharge | 均匀 | 室温 | RW9–RW12 |
| 2. Battery_Uniform_Distribution_Discharge_Room_Temp | 均匀 | 室温 | RW3–RW6 |
| 3. Battery_Uniform_Distribution_Variable_Charge_Room_Temp | 均匀 | 室温 | RW1,2,7,8 |
| 4. RW_Skewed_High_40C | 偏高 | 40 °C | RW25–RW28 |
| 5. RW_Skewed_High_Room_Temp | 偏高 | 室温 | RW17–RW20 |
| 6. RW_Skewed_Low_40C | 偏低 | 40 °C | RW21–RW24 |
| 7. RW_Skewed_Low_Room_Temp | 偏低 | 室温 | RW13–RW16 |

共 28 芯。原始归档解压后约 5 GB,**不随包分发**。

## 倾向性的独立验证

数据集文档给出动作抽取的概率表。我在 skewed-high 子集的前 4000 步上实测比对:

| 负载档 | 文档概率 | 实测 |
|---|---|---|
| 3.5 A | 17.2% | 17.10% |
| 4.0 A | 23.4% | 22.80% |
| 4.5 A | 19.4% | 18.95% |
| 5.0 A | 5.0% | 4.47% |

**倾向性已知且被独立验证** —— 这是 P(H=1 \| Z, do(A)) 可识别的依据,也是本数据集区别于
Jones / Severson / Zhu 三个观测型数据集的根本之处。

## 派生产物

| 文件 | 生成脚本 | 说明 |
|---|---|---|
| `data/steps.parquet` | `scripts/01_extract_steps.py` | 389,307 个随机游走放电步 × 28 芯(**随包分发**) |
| `data/models.parquet` | `scripts/02_build_models.py` | 1539 个 (θ,π) 模型:证据 pmf、Ψ、等级 |
| `data/collision.parquet` | `scripts/04_run_L3.py` | 随机臂与混杂臂的证据分布 |
| `results/*` | `scripts/03,04,05,06` | 全部门控、诊断与敏感性 |
| `results/GATE_REPORT.md` | `scripts/07_make_report.py` | 由结果文件生成,不含手写数字 |

`steps.parquet` 随包,因此 `02` 之后的全部步骤可**离线复现**;`01` 需要原始数据。

## 上游数据的处理要点

1. 每个 `.mat` 的 `data.step[]` 中,`type='D'` 且 comment 含 "random walk" 的步才是随机化动作步。
2. 老化阶段由 "reference discharge" 步切分(相邻 ≤3 步的重复引用合并为同一次参考)。
3. 动作 = 该步电流绝对值的中位数,四舍五入到整数安培,限制在共同支撑 {1,2,3,4} A。
4. 危害 H = 该步终止电压 ≤ 3.25 V(即触发 3.2 V 保护截止)。
