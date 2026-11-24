# NASA 电池证据链重做
完整评审式实验报告见 [REPORT_CN.md](REPORT_CN.md)。[结果图](NASA_frontier_and_replay.pdf) 左图为原策略目标的修正前沿，右图为独立电芯回放。两图的采样设计不同。

## 复跑
Python 3.12.14 已实测。从本目录执行以下命令。主程序只读取随包表格，不需要联网获取实验数据。
```bash
python -m pip install -r requirements.txt
python reproduce.py
```
如仅核验现有结果，可运行 `python src/check.py`。重算会更新本目录的 `results/`。每个分析已在干净工作副本复算，57 张结果 CSV 与交付内容逐字节一致。本次从上传包提供的步级表开始，未重做 MATLAB 波形抽取。原论文、旧配置与原冻结果均未覆盖。

## 输入与物理单位
`data/nasa_steps.csv.gz` 是给定 `certlimrepro.zip` 中 NASA 随机使用模块 `steps.parquet` 的 389,307 条记录，保留原行序和 10 个所用字段，包括端电压、测得电流、温度、持续时间等。原 Parquet 的 SHA-256 为 `49ba2b723b4f14191fd5946cb1acd8da902cdd161dc995ea804facd6ae982e39`（以随包 `INPUT_PROVENANCE.json` 为准）。`data/v19_frontier.csv` 是供比较的原冻结表。原数据引用、授权和上游说明保存在 `data/THIRD_PARTY_NOTICES.md`。

## 结果导航
| 问题 | 结果文件或目录 |
|---|---|
| 模型能否定级、缺失概率质量多大 | `results/legacy_grades.csv` |
| 全部 11 个块长度的修正前沿、严格增益上界 | `results/corrected_frontier.csv` |
| H 单通道全网格查表规则 | `results/cutoff_lookup_all_orders.csv` |
| 逐状态置信集合与式（20） | `results/confidence_summary.csv`、`results/confidence_frontier.csv`、`results/confidence_rule_n1.csv` |
| 整电芯置换及分割记录的独立关联 | `results/legacy_block_test.csv`、`results/physical_cell_association.csv` |
| 14 芯冻结与 28 次留一的错误、出决定率和 Alert | `results/physical_summary.csv`、`results/physical_stage_decisions.csv` |
| 查表规则、逐块输入和电芯重采样区间 | `results/frozen_physical_rules.csv`、`results/physical_blocks.csv`、`results/physical_cell_bootstrap.csv` |
| 决策优化及消融 | `results/ordered_summary.csv`、`results/ordered_lookups.csv` |
| 整芯分级和置信保护迁移 | `results/whole_cell_classes.csv`、`results/whole_cell_certificate.csv` |
| 协议对照与重配对 | `results/arm_only_summary.csv`、`results/pairing_summary.csv` |
| 统一为 60 秒终止事件的重放 | `results/fixed60/` |
| 动作前温度降额压力测试 | `results/thermal_summary.csv`、`results/thermal_missing_robust.csv` |

`PROTOCOL.md` 记录本轮初始设置。`REPLAY_BOUNDARY_NOTE.md` 记录隔离上下文窗口的实现修正。`CELL_EXTENSION.md`、`ORDERED_RULE.md`、`DURATION_CHECK.md` 分别标明看过部分数据后的扩展。二次分析使用相同数据，不能当作独立注册确认。仓内的 `locked_14` 指计算时训练与测试隔离，未暗示数据集此前从未被研究者查看。
