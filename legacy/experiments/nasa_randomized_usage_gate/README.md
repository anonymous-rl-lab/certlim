# NASA 随机使用外部认证门

第四个真实系统外部门,配套理论章 *Safety-Certification Limits under Partial Causal Identifiability* (v04)。
与前三个(Jones EIS / Severson MATR / Zhu 弛豫)的根本区别:**动作由已知概率分布随机分配**,
因此 P(H=1 | Z, do(A)) 可识别,Ψ 是真值而不是代理。

## 为什么换这个数据集

前三个实验对主定理支撑有限,原因是结构性的:

| 定理需要 | 观测型电池数据集给的 | 本数据集 |
|---|---|---|
| 同一 θ 下重复抽取 n 个 iid 证据,n 可变 | 一芯一条命,每域 5–28 芯 | **每 θ 单元 150–4000 步** |
| Θ_S、Θ_U 各有多个成员 | Zhu:5 安全 / 2 危险 | **738 安全 / 528 危险** |
| 安全等级独立于域身份 | Zhu:η² = 0.886,等级 ≡ 协议 | **Ψ 随 π 变 3–5 倍** |
| 能验证 Θ_sf 非空 | 不可能(Ψ 不可识别) | **已构造并验证** |

## 冻结结论

| 门 | 内容 | 结果 |
|---|---|:--|
| G1 | 𝒟(n) ≤ min(1, α+β+Δ_E(n)) | **PASS**,11 个 n 全部成立 |
| G2 | 碰撞区 𝒟 = α+β(界可达) | **PASS**,𝒟 = 0.100000 精确 |
| G3 | Δ_E(n) 单调不减 | **PASS**,0.149 → 0.556 |
| G4 | n⋆ 有限;Sion 恒等式 γ = Δ/2 | **PASS**,n⋆ = 1,残差 ≤ 9.3e-9 |
| G5 | Θ_sf 非空(碰撞被构造并验证) | **PASS**,Δ = 0.000000 |
| G6 | 碰撞下界成立 | **PASS** |

> 三句话:**主定理的界在真值可识别的真实数据上被直接检验并成立;界在碰撞区是可达的,不只是上界;
> 跨等级碰撞第一次被构造出来并验证 —— 而且构造它的是一个「热时降载、凉时加载」的合理热降额策略。**
>
> 附带一个负面结果:**自然混杂不一定制造碰撞**。朴素的「高温→重载」混杂反而把 Δ 从 0.0869 抬到 0.0953。

## 快速审计(无需原始数据)

```bash
pip install -r requirements.txt
bash scripts/run_all.sh          # 约 10 分钟,含 n=20 的 LP
```

`data/steps.parquet`(389,307 步 × 28 芯)随包分发,`02` 之后全部可离线复现。

## 从原始数据完整复现

```bash
bash scripts/00_download_and_extract.sh ./data/raw   # 约 1.07 GB
PYTHONPATH=src python3 scripts/01_extract_steps.py
```

## 目录

```
├── config/registered.json      冻结配置(哈希见 results/freeze.json)
├── docs/
│   ├── FROZEN_PROTOCOL.md      冻结协议,逐字节不可改
│   ├── PROTOCOL_ERRATA.md      3 处协议偏离 + 1 个运行中发现的代码 bug,未回写
│   ├── DATA_PROVENANCE.md      溯源、倾向性的独立验证、处理要点
│   └── CLAIM_STATUS.md         主张 ↔ 证据(由脚本生成)
├── src/nasa_gate/core.py       多项计数实验、凸包 TV LP、𝒟 的精确 LP、Sion 对偶
├── scripts/                    00 下载 · 01 提步 · 02 建模型 · 03 L1/L2 · 04/05 L3 · 06 零校准 · 07/08 报告
├── data/steps.parquet          随包分发
├── results/                    全部结果 + GATE_REPORT.md
└── tests/test_core.py          覆盖判决路径,含 0·log0 bug 的回归测试
```

## 必读的解释边界

1. 危害 H 是 **3.2 V 保护介入**,不是事故。论文须以「保护介入率」表述。
2. 每子集 4 芯;θ = (芯 × 阶段) 撑到 513 个单元,同芯单元不独立,置换以**电芯**为块。
3. 均匀臂无 5 A 档,跨臂评估限于 A ∈ {1,2,3,4}。
4. 步内条件 iid 由实测支持(条件于状态箱后 lag-1 相关中位 −0.020),非严格独立。
5. 全部结论相对于本包**注册的**模型类成立。

## 许可

代码 MIT(`LICENSE`)。数据 CC BY 4.0,归 NASA PCoE 所有,不随包分发。
