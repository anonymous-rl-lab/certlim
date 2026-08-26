#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from run_small import (  # noqa: E402
    add_history,
    convex_hull_tv,
    feature_menus,
    permute_eis_within_cell,
    product_rows,
)


def histogram(labels: np.ndarray, environments: pd.Series, index: pd.Index, bins: int) -> pd.DataFrame:
    table = pd.crosstab(environments, labels, normalize="index")
    return table.reindex(index=index, columns=range(bins), fill_value=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycles", type=Path, default=PROJECT / "results" / "smoke35_cubic" / "cycles.csv")
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT / "config" / "nested_geometry_audit_rerun.json",
    )
    parser.add_argument("--output", type=Path, default=PROJECT / "results" / "nested_geometry")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if config["status"] != "AUDIT_LOCKED_BEFORE_CORRECTED_RERUN":
        raise RuntimeError("nested geometry protocol is not audit-locked")
    observed_hash = hashlib.sha256(args.cycles.read_bytes()).hexdigest()
    if observed_hash != config["input_cycle_sha256"]:
        raise RuntimeError(f"cycle-table hash mismatch: {observed_hash}")
    args.output.mkdir(parents=True, exist_ok=True)

    frame = add_history(pd.read_csv(args.cycles))
    permuted = permute_eis_within_cell(frame, seed=config["permutation_seed"])
    menus = feature_menus(frame)
    old_columns = menus["old_history"]
    eis_columns = sorted(
        column for column in frame if column.startswith("eis_re_") or column.startswith("eis_neg_im_")
    )

    risks = frame.groupby("environment").agg(
        n=("under_delivery", "size"), risk=("under_delivery", "mean")
    )
    risks = risks[risks.n >= config["minimum_observations"]]
    grades = pd.Series("buffer", index=risks.index)
    grades.loc[risks.risk <= config["safe_risk_upper"]] = "safe"
    grades.loc[risks.risk >= config["unsafe_risk_lower"]] = "unsafe"
    rows: list[dict[str, object]] = []

    old_bins = config["old_history_bins"]
    eis_bins = config["eis_bins"]
    for seed in config["quantizer_seeds"]:
        old_transform = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            PCA(n_components=min(10, len(old_columns)), random_state=seed),
        )
        old_coordinates = old_transform.fit_transform(frame[old_columns])
        old_labels = KMeans(n_clusters=old_bins, n_init=20, random_state=seed).fit_predict(old_coordinates)

        eis_transform = make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            PCA(n_components=10, random_state=seed),
        )
        eis_coordinates = eis_transform.fit_transform(frame[eis_columns])
        eis_cluster = KMeans(n_clusters=eis_bins, n_init=20, random_state=seed).fit(eis_coordinates)
        eis_labels = eis_cluster.labels_
        permuted_eis_labels = eis_cluster.predict(eis_transform.transform(permuted[eis_columns]))

        label_sets = {
            "old_history": (old_labels, old_bins),
            "old_history_eis_nested": (
                eis_bins * old_labels + eis_labels,
                old_bins * eis_bins,
            ),
            "old_history_eis_permuted_nested": (
                eis_bins * old_labels + permuted_eis_labels,
                old_bins * eis_bins,
            ),
        }
        for menu, (labels, bins) in label_sets.items():
            hist = histogram(labels, frame["environment"], risks.index, bins)
            safe = hist.loc[grades == "safe"].to_numpy(float)
            unsafe = hist.loc[grades == "unsafe"].to_numpy(float)
            for block_length in config["block_lengths"]:
                rows.append(
                    {
                        "menu": menu,
                        "seed": seed,
                        "block_length": block_length,
                        "delta_hat": convex_hull_tv(
                            product_rows(safe, block_length), product_rows(unsafe, block_length)
                        ),
                        "safe_environments": int((grades == "safe").sum()),
                        "buffer_environments": int((grades == "buffer").sum()),
                        "unsafe_environments": int((grades == "unsafe").sum()),
                    }
                )

    results = pd.DataFrame(rows)
    results.to_csv(args.output / "geometry.csv", index=False, float_format="%.12g")
    pivot = results.pivot(index=["seed", "block_length"], columns="menu", values="delta_hat")
    structural_invariants = {
        "nested_eis_dominates_old": bool(
            (pivot["old_history_eis_nested"] >= pivot["old_history"] - 1e-8).all()
        ),
        "nested_permuted_dominates_old": bool(
            (pivot["old_history_eis_permuted_nested"] >= pivot["old_history"] - 1e-8).all()
        ),
        "block_monotonicity": bool(
            results.sort_values("block_length")
            .groupby(["menu", "seed"])["delta_hat"]
            .apply(lambda values: np.all(np.diff(values.to_numpy()) >= -1e-8))
            .all()
        ),
    }
    aggregate = results.groupby(["menu", "block_length"])["delta_hat"].agg(["median", "min", "max"])
    contrast = pivot["old_history_eis_nested"] - pivot["old_history_eis_permuted_nested"]
    contrast_rows = []
    for block_length, values in contrast.groupby(level="block_length"):
        contrast_rows.append(
            {
                "block_length": int(block_length),
                "median_real_minus_permuted": float(values.median()),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "positive_seeds": int((values > 0).sum()),
                "n_seeds": int(len(values)),
            }
        )
    contrasts = pd.DataFrame(contrast_rows)
    contrasts.to_csv(args.output / "real_vs_permuted_contrast.csv", index=False, float_format="%.12g")
    summary = {
        "status": "COMPLETE" if all(structural_invariants.values()) else "INVALID",
        "classification": config["classification"],
        "method": config["method"],
        "warning": "nested dominance is a structural invariant, not empirical evidence that EIS is informative",
        "aggregate": {
            f"{menu}_n{block}": {key: float(value) for key, value in row.items()}
            for (menu, block), row in aggregate.to_dict(orient="index").items()
        },
        "real_vs_permuted_contrast": contrasts.set_index("block_length").to_dict(orient="index"),
        "structural_invariants": structural_invariants,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.output / "config_snapshot.json").write_text(json.dumps(config, indent=2) + "\n")
    environment = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": importlib.metadata.version("numpy"),
        "pandas": importlib.metadata.version("pandas"),
        "scipy": importlib.metadata.version("scipy"),
        "scikit_learn": importlib.metadata.version("scikit-learn"),
    }
    (args.output / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    lines = [
        "# Jones nested-geometry audit rerun",
        "",
        f"**Status: {summary['status']}**",
        "",
        "> Nested dominance is a structural invariant of evidence refinement, not an empirical PASS.",
        "",
        "## Real-versus-permuted exploratory contrast",
        "",
        "| block length | median real - permuted | min | max | positive seeds |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in contrasts.itertuples(index=False):
        lines.append(
            f"| {row.block_length} | {row.median_real_minus_permuted:.4f} | "
            f"{row.minimum:.4f} | {row.maximum:.4f} | {row.positive_seeds}/{row.n_seeds} |"
        )
    lines.extend(["", "## Structural invariants", "", "| invariant | result |", "|---|---:|"])
    lines.extend(
        f"| {name} | {'PASS' if value else 'FAIL'} |"
        for name, value in structural_invariants.items()
    )
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
