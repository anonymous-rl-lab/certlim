# 第三方声明

## 数据

NASA PCoE *Randomized Battery Usage Data Set*,DOI `10.5281/zenodo.15277374`,许可 **CC BY 4.0**。
引用要求(数据集文档指定):B. Bole, C. Kulkarni, M. Daigle, "Adaptation of an Electrochemistry-based
Li-Ion Battery Model to Account for Deterioration Observed Under Randomized Use," *Annual Conference of
the Prognostics and Health Management Society*, 2014.

原始归档不随本包分发,由 `scripts/00_download_and_extract.sh` 从 Zenodo 获取。
`data/steps.parquet` 是上述数据的派生物,同样受 CC BY 4.0 约束。

## 软件依赖

NumPy(BSD-3)、pandas(BSD-3)、SciPy(BSD-3)、pyarrow(Apache-2.0)。

本次派生表增加了持续时间字段，并以 gzip CSV 保存选定列，保留所用原始记录。该包将上传的步级 Parquet 作为上游数据，构建脚本可在原 certlimrepro.zip 中找到。NASA 数据的 CC BY 4.0 适用于该派生表。
