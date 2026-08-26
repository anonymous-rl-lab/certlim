# Jones EIS external gates

本子包将 Jones chemistry-2 数据映射到 v04 有限证据认证框架：

- 25 °C：32 个训练/校准电芯；
- 35 °C：16 个锁定外测电芯；
- 证据时序：充电前 EIS → 随机动作 → 放电容量结局；
- 审计纠偏结果：真实 EIS 相对置乱 EIS 保留小幅跨温度容量预测价值，但跨温度三决策认证仍 FAIL；预测精度与安全认证能力反向移动。

原始数据不在代码总包中。先按根目录 `docs/DATA_PROVENANCE.md` 下载并校验，然后运行：

```bash
PYTHONPATH=src python scripts/run_smoke.py \
  --raw-root data/raw/chemistry2-25C \
  --archive data/downloads/chemistry2-25C.zip \
  --config config/smoke25.json \
  --output results/smoke25

PYTHONPATH=src python scripts/run_smoke.py \
  --raw-root data/raw/chemistry2-35C \
  --archive data/downloads/chemistry2-35C.zip \
  --config config/smoke.json \
  --output results/smoke35_cubic

python scripts/run_cross_temperature_audit.py \
  --train-cycles /path/to/chemistry2-25C-cycles.csv \
  --test-cycles /path/to/chemistry2-35C-cycles.csv

python scripts/run_small.py \
  --cycles /path/to/chemistry2-35C-cycles.csv \
  --config config/small_audit_rerun.json \
  --output results/small_cubic_audit_rerun

python scripts/run_nested_geometry.py \
  --cycles /path/to/chemistry2-35C-cycles.csv \
  --config config/nested_geometry_audit_rerun.json \
  --output results/nested_geometry_audit_rerun
```

旧结果保留在原目录，仅作 provenance。审计纠偏后的唯一正式结果位于 `results/*_audit_rerun/`；完整裁决见 `JONES_EIS_GATE_REPORT.md`。
