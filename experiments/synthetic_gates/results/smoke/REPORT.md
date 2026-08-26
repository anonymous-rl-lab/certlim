# v04 生死门实验报告：smoke

**总判定：PASS**

- 理论版本：`v04`
- 实验版本：`v04-gates-0.1.0`
- 冻结配置 SHA-256：`62be13f80dba48f464b53dec8a92865eb6a070acce666b70b33538f927afa9b4`
- 运行时：0.105 秒（CPU；GPU 未使用；外部 API 成本 0 美元）
- 随机种子：无；本阶段为确定性精确计算

## 门控结果

| Gate | 结果 | 观测值 | 预注册判据 |
|---|---:|---|---|
| G1_exact_old_evidence_collision | PASS | `2.7755575615628914e-17` | max TV <= 1e-08 |
| G2_policy_grade_flip | PASS | `0` | zero grade mismatches for both policies |
| G3_data_processing_negative_control | PASS | `2.7755575615628914e-17` | TV of XOR-derived old evidence <= 1e-08 |
| G4_probability_normalization | PASS | `2.220446049250313e-16` | max mass residual <= 1e-08 |
| G5_registered_proxy_breaks_gate | PASS | `{"min_augmented_tv": 0.015811388300841916, "max_formula_residual": 1.942890293094024e-16}` | all augmented TV > 1e-08 and formula residual <= 1e-08 |
| G6_finite_block_landmarks | PASS | `{"delta_1": 5.551115123125783e-17, "delta_2": 0.1250000000000001, "gamma_2": 0.0625, "n_star": 2, "max_residual": 1.1102230246251565e-16}` | Delta(1)=0, Delta(2)=1/8, gamma(2)=1/16, n*=2 |
| G7_frontier_monotonicity | PASS | `0.0014648437500002776` | min Delta(n)-Delta(n-1) >= -1e-08 |
| G8_sion_primal_dual_identity | PASS | `6.106226635438361e-16` | max |primal TV-dual gap| <= 1e-08 |

## 核心读数

- 旧证据有限块见证：`Delta(1)=5.55111512313e-17`，`Delta(2)=0.125`。
- 当前网格代理最弱分离：`min TV=0.0158113883008`；这验证注册成对 SCM，不外推为一般代理识别。

## 解释边界

本报告是注册 SCM 类上的理论—代码验算。它验证精确碰撞、凸包距离、Sion 对偶、有限样本代理率及相应门槛；不构成电池、车辆或工业部署的经验验证。缓冲带 `Theta_A` 也不受极端区域二元规则保护。
