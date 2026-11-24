#!/usr/bin/env python3
"""Execute the frozen 3x3x3 EOL robustness grid from raw Zhu CSV files."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

from zhu_gate.evaluate import pairwise_vs_hull
from zhu_gate.labels import domain_classes, drop_aborted, first_sustained_crossing


CFG = json.load(open(os.path.join(ROOT, "config", "registered.json"), encoding="utf-8"))
CHEM = {"d1": "NCA", "d2": "NCM"}


def parse_name(name):
    match = re.match(r"CY(\d+)-(\d+)_(\d+)-#(\d+)", name)
    if match is None:
        raise ValueError(f"unrecognized cell name: {name}")
    return f"{name}"


def capacities(raw_root, eligible_ids):
    output = {}
    for tag, chem in CHEM.items():
        folder = os.path.join(raw_root, tag)
        for filename in sorted(os.listdir(folder)):
            if not filename.endswith(".csv"):
                continue
            stem = parse_name(filename[:-4])
            cell_id = f"{chem}|{stem}"
            if cell_id not in eligible_ids:
                continue
            path = os.path.join(folder, filename)
            data = pd.read_csv(path, usecols=["cycle number", "Q discharge/mA.h"])
            data.columns = [column.strip() for column in data.columns]
            cap = data.groupby("cycle number")["Q discharge/mA.h"].max()
            output[cell_id] = cap[cap > 0]
    missing = sorted(eligible_ids - set(output))
    if missing:
        raise RuntimeError(f"raw data missing {len(missing)} released cells; first={missing[0]}")
    return output


def main(raw_root, output_dir):
    frame = pd.read_csv(os.path.join(ROOT, "data", "processed", "features.csv"))
    cap = capacities(raw_root, set(frame.cell_id))
    settings = CFG["eol"]["sensitivity"]
    cell_rows, summary_rows = [], []
    primary_grades = None
    for window in settings["window"]:
        for factor in settings["factor"]:
            for persistence in settings["k"]:
                endpoints = {}
                interrupted = 0
                for cell_id, values in cap.items():
                    clean, removed = drop_aborted(values, int(window), float(factor))
                    endpoint, _ = first_sustained_crossing(
                        clean, CFG["eol"]["primary_frac"], int(persistence)
                    )
                    endpoints[cell_id] = endpoint
                    interrupted += removed
                    cell_rows.append({
                        "window": int(window), "factor": float(factor),
                        "persistence_k": int(persistence), "cell_id": cell_id,
                        "eol90": endpoint, "n_aborted": int(removed),
                    })
                variant = frame.copy()
                variant["eol90"] = variant.cell_id.map(endpoints)
                labelled, psi = domain_classes(
                    variant, CFG["grades"]["hazard_eol_cycles"],
                    CFG["grades"]["psi_safe_max"], CFG["grades"]["psi_unsafe_min"]
                )
                grades = psi.cls.to_dict()
                if (window, factor, persistence) == (
                    CFG["eol"]["abort_window"], CFG["eol"]["abort_factor"],
                    CFG["eol"]["sustain_k"]
                ):
                    primary_grades = grades
                for K in CFG["quantizer"]["K_nested"]:
                    pairwise, hull = pairwise_vs_hull(labelled, grades, int(K))
                    summary_rows.append({
                        "window": int(window), "factor": float(factor),
                        "persistence_k": int(persistence), "K": int(K),
                        "n_with_eol90": int(variant.eol90.notna().sum()),
                        "n_labelled": int(len(labelled)),
                        "n_aborted": int(interrupted),
                        "n_safe_domains": int((psi.cls == "S").sum()),
                        "n_unsafe_domains": int((psi.cls == "U").sum()),
                        "n_buffer_domains": int((psi.cls == "A").sum()),
                        "min_pairwise_tv": float(pairwise.tv.min()),
                        "hull_delta": float(hull),
                        "pairwise_minus_hull": float(pairwise.tv.min() - hull),
                    })

    cells = pd.DataFrame(cell_rows)
    summary = pd.DataFrame(summary_rows)
    primary_grades = primary_grades or {}
    stability = []
    for (window, factor, persistence), group in cells.groupby(["window", "factor", "persistence_k"]):
        variant = frame.copy()
        variant["eol90"] = variant.cell_id.map(group.set_index("cell_id").eol90)
        _, psi = domain_classes(variant, CFG["grades"]["hazard_eol_cycles"],
                                CFG["grades"]["psi_safe_max"], CFG["grades"]["psi_unsafe_min"])
        grades = psi.cls.to_dict()
        stability.append({
            "window": int(window), "factor": float(factor), "persistence_k": int(persistence),
            "n_domain_grade_changes_vs_primary": int(sum(
                grades.get(domain) != primary_grades.get(domain)
                for domain in set(grades) | set(primary_grades)
            )),
        })
    summary = summary.merge(pd.DataFrame(stability),
                            on=["window", "factor", "persistence_k"], how="left")
    os.makedirs(output_dir, exist_ok=True)
    cells.to_csv(os.path.join(output_dir, "eol_sensitivity_cells.csv"), index=False,
                 float_format="%.12g")
    summary.to_csv(os.path.join(output_dir, "eol_sensitivity_summary.csv"), index=False,
                   float_format="%.12g")
    audit = {
        "variants": int(len(stability)),
        "cells": int(len(frame)),
        "all_primary_endpoints_reproduced": bool(np.allclose(
            cells[(cells.window == CFG["eol"]["abort_window"])
                  & (cells.factor == CFG["eol"]["abort_factor"])
                  & (cells.persistence_k == CFG["eol"]["sustain_k"])]
            .set_index("cell_id").eol90.reindex(frame.cell_id),
            frame.eol90, equal_nan=True,
        )),
        "maximum_domain_grade_changes": int(summary.n_domain_grade_changes_vs_primary.max()),
        "n_with_eol90_range": [int(summary.n_with_eol90.min()), int(summary.n_with_eol90.max())],
        "n_aborted_range": [int(summary.n_aborted.min()), int(summary.n_aborted.max())],
    }
    with open(os.path.join(output_dir, "eol_sensitivity_audit.json"), "w", encoding="utf-8") as handle:
        json.dump(audit, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True, help="directory containing d1/ and d2/")
    parser.add_argument("--out", default=os.path.join(ROOT, "results"))
    args = parser.parse_args()
    main(args.raw, args.out)
