# Zhu 2022 电压弛豫外部认证门 v01.1

这是 v01 的**审计纠偏版**。冻结协议与冻结配置保持原哈希；专家自审和独立
复核发现的错误全部留在 `docs/PROTOCOL_ERRATA.md`，原 v01 结果完整保存在
`results/legacy_v01/`。

## 最终裁决

**注册外部门：NOT_ESTABLISHED。**  
**事后纠偏层：DIAGNOSTIC_ONLY。**

没有合并的 `overall_pass`，因为冻结门与事后修正门不能混成一个裁决。

## 主要结果

1. 注册主分辨率 **K=4** 下，最小逐对 TV 为 0.25，但凸包 Delta 为 0：
   所有安全—危险域逐对均分离，复合凸包却精确碰撞。这是注册分辨率上的
   事后几何诊断，不等于注册外部门通过。
2. 在分辨率敏感性 **K=8** 下，最小逐对 TV 为 0.4286，凸包 Delta 为 0.1786；
   逐对减凸包差经 2,000 次置换校准后仍显著。这支持“逐对距离可高估复合
   可分离度”的经验诊断，但不是注册主结果。
3. 域内弛豫配对置换已按冻结协议补跑 200 次。当前管线下，弛豫表观增益
   没有超过确定性冗余特征造成的管线底；结论是**额外增益未建立**，不是
   “弛豫没有信息”。
4. 删除一个 n=2 的安全域会显著改变 K=8 经验凸包；该结果被限定为低支持
   有限样本杠杆诊断。
5. G4 与 G5 均明确列为 `NOT_EVALUABLE`，不再被省略或用无效校准硬判。

精确数字与 p 值见 `results/GATE_REPORT.md`。

## 快速复现

```bash
python3 -m pip install -r requirements-lock.txt
bash scripts/run_all.sh
```

`run_all.sh` 在重跑前后校验同一份发布清单，绝不自动重建清单。

原始数据复现和清单语义见 `docs/REPRODUCIBILITY.md`。

## 证据分层

```text
results/as_registered_gates.json    冻结口径的名义结果与有效性判定
results/corrected_diagnostics.json  事后纠偏诊断，不覆盖冻结裁决
results/legacy_v01/                 v01 原始产物，原样保留
docs/PROTOCOL_ERRATA.md             原专家自审错误 + 独立审计新增错误
docs/CORRECTION_PROTOCOL_v01_1.md   v01.1 解释规则
```

## 数据与许可

代码采用 MIT 许可。Zhu 数据采用 CC BY 4.0，原始数据不随包分发。
