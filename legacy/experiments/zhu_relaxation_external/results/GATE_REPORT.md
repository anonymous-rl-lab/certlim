# Zhu 2022 电压弛豫外部认证门 — v01.1 纠偏报告

本报告由结果文件自动生成。冻结协议和冻结配置均未改写。

- 冻结时刻：`2026-08-26T00:40:31.778651+00:00`
- 协议 SHA-256：`dabfc607d1437919f5600be3427032b59b7e934cf2ccb3f62f16514ab61f20cc`
- 配置 SHA-256：`94213d3a6f1860778b64760140c9ddc653db5c5fde5acd972c21ba75a72dc1ed`
- 注册主分辨率：K=4

## 0. 裁决

**注册结论：NOT_ESTABLISHED**  
**事后纠偏层：DIAGNOSTIC_ONLY**

这两个层次不得合并成一个布尔 `overall_pass`。v01 的原始结果完整保存在
`results/legacy_v01/`。

| gate | nominal | inferential_status | validity |
|---|---|---|---|
| G0_integrity | True | PASS | valid |
| G1_P1_data_processing | True | NOT_EVALUABLE | invalid theorem test: the two menus were independently quantized and are not nested |
| G2_P2_equality | False | FAIL | pipeline negative control only; population equality is an identity |
| G3_P3_channel_gain | False | NOT_DETECTED | empirical pipeline randomization; not a causal-proxy test |
| G4_Q1_margin |  | NOT_EVALUABLE | each target exposes only one safety side and plug-in rho is vacuous |
| G5_Q2_side_error | False | NOT_EVALUABLE | released v01 used one unconditional split radius, not registered leave-one/class-conditional calibration |

## 1. 数据完整性

- 电芯数：118
- 有 EOL@90：98
- 进入风险分类：116
- 剔除中断周期：442
- Spearman(EOL@90,EOL@95)：0.7904
- 域身份对 log10(EOL) 的 eta²：0.8863
- 原始 CSV 重提取：PASS，最大数值差
  0

| domain | psi | n | cls |
|---|---|---|---|
| NCA_T25_C0.25 | 0.0 | 5 | S |
| NCA_T25_C0.5 | 0.1579 | 19 | A |
| NCA_T25_C1.0 | 1.0 | 8 | U |
| NCA_T35_C0.5 | 0.0 | 2 | S |
| NCA_T45_C0.5 | 0.3214 | 28 | U |
| NCM_T25_C0.5 | 0.0 | 22 | S |
| NCM_T35_C0.5 | 0.0 | 4 | S |
| NCM_T45_C0.5 | 0.0 | 28 | S |

## 2. 注册主分析：K=4

注册 K=4 下，最小逐对 TV 为 0.2500，
但凸包 Delta 为 0.0000：**所有逐对均分离，
复合凸包却发生精确碰撞**。该逐对—凸包差的置换 p=
0.0075。这是注册分辨率上的事后几何诊断，
不是原冻结门之一。

| K | menu | n_columns | delta | null_mean | null_sd | null_q95 | excess | p_perm |
|---|---|---|---|---|---|---|---|---|
| 4 | summary | 8 | 0.0 | 0.0345 | 0.0465 | 0.1334 | -0.0345 | 1.0 |
| 4 | g_summary | 8 | 0.0508 | 0.0326 | 0.0437 | 0.1199 | 0.0182 | 0.2814 |
| 4 | summary_derived | 42 | 0.1129 | 0.0327 | 0.0451 | 0.127 | 0.0802 | 0.0798 |
| 4 | relax | 34 | 0.0 | 0.0384 | 0.0475 | 0.1304 | -0.0384 | 1.0 |
| 4 | summary_relax | 42 | 0.0 | 0.0378 | 0.0474 | 0.1364 | -0.0378 | 1.0 |

域内弛豫配对置换实际执行 200 次：观测增益
-0.0000，置换 p=1.0000，注册 G3 为
**NOT_DETECTED**。

## 3. K=8 分辨率敏感性：逐对几何与凸包几何分离

K=8 下，最小逐对 TV 为 0.4286，
凸包 Delta 为 0.1786，比值
2.40×。这是**冻结的分辨率敏感性结果**；
逐对—凸包对比本身属于事后诊断。

K=4/K=8 全局行置换校准：

| K | metric | observed | null_mean | null_sd | null_q95 | p_upper | n_permutations | dropped_domain |
|---|---|---|---|---|---|---|---|---|
| 4 | hull_delta | 0.0 | 0.0365 | 0.0478 | 0.1384 | 1.0 | 2000 |  |
| 4 | min_pairwise_tv | 0.25 | 0.1229 | 0.0539 | 0.2143 | 0.0225 | 2000 |  |
| 4 | pairwise_minus_hull | 0.25 | 0.0864 | 0.0554 | 0.1786 | 0.0075 | 2000 |  |
| 4 | leave_one_shift | 0.1674 | 0.0146 | 0.0295 | 0.079 | 0.0015 | 2000 | NCA_T35_C0.5 |
| 8 | hull_delta | 0.1786 | 0.1346 | 0.057 | 0.2373 | 0.2234 | 2000 |  |
| 8 | min_pairwise_tv | 0.4286 | 0.2423 | 0.0622 | 0.3442 | 0.005 | 2000 |  |
| 8 | pairwise_minus_hull | 0.25 | 0.1078 | 0.0579 | 0.2076 | 0.0165 | 2000 |  |
| 8 | leave_one_shift | 0.3393 | 0.0153 | 0.0255 | 0.0696 | 0.0005 | 2000 | NCA_T35_C0.5 |

K=8 绝对 Delta 的 p=0.2234，未建立总体分离；
逐对减凸包差的 p=0.0165，支持“逐对距离
可显著高估复合可分离度”这一经验诊断。

| safe_domain | unsafe_domain | tv |
|---|---|---|
| NCA_T35_C0.5 | NCA_T45_C0.5 | 0.4286 |
| NCA_T25_C0.25 | NCA_T45_C0.5 | 0.5714 |
| NCM_T45_C0.5 | NCA_T45_C0.5 | 0.5714 |
| NCM_T25_C0.5 | NCA_T45_C0.5 | 0.711 |
| NCM_T35_C0.5 | NCA_T25_C1.0 | 0.75 |
| NCM_T25_C0.5 | NCA_T25_C1.0 | 0.8182 |
| NCM_T45_C0.5 | NCA_T25_C1.0 | 0.9643 |
| NCM_T35_C0.5 | NCA_T45_C0.5 | 0.9643 |
| NCA_T25_C0.25 | NCA_T25_C1.0 | 1.0 |
| NCA_T35_C0.5 | NCA_T25_C1.0 | 1.0 |

## 4. 新通道、冗余管线与置换对照

K=8 时，加入弛豫列的表观增益为
+0.0714；
加入同维数确定性派生列的管线增益为
+0.1481。
弛豫增益没有超过该管线底线；域内配对置换 p=0.3980。

结论是：**当前管线下，弛豫通道的额外增益尚未建立**。这不是“弛豫通道
没有信息”的证伪结论。各菜单独立压缩，故该对照同时包含分区改变效应。

| K | baseline_delta | observed_joint_delta | observed_gain | null_mean_gain | null_sd_gain | null_q95_gain | p_upper | n_permutations |
|---|---|---|---|---|---|---|---|---|
| 4 | 0.0 | 0.0 | -0.0 | -0.0 | 0.0 | 0.0 | 1.0 | 200 |
| 8 | 0.1786 | 0.25 | 0.0714 | 0.0617 | 0.049 | 0.1632 | 0.398 | 200 |

配对域标签零分布：

| K | contrast | observed_gap | null_mean | null_sd | null_q05 | null_q95 | p_upper | p_two_sided | n_permutations |
|---|---|---|---|---|---|---|---|---|---|
| 2 | g_summary_minus_summary | -0.0 | 0.0005 | 0.0141 | -0.0 | 0.0 | 0.9661 | 1.0 | 500 |
| 2 | summary_derived_minus_summary | -0.0 | -0.0006 | 0.0205 | -0.0076 | 0.0 | 0.9461 | 1.0 | 500 |
| 2 | summary_relax_minus_summary | -0.0 | -0.0003 | 0.0296 | -0.0357 | 0.0357 | 0.9321 | 1.0 | 500 |
| 4 | g_summary_minus_summary | 0.0508 | -0.0026 | 0.0625 | -0.1071 | 0.0993 | 0.1617 | 0.3234 | 500 |
| 4 | summary_derived_minus_summary | 0.1129 | -0.0002 | 0.0487 | -0.0802 | 0.0811 | 0.022 | 0.0439 | 500 |
| 4 | summary_relax_minus_summary | -0.0 | 0.005 | 0.0695 | -0.1165 | 0.1273 | 0.5968 | 1.0 | 500 |
| 8 | g_summary_minus_summary | 0.046 | -0.0264 | 0.0781 | -0.1542 | 0.0968 | 0.1836 | 0.3673 | 500 |
| 8 | summary_derived_minus_summary | 0.1481 | -0.0026 | 0.0602 | -0.1013 | 0.0886 | 0.008 | 0.016 | 500 |
| 8 | summary_relax_minus_summary | 0.0714 | -0.0043 | 0.0749 | -0.1191 | 0.119 | 0.1497 | 0.2994 | 500 |

## 5. 严格嵌套粗化仅作为代码恒等式

| K | delta | nested_from | monotone |
|---|---|---|---|
| 8 | 0.1786 |  | True |
| 4 | 0.0 | 8.0 | True |
| 2 | 0.0 | 8.0 | True |

该单调性由同一 K=8 分区的确定性粗化保证，是实现检查，不作为原注册
`g_summary` 门的外部验证。

## 6. 低支持域杠杆

删除 `NCA_T35_C0.5`（n=2）后，K=8 Delta 从
0.1786 升至 0.5178，置换 p=
0.0005。

固定量化器的域内自助结果：shift 中位数 0.1828，
95% 区间 [0.0227,0.4326]。
它说明有限样本复合几何对低支持成员高度敏感，不能直接外推为总体定理。

| K | minimum_domain_n | n_safe_domains | n_unsafe_domains | hull_delta | min_pairwise_tv | pairwise_minus_hull |
|---|---|---|---|---|---|---|
| 4 | 1 | 5 | 2 | 0.0 | 0.25 | 0.25 |
| 4 | 3 | 4 | 2 | 0.1674 | 0.25 | 0.0826 |
| 4 | 5 | 3 | 2 | 0.2704 | 0.3929 | 0.1224 |
| 4 | 8 | 2 | 2 | 0.2704 | 0.3929 | 0.1224 |
| 4 | 10 | 2 | 1 | 0.3929 | 0.3929 | 0.0 |
| 8 | 1 | 5 | 2 | 0.1786 | 0.4286 | 0.25 |
| 8 | 3 | 4 | 2 | 0.5178 | 0.5714 | 0.0536 |
| 8 | 5 | 3 | 2 | 0.5178 | 0.5714 | 0.0536 |
| 8 | 8 | 2 | 2 | 0.5201 | 0.5714 | 0.0513 |
| 8 | 10 | 2 | 1 | 0.5714 | 0.5714 | 0.0 |

## 7. 阈值与迁移线

阈值敏感性严格恢复为主设置 (100,150) 及冻结的三组
(100,200)、(110,160)、(100,140)：

| is_registered_primary | hazard_cycles | certify_cycles | K | n_safe_domains | n_unsafe_domains | n_buffer_domains | source_unsafe_cells | source_safe_cells | delta_summary | delta_derived | delta_summary_relax | redundancy_pipeline_floor | relax_gain |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| True | 100 | 150 | 2 | 5 | 2 | 1 | 9 | 11 | 0.0 | 0.0 | 0.0 | -0.0 | -0.0 |
| True | 100 | 150 | 4 | 5 | 2 | 1 | 9 | 11 | 0.0 | 0.1129 | 0.0 | 0.1129 | -0.0 |
| True | 100 | 150 | 8 | 5 | 2 | 1 | 9 | 11 | 0.1786 | 0.3267 | 0.25 | 0.1481 | 0.0714 |
| False | 100 | 200 | 2 | 5 | 2 | 1 | 9 | 2 | 0.0 | 0.0 | 0.0 | -0.0 | -0.0 |
| False | 100 | 200 | 4 | 5 | 2 | 1 | 9 | 2 | 0.0 | 0.1129 | 0.0 | 0.1129 | -0.0 |
| False | 100 | 200 | 8 | 5 | 2 | 1 | 9 | 2 | 0.1786 | 0.3267 | 0.25 | 0.1481 | 0.0714 |
| False | 110 | 160 | 2 | 5 | 3 | 0 | 11 | 11 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| False | 110 | 160 | 4 | 5 | 3 | 0 | 11 | 11 | 0.0 | 0.0 | 0.2868 | -0.0 | 0.2868 |
| False | 110 | 160 | 8 | 5 | 3 | 0 | 11 | 11 | 0.102 | 0.192 | 0.3637 | 0.09 | 0.2616 |
| False | 100 | 140 | 2 | 5 | 2 | 1 | 9 | 12 | 0.0 | 0.0 | 0.0 | -0.0 | -0.0 |
| False | 100 | 140 | 4 | 5 | 2 | 1 | 9 | 12 | 0.0 | 0.1129 | 0.0 | 0.1129 | -0.0 |
| False | 100 | 140 | 8 | 5 | 2 | 1 | 9 | 12 | 0.1786 | 0.3267 | 0.25 | 0.1481 | 0.0714 |

G4 明确列为 `NOT_EVALUABLE`。G5 同样不评分：v01 使用一次随机拆分与一个
无条件残差半径，不是注册的留一交叉拟合，也不能提供两类条件侧错误保证。
下表仅为原 v01 数值溯源：

| target | n | side | n_unsafe | n_safe | decisiveness | observed_side_error | rho_U | rho_S | bound | bound_is_vacuous | Q2_holds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| NCA_T25_C0.5 | 17 | unsafe | 3 | 0 | 0.2941 | 0 | 1.0 |  | 1.1 | True | True |
| NCA_T25_C1.0 | 8 | unsafe | 8 | 0 | 0.875 | 0 | 1.0 |  | 1.1 | True | True |
| NCA_T25_C0.25 | 5 | safe | 0 | 5 | 1.0 | 1 |  | 0.8182 | 0.9182 | False | False |
| NCM_T45_C0.5 | 25 | safe | 0 | 25 | 1.0 | 0 |  | 0.7091 | 0.8091 | False | True |

## 8. 冻结 EOL 3×3×3 敏感性

已执行 27 个端点变体；主设置逐电芯复现 =
True。相对主设置，域等级变化数的最大值为
0。

主设置的三种分辨率：

| window | factor | persistence_k | K | n_with_eol90 | n_labelled | n_aborted | n_safe_domains | n_unsafe_domains | n_buffer_domains | min_pairwise_tv | hull_delta | pairwise_minus_hull | n_domain_grade_changes_vs_primary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 0.5 | 3 | 2 | 98 | 116 | 442 | 5 | 2 | 1 | 0.0 | 0.0 | -0.0 | 0 |
| 11 | 0.5 | 3 | 4 | 98 | 116 | 442 | 5 | 2 | 1 | 0.25 | 0.0 | 0.25 | 0 |
| 11 | 0.5 | 3 | 8 | 98 | 116 | 442 | 5 | 2 | 1 | 0.4286 | 0.1786 | 0.25 | 0 |

完整 27×3 表见 `results/eol_sensitivity_summary.csv`，逐电芯端点见
`results/eol_sensitivity_cells.csv`。

## 9. 最终科学边界

1. 注册外部门没有通过；结论为 `NOT_ESTABLISHED`，不是 PASS。
2. 注册 K=4 上出现“逐对全部分离、凸包精确碰撞”；K=8 上同一差异仍存在。
3. K=8 的绝对 Delta 未高于置换零分布，不能声称总体正分离。
4. 弛豫增益无法与当前量化管线造成的冗余分区效应区分。
5. 低支持域效应真实但属于有限样本杠杆诊断。
