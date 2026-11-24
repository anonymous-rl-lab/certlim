# 主张与证据 — v01.1

注册结果与事后诊断严格分层；`Supported diagnostic` 不等于确认性门通过。

| 主张 | 状态 | 证据边界 |
|---|---:|---|
| 原始 CSV 可逐列重建发布特征表 | **Supported** | status=PASS, max numeric difference=0 |
| 冻结注册外部门通过 | **Not established** | G2 fails; G1, G4 and G5 are not evaluable under the frozen implementation |
| 注册 K=4 下逐对分离但复合凸包碰撞 | **Supported diagnostic** | min pairwise=0.2500, hull Delta=0.0000, gap permutation p=0.0075; registered resolution but post-hoc contrast |
| K=8 下逐对 TV 高估凸包可分离度 | **Supported diagnostic** | min pairwise=0.4286, hull Delta=0.1786, gap permutation p=0.0165; K=8 是分辨率敏感性 |
| K=8 绝对凸包 Delta 高于置换零分布 | **Not established** | Delta=0.1786, p=0.2234 |
| 弛豫通道提供超出冗余管线的可分离度增益 | **Not established** | relax gain=+0.0714, pipeline floor=+0.1481, within-domain pairing p=0.3980 |
| 弛豫通道没有信息 | **Not tested** | 负结果只针对当前有限样本量化管线，不能证伪通道信息 |
| 严格粗化使 Delta 单调不增 | **Code invariant** | 同一 K=8 分区粗化为 K=4/K=2；结构上必然成立，不是外部实证 |
| 低支持安全域显著影响经验凸包 | **Supported diagnostic** | drop NCA_T35_C0.5(n=2): Delta 0.1786->0.5178, permutation p=0.0005; population claim not made |
| 迁移侧错误界被外部验证 | **Not evaluable** | v01 calibration is unconditional and does not implement the registered class-conditional procedure |
| 弛豫是理论意义上的独立因果代理 | **Not established** | 仅为非派生测量通道；没有验证条件独立性或完备性 |
| 跨化学因果认证得到验证 | **Not established** | domain identity explains 88.6% of log10(EOL) variance |
| EOL 3x3x3 稳健性网格已执行 | **Completed** | 27 variants; maximum domain-grade changes=0 |
