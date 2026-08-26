# Zhu 2022 电压弛豫外部认证门 — 结果报告

自动生成自 `results/`。不含任何手写数字。

- 冻结时刻:`2026-08-26T00:40:31.778651+00:00`(在任何模型拟合之前)
- 协议 SHA-256:`dabfc607d1437919f5600be3427032b59b7e934cf2ccb3f62f16514ab61f20cc`
- 配置 SHA-256:`94213d3a6f1860778b64760140c9ddc653db5c5fde5acd972c21ba75a72dc1ed`
- 运行环境:python 3.11.15 / numpy 2.4.4 / scipy 1.17.1 / sklearn 1.8.0

## 0. 总判定

**overall_pass = False**

| 门 | 判据 | 结果 |
|---|---|:--|
| G0_integrity | source domain has >=5 cells on each side | PASS |
| G1_P1_data_processing | Delta non-increasing under a strictly nested coarsening | PASS |
| G2_P2_redundancy_null | |Delta(summary+derived) - Delta(summary)| <= null SD (pipeline negative control, not a theorem test - see ERRATA) | FAIL |
| G3_P3_channel_gain | relax gain exceeds the dimension-matched redundancy floor AND permutation p<0.05 | FAIL |
| G5_Q2_transported_side_error | every measurable target satisfies observed side error <= alpha+rho | FAIL |

## 1. 数据

- 电芯 118,其中有 EOL@90 的 98,进入域分类的 116
- 剔除的中断周期 442
- Spearman(EOL@90, EOL@95) = 0.7904

### 域级策略风险 Psi = P(EOL@90 <= 100)

| domain        |    psi |   n | cls   |
|:--------------|-------:|----:|:------|
| NCA_T25_C0.25 | 0      |   5 | S     |
| NCA_T25_C0.5  | 0.1579 |  19 | A     |
| NCA_T25_C1.0  | 1      |   8 | U     |
| NCA_T35_C0.5  | 0      |   2 | S     |
| NCA_T45_C0.5  | 0.3214 |  28 | U     |
| NCM_T25_C0.5  | 0      |  22 | S     |
| NCM_T35_C0.5  | 0      |   4 | S     |
| NCM_T45_C0.5  | 0      |  28 | S     |

## 2. 主诊断:逐对散度不是正确的对象

最小逐对 TV = **0.4286**,凸包 Delta = **0.1786**,
比值 **2.40x**。

| safe_domain   | unsafe_domain   |     tv |
|:--------------|:----------------|-------:|
| NCA_T35_C0.5  | NCA_T45_C0.5    | 0.4286 |
| NCA_T25_C0.25 | NCA_T45_C0.5    | 0.5714 |
| NCM_T45_C0.5  | NCA_T45_C0.5    | 0.5714 |
| NCM_T25_C0.5  | NCA_T45_C0.5    | 0.711  |
| NCM_T35_C0.5  | NCA_T25_C1.0    | 0.75   |
| NCM_T25_C0.5  | NCA_T25_C1.0    | 0.8182 |
| NCM_T45_C0.5  | NCA_T25_C1.0    | 0.9643 |
| NCM_T35_C0.5  | NCA_T45_C0.5    | 0.9643 |
| NCA_T25_C0.25 | NCA_T25_C1.0    | 1      |
| NCA_T35_C0.5  | NCA_T25_C1.0    | 1      |

## 3. Delta 由单个安全域决定

| dropped_safe_domain   |   n_cells |   delta_without |   delta_full |   shift |
|:----------------------|----------:|----------------:|-------------:|--------:|
| NCA_T35_C0.5          |         2 |          0.5178 |       0.1786 |  0.3393 |
| NCA_T25_C0.25         |         5 |          0.2296 |       0.1786 |  0.0511 |
| NCM_T25_C0.5          |        22 |          0.1786 |       0.1786 |  0      |
| NCM_T35_C0.5          |         4 |          0.1786 |       0.1786 |  0      |
| NCM_T45_C0.5          |        28 |          0.1786 |       0.1786 |  0      |

## 4. B 线:Delta 与置换零分布(K = 2, 4, 8)

|   K | menu            |   n_columns |   delta |   null_mean |   null_sd |   null_q95 |   excess |   p_perm |
|----:|:----------------|------------:|--------:|------------:|----------:|-----------:|---------:|---------:|
|   2 | summary         |           8 |  0      |      0.0036 |    0.0165 |     0.025  |  -0.0036 |   1      |
|   2 | g_summary       |           8 |  0      |      0.0032 |    0.0185 |     0      |  -0.0032 |   1      |
|   2 | summary_derived |          42 |  0      |      0.004  |    0.0181 |     0.0255 |  -0.004  |   1      |
|   2 | relax           |          34 |  0      |      0.0057 |    0.0215 |     0.0361 |  -0.0057 |   1      |
|   2 | summary_relax   |          42 |  0      |      0.0057 |    0.0215 |     0.0361 |  -0.0057 |   1      |
|   4 | summary         |           8 |  0      |      0.0345 |    0.0465 |     0.1334 |  -0.0345 |   1      |
|   4 | g_summary       |           8 |  0.0508 |      0.0326 |    0.0437 |     0.1199 |   0.0182 |   0.2814 |
|   4 | summary_derived |          42 |  0.1129 |      0.0327 |    0.0451 |     0.127  |   0.0802 |   0.0798 |
|   4 | relax           |          34 |  0      |      0.0384 |    0.0475 |     0.1304 |  -0.0384 |   1      |
|   4 | summary_relax   |          42 |  0      |      0.0378 |    0.0474 |     0.1364 |  -0.0378 |   1      |
|   8 | summary         |           8 |  0.1786 |      0.1339 |    0.0596 |     0.2484 |   0.0447 |   0.2295 |
|   8 | g_summary       |           8 |  0.2246 |      0.1116 |    0.0557 |     0.214  |   0.1129 |   0.0359 |
|   8 | summary_derived |          42 |  0.3267 |      0.1317 |    0.0568 |     0.2273 |   0.195  |   0.004  |
|   8 | relax           |          34 |  0.1865 |      0.1349 |    0.057  |     0.2275 |   0.0516 |   0.1836 |
|   8 | summary_relax   |          42 |  0.25   |      0.1371 |    0.0579 |     0.2365 |   0.1129 |   0.0399 |

### 三条配对读数(K=8)

- `summary` Delta = **0.1786**,零分布 SD = 0.0596
- 加 34 个**零信息**派生列:Delta 变化 **+0.1481** ← 维度膨胀底
- 加 34 个**弛豫测量**列:Delta 变化 **+0.0714**
- 弛豫增益**未超过**维度膨胀底 → G3 **FAIL**

## 5. 数据处理不等式(严格嵌套量化器)

|   K |   delta |   nested_from | monotone   |
|----:|--------:|--------------:|:-----------|
|   8 |  0.1786 |           nan | True       |
|   4 |  0      |             8 | True       |
|   2 |  0      |             8 | True       |

## 6. 阈值敏感性(主分析冻结在第一行)

|   hazard_cycles |   n_unsafe_domains |   delta_summary |   delta_derived |   delta_relax |   relax_gain |   redundancy_floor | gain_exceeds_floor   |
|----------------:|-------------------:|----------------:|----------------:|--------------:|-------------:|-------------------:|:---------------------|
|             100 |                  2 |          0.1786 |          0.3267 |        0.25   |       0.0714 |             0.1481 | False                |
|             110 |                  3 |          0.102  |          0.192  |        0.3637 |       0.2616 |             0.09   | True                 |
|             120 |                  3 |          0.102  |          0.192  |        0.3637 |       0.2616 |             0.09   | True                 |

## 7. A 线:四点迁移案例

源域 `NCA_T45_C0.5`,n=27
(unsafe 9 / safe 11),
fit 13 / cal 14,
conformal 半径(log10) = 0.2746

| target        |   n | side   |   n_unsafe |   n_safe |   decisiveness |   observed_side_error |   rho_U |    rho_S |   bound | bound_is_vacuous   | Q2_holds   |
|:--------------|----:|:-------|-----------:|---------:|---------------:|----------------------:|--------:|---------:|--------:|:-------------------|:-----------|
| NCA_T25_C0.5  |  17 | unsafe |          3 |        0 |         0.2941 |                     0 |       1 | nan      |  1.1    | True               | True       |
| NCA_T25_C1.0  |   8 | unsafe |          8 |        0 |         0.875  |                     0 |       1 | nan      |  1.1    | True               | True       |
| NCA_T25_C0.25 |   5 | safe   |          0 |        5 |         1      |                     1 |     nan |   0.8182 |  0.9182 | False              | False      |
| NCM_T45_C0.5  |  25 | safe   |          0 |       25 |         1      |                     0 |     nan |   0.7091 |  0.8091 | False              | True       |

## 8. 解释边界

见 `docs/FROZEN_PROTOCOL.md` §8 与 `docs/PROTOCOL_ERRATA.md`。要点:
域身份解释 log10(EOL) 的 88.6% 方差,安全等级近乎域身份的确定函数;
本实验的 Delta 差异只能解释为**证据集合上的分离度变化**,不能解释为因果信息增益。
