# 数据溯源

## 上游

| 项 | 值 |
|---|---|
| 论文 | Zhu, J. *et al.* "Data-driven capacity estimation of commercial lithium-ion batteries from voltage relaxation." *Nature Communications* **13**, 2261 (2022) |
| 论文 DOI | `10.1038/s41467-022-29837-w` |
| 数据 DOI | `10.5281/zenodo.6405084` |
| 许可 | CC BY 4.0 |
| 下载 | `scripts/download_data.sh`(Zenodo 直连,无需申请) |

## 使用与未使用

| 归档 | 内容 | 本实验 |
|---|---|---|
| `Dataset_1_NCA_battery.zip` (580 MB) | NCA 18650,66 芯 | **使用** |
| `Dataset_2_NCM_battery.zip` (737 MB) | NCM 18650,55 芯 | **使用** |
| `Dataset_3_NCM_NCA_battery.zip` (356 MB) | NCM+NCA,9 芯 | **排除** |
| `Impedance raw data and fitting data.zip` (1.3 MB) | 代表性电芯 EIS | 未使用 |

**排除 Dataset_3 的理由(冻结协议 §1.1)**:其充电后静置协议为 3570 s / 120 点 / 30 s 采样,
而 NCA 与 NCM 在 25/35/45 °C、0.25/0.5/1 C 全部工况下均为 1680 s / 15 点 / 120 s。
化学体系与测量协议在该子集上不可分离,把它并进来会让"跨化学"与"跨测量协议"混淆。
代价是失去放电倍率轴(1C/2C/4C)。

## 文件命名

`CY{温度}-{充电倍率}_{放电倍率}-#{编号}.csv`,例如 `CY45-05_1-#12` = 45 °C,充电 0.5 C,放电 1 C,第 12 芯。
列:`time/s, control/V/mA, Ecell/V, <I>/mA, Q discharge/mA.h, Q charge/mA.h, control/V, control/mA, cycle number`。

## 派生产物

| 文件 | 生成脚本 | 说明 |
|---|---|---|
| `data/processed/features.csv` | `scripts/01_extract_features.py` | 118 芯 × (标签 + 8 维循环摘要 + 34 维弛豫) |
| `data/processed/excluded_cells.csv` | 同上 | 被排除的电芯及原因 |
| `results/*` | `scripts/02_run_gates.py` | 注册裁决、纠偏诊断与置换/自助结果 |
| `results/eol_sensitivity_*` | `scripts/05_run_eol_sensitivity.py` | 冻结 3×3×3 EOL 网格 |
| `results/raw_feature_reproduction.json` | `scripts/06_verify_raw_features.py` | 原始 CSV 到发布特征表的独立重提取核对 |
| `results/GATE_REPORT.md` | `scripts/03_make_report.py` | 由结果文件生成,不含手写数字 |

本实验实际使用的两组原始 CSV 解压后约 4.2 GB（包含被排除 Dataset_3 时约 5.3 GB），
**不随包分发**,由 `download_data.sh` 获取。
`features.csv` 随包分发,因此 `02`/`03` 两步可在无原始数据的情况下完整复现。

## 已知的上游数据缺陷

1. **中断周期**:NCA 在第 25–26 周期、NCM 在第 51 周期附近存在协议变更(每周期采样行数由约 583 跳到约 909),
   个别周期被截断,放电容量掉到初始值的 2.7%,下一周期恢复。若不剔除会被误判为衰减。
   全池共剔除 442 个此类周期(见 `features.csv` 的 `n_aborted` 列)。
2. **右截尾**:118 芯中 20 芯在记录期内未跌破 90% 初始容量。EOL@80 的截尾更重(约 42%),
   故主分析采用 EOL@90。
3. **静置截断**:3 芯的充电后静置窗口短于 1600 s,已排除。
