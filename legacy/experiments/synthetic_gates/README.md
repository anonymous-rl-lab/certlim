# v04 Causal Safety Certification Gates

这是理论章节 v04 的独立生死门实验包。它刻意不复用 v51 的连续 Gaussian 代理、RFF 检验或混杂偏差标签，以免理论与代码再次错位。

## 运行顺序

```bash
python -m unittest discover -s tests -v
python scripts/run_gates.py smoke
python scripts/run_gates.py small
```

`smoke` 是 10 分钟预算内的确定性代数与 LP 审计；只有通过后才运行 `small`。`small` 在 1 小时预算内计算 \(n\le128\) 的精确前沿，并用冻结种子校验二元代理检验的精确二项尾概率。

## 输出

- `collision.csv`：旧证据 TV 与派生特征负对照；
- `policy_flip.csv`：两种部署动作下的风险与等级翻转；
- `proxy_geometry.csv`：增强证据 TV、\(T=1\{A=W\}\) 的均值差与 \(\delta\)；
- `delta_frontier.csv`：LP 原问题、对偶分离、\(\Delta(n)\)、\(\gamma(n)\)、必要无 Alert 门及 Hoeffding 设计；
- `proxy_exact_rates.csv` 与 `proxy_mc_*.csv`：small 阶段有限样本核验；
- `gates.json`、`summary.json`、`runtime.json` 与 `REPORT.md`：机器可读和人工可读审计。

Bernoulli 有限块 LP 使用成功次数作为充分统计量，把 \(2^n\) 个序列状态无损压缩为 \(n+1\) 个计数状态；这项压缩只用于当前 iid Bernoulli 见证，不被宣称为一般有限字母表算法。

当前没有注册 formal 阶段。若 small 通过，正式规模、种子、算力、预计时长与成本需另行冻结后再启动。
