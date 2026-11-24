#!/usr/bin/env python3
"""Re-extract raw features to a temporary path and compare with the release."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load_extractor():
    path = os.path.join(ROOT, "scripts", "01_extract_features.py")
    spec = importlib.util.spec_from_file_location("zhu_extract_features", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(raw_root, output):
    released = pd.read_csv(os.path.join(ROOT, "data", "processed", "features.csv"))
    with tempfile.TemporaryDirectory(prefix="zhu-raw-reproduction-") as temporary:
        candidate_path = os.path.join(temporary, "features.csv")
        load_extractor().main(raw_root, candidate_path)
        candidate = pd.read_csv(candidate_path)
    same_columns = list(released.columns) == list(candidate.columns)
    same_ids = list(released.cell_id) == list(candidate.cell_id)
    numeric = [column for column in released.columns
               if pd.api.types.is_numeric_dtype(released[column])]
    text = [column for column in released.columns if column not in numeric]
    max_difference = 0.0
    n_differences = 0
    if same_columns and same_ids:
        left = released[numeric].to_numpy(float)
        right = candidate[numeric].to_numpy(float)
        difference = np.abs(left - right)
        max_difference = float(np.nanmax(difference))
        n_differences = int(np.sum(np.nan_to_num(difference, nan=0.0) > 1e-12))
        same_text = bool(released[text].fillna("").equals(candidate[text].fillna("")))
    else:
        same_text = False
    result = {
        "status": "PASS" if (same_columns and same_ids and same_text and n_differences == 0) else "FAIL",
        "released_shape": list(released.shape),
        "reextracted_shape": list(candidate.shape),
        "columns_exact": same_columns,
        "cell_order_exact": same_ids,
        "text_exact": same_text,
        "max_numeric_absolute_difference": max_difference,
        "numeric_differences_over_1e-12": n_differences,
    }
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="directory containing d1/ and d2/")
    parser.add_argument("--out", default=os.path.join(ROOT, "results", "raw_feature_reproduction.json"))
    args = parser.parse_args()
    raise SystemExit(main(args.raw, args.out))
