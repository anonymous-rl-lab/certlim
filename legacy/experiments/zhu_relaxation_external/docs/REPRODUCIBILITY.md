# 可复现性说明

## 离线数值复现

包内提供 118 个电芯的冻结特征表。安装 `requirements-lock.txt` 后运行：

```bash
bash scripts/run_all.sh
```

脚本先校验发布清单，再运行数值分析、报告生成和测试，最后再次校验同一份
发布清单。它**不会**在校验前重写正确答案。

`results/runtime.json` 与 `results/environment.json` 分别记录墙钟时间和实际
环境，二者不进入发布产物的逐字节清单。CSV 使用固定有效位数输出。

## 原始数据复现

原始数据不随包分发。下载并解压后，建立包含 `d1/` 与 `d2/` 的目录，然后运行：

```bash
PYTHONPATH=src python3 scripts/01_extract_features.py --raw /path/to/raw-root
PYTHONPATH=src python3 scripts/05_run_eol_sensitivity.py --raw /path/to/raw-root
PYTHONPATH=src python3 scripts/06_verify_raw_features.py --raw /path/to/raw-root
```

主设置必须满足：发布特征表逐数值一致，且 3×3×3 输出中主设置逐电芯
EOL@90 一致。

## 清单语义

`MANIFEST.sha256` 覆盖发布代码、文档、冻结输入和确定性结果；忽略：

- `MANIFEST.sha256` 自身；
- `results/runtime.json`；
- `results/environment.json`；
- `data/raw/`、缓存和字节码。

校验器同时检查哈希不符、缺失文件和未登记的额外文件。
