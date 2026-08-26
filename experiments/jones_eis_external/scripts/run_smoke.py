#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from jones_eis import extract_dataset  # noqa: E402


def file_md5(path: Path) -> str:
    digest = hashlib.md5()  # noqa: S324 - source publishes MD5 for integrity
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=PROJECT / "data" / "raw" / "chemistry2-35C",
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=PROJECT / "data" / "downloads" / "chemistry2-35C.zip",
    )
    parser.add_argument("--config", type=Path, default=PROJECT / "config" / "smoke.json")
    parser.add_argument("--output", type=Path, default=PROJECT / "results" / "smoke")
    args = parser.parse_args()

    config = json.loads(args.config.read_text())
    gates = config["gates"]
    args.output.mkdir(parents=True, exist_ok=True)

    observed_md5 = file_md5(args.archive)
    frame, errors, metadata = extract_dataset(args.raw_root, config["n_frequency"])
    frame.to_csv(args.output / "cycles.csv", index=False)
    errors.to_csv(args.output / "errors.csv", index=False)

    per_cell = frame.groupby("cell").size() if not frame.empty else np.array([])
    action_std = {
        column: float(frame[column].std())
        for column in ("charge_stage1_ma", "charge_stage2_ma", "discharge_current_ma")
    }
    completeness = metadata["n_complete_cycles"] / max(metadata["n_expected_cycles"], 1)
    chronology_rate = float(frame["chronology_ok"].mean()) if len(frame) else 0.0
    checks = {
        "archive_checksum": observed_md5 == config["archive_md5"],
        "cell_count": metadata["n_cells_discovered"] >= gates["minimum_cells"],
        "complete_cycle_count": metadata["n_complete_cycles"] >= gates["minimum_complete_cycles"],
        "cycles_per_cell": bool(len(per_cell) and per_cell.min() >= gates["minimum_cycles_per_cell"]),
        "pairing_and_parse_completeness": completeness >= gates["minimum_completeness"],
        "protocol_chronology": chronology_rate >= gates["minimum_chronology_rate"],
        "eis_support": bool(len(frame) and frame["eis_rows"].min() >= gates["minimum_eis_rows"]),
        "action_variation": all(value >= gates["minimum_action_std_ma"] for value in action_std.values()),
        "finite_outcomes": bool(len(frame) and np.isfinite(frame["soh"]).all()),
    }
    summary = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "config": config,
        "observed_archive_md5": observed_md5,
        "metadata": metadata,
        "completeness": completeness,
        "chronology_rate": chronology_rate,
        "cycles_per_cell": {
            "minimum": int(per_cell.min()) if len(per_cell) else 0,
            "median": float(per_cell.median()) if len(per_cell) else 0,
            "maximum": int(per_cell.max()) if len(per_cell) else 0,
        },
        "action_std_ma": action_std,
        "outcome_audit": {
            "soh_min": float(frame["soh"].min()) if len(frame) else None,
            "soh_median": float(frame["soh"].median()) if len(frame) else None,
            "soh_max": float(frame["soh"].max()) if len(frame) else None,
            "count_soh_le_0_95": int((frame["soh"] <= 0.95).sum()) if len(frame) else 0,
            "count_soh_le_0_90": int((frame["soh"] <= 0.90).sum()) if len(frame) else 0,
        },
        "checks": checks,
    }
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# Jones EIS smoke report",
        "",
        f"**Overall: {summary['status']}**",
        "",
        "## Gates",
        "",
        "| Gate | Result |",
        "|---|---:|",
    ]
    lines.extend(f"| {key} | {'PASS' if value else 'FAIL'} |" for key, value in checks.items())
    lines.extend(
        [
            "",
            "## Audit counts",
            "",
            f"- Cells: {metadata['n_cells_discovered']}",
            f"- Expected cycle triplets: {metadata['n_expected_cycles']}",
            f"- Complete parsed cycles: {metadata['n_complete_cycles']}",
            f"- Explicit errors: {metadata['n_errors']}",
            f"- Completeness: {completeness:.3%}",
            f"- Chronology pass rate: {chronology_rate:.3%}",
            f"- Cycles/cell: {summary['cycles_per_cell']}",
            "",
            "## Evaluability audit (not a result)",
            "",
            f"- SOH range: {summary['outcome_audit']['soh_min']:.4f} to {summary['outcome_audit']['soh_max']:.4f}",
            f"- SOH ≤ 0.95: {summary['outcome_audit']['count_soh_le_0_95']}",
            f"- SOH ≤ 0.90: {summary['outcome_audit']['count_soh_le_0_90']}",
            "- This section only determines whether a registered endpoint is supportable; it is not inferential evidence.",
        ]
    )
    (args.output / "report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
