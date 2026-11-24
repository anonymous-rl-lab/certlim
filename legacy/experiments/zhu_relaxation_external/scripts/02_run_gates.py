#!/usr/bin/env python3
"""Run registered analyses and post-hoc diagnostics as separate evidence layers."""
from __future__ import annotations

import json
import os
import platform
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))

import numpy
import pandas
import scipy
import sklearn

from zhu_gate.labels import domain_classes
from zhu_gate.geometry import (
    channel_pairing_permutation,
    delta_from_codes,
    geometry_permutation_diagnostics,
    low_support_bootstrap,
    paired_delta_difference,
    quantize,
    support_sensitivity,
)
from zhu_gate.evaluate import (
    a_line,
    b_line,
    evaluate_corrected_diagnostics,
    evaluate_registered_gates,
    leave_one_domain,
    nesting_check,
    pairwise_vs_hull,
)
from zhu_gate.menus import build_menus, relax_columns, summary_columns


CFG = json.load(open(os.path.join(ROOT, "config", "registered.json"), encoding="utf-8"))
RES = os.path.join(ROOT, "results")
G, Q = CFG["grades"], CFG["quantizer"]


def write_csv(frame, name):
    frame.to_csv(os.path.join(RES, name), index=False, float_format="%.12g")


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean_json(v) for v in value]
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if not np.isfinite(value) else float(value)
    return value


def write_json(value, name):
    with open(os.path.join(RES, name), "w", encoding="utf-8") as handle:
        json.dump(clean_json(value), handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def threshold_grid(frame):
    pairs = [(G["hazard_eol_cycles"], G["certify_eol_cycles"], True)]
    pairs.extend((int(h), int(c), False) for h, c in G["threshold_sensitivity"])
    rows = []
    for hazard, certify, primary in pairs:
        labelled, psi = domain_classes(frame, hazard, G["psi_safe_max"], G["psi_unsafe_min"])
        dom_class = psi.cls.to_dict()
        menus = build_menus(labelled)
        source = frame[(frame.domain == CFG["transfer"]["source"]) & frame.eol90.notna()]
        for K in Q["K_nested"]:
            deltas = {
                name: delta_from_codes(quantize(menus[name], K), labelled.domain.values,
                                       dom_class, K)
                for name in ("summary", "summary_derived", "summary_relax")
            }
            rows.append({
                "is_registered_primary": primary,
                "hazard_cycles": hazard,
                "certify_cycles": certify,
                "K": K,
                "n_safe_domains": int((psi.cls == "S").sum()),
                "n_unsafe_domains": int((psi.cls == "U").sum()),
                "n_buffer_domains": int((psi.cls == "A").sum()),
                "source_unsafe_cells": int((source.eol90 <= hazard).sum()),
                "source_safe_cells": int((source.eol90 >= certify).sum()),
                "delta_summary": deltas["summary"],
                "delta_derived": deltas["summary_derived"],
                "delta_summary_relax": deltas["summary_relax"],
                "redundancy_pipeline_floor": deltas["summary_derived"] - deltas["summary"],
                "relax_gain": deltas["summary_relax"] - deltas["summary"],
            })
    return pd.DataFrame(rows)


def main():
    started = time.time()
    frame = pd.read_csv(os.path.join(ROOT, "data", "processed", "features.csv"))
    labelled, psi = domain_classes(frame, G["hazard_eol_cycles"],
                                    G["psi_safe_max"], G["psi_unsafe_min"])
    dom_class = psi.cls.to_dict()
    write_csv(psi.reset_index(), "domains.csv")

    deltas = b_line(labelled, dom_class, Q["K_nested"],
                    CFG["null_calibration"]["domain_label_permutations"], CFG["seed"])
    write_csv(deltas, "delta_menus.csv")

    menus = build_menus(labelled)
    paired_rows = []
    contrasts = {
        "g_summary_minus_summary": (menus["g_summary"], menus["summary"]),
        "summary_derived_minus_summary": (menus["summary_derived"], menus["summary"]),
        "summary_relax_minus_summary": (menus["summary_relax"], menus["summary"]),
    }
    for K in Q["K_nested"]:
        for offset, (name, (new, base)) in enumerate(contrasts.items()):
            result = paired_delta_difference(
                new, base, labelled.domain.values, dom_class, K,
                CFG["null_calibration"]["domain_label_permutations"],
                CFG["seed"] + 1000 * K + offset,
            )
            paired_rows.append({"K": K, "contrast": name, **result})
    paired = pd.DataFrame(paired_rows)
    write_csv(paired, "paired_menu_nulls.csv")

    channel_tables, channel_summaries = [], []
    X = labelled[summary_columns(labelled)].reset_index(drop=True)
    W = labelled[relax_columns(labelled)].reset_index(drop=True)
    for K in (Q["K_primary"], 8):
        table, summary = channel_pairing_permutation(
            X, W, labelled.domain.values, dom_class, K,
            CFG["negative_control"]["relax_block_permutations"],
            CFG["seed"] + 20000 + K,
        )
        channel_tables.append(table)
        channel_summaries.append(summary)
    channel_perms = pd.concat(channel_tables, ignore_index=True)
    channel_summary = pd.DataFrame(channel_summaries)
    write_csv(channel_perms, "relax_pairing_permutations.csv")
    write_csv(channel_summary, "relax_pairing_summary.csv")

    nesting = nesting_check(labelled, dom_class, 8, [4, 2])
    write_csv(nesting, "nesting_check.csv")

    pairwise_tables, leave_tables = [], []
    for K in (Q["K_primary"], 8):
        pairwise, hull = pairwise_vs_hull(labelled, dom_class, K)
        pairwise.insert(0, "K", K)
        pairwise["hull_delta"] = hull
        pairwise_tables.append(pairwise)
        leave = leave_one_domain(labelled, dom_class, K)
        leave.insert(0, "K", K)
        leave_tables.append(leave)
    pairwise_all = pd.concat(pairwise_tables, ignore_index=True)
    leave_all = pd.concat(leave_tables, ignore_index=True)
    write_csv(pairwise_all, "pairwise_vs_hull.csv")
    write_csv(leave_all, "leave_one_domain.csv")

    geometry_draws, geometry_summaries = [], []
    for K in (Q["K_primary"], 8):
        draws, null = geometry_permutation_diagnostics(
            labelled[summary_columns(labelled)], labelled.domain.values, dom_class, K,
            "NCA_T35_C0.5", 2000, CFG["seed"] + 30000 + K,
        )
        geometry_draws.append(draws)
        geometry_summaries.append(null)
    geo_draws = pd.concat(geometry_draws, ignore_index=True)
    geo_null = pd.concat(geometry_summaries, ignore_index=True)
    write_csv(geo_draws, "geometry_permutation_draws.csv")
    write_csv(geo_null, "geometry_permutation_summary.csv")

    support = pd.concat([
        support_sensitivity(labelled[summary_columns(labelled)], labelled.domain.values,
                            dom_class, K, [1, 3, 5, 8, 10])
        for K in (Q["K_primary"], 8)
    ], ignore_index=True)
    write_csv(support, "support_sensitivity.csv")
    boot, boot_summary = low_support_bootstrap(
        labelled[summary_columns(labelled)], labelled.domain.values, dom_class, 8,
        "NCA_T35_C0.5", 1000, CFG["seed"] + 40000,
    )
    write_csv(boot, "low_support_bootstrap.csv")
    write_json(boot_summary, "low_support_bootstrap_summary.json")

    thresholds = threshold_grid(frame)
    write_csv(thresholds, "threshold_sensitivity.csv")

    transfer, meta = a_line(frame, CFG)
    write_csv(transfer, "transfer_legacy.csv")
    a_validity = {
        "status": "NOT_EVALUABLE",
        "registered_claim": "class-conditional transported side-error control",
        "legacy_file": "results/transfer_legacy.csv",
        "legacy_procedure": "one random fit/cal split with one unconditional residual radius",
        "registered_procedure": "leave-one cross-fitting plus split conformal",
        "premise_failures": [
            "the released implementation did not perform leave-one cross-fitting",
            "one unconditional interval does not certify both class-conditional side errors",
            "rho is a plug-in estimate without uncertainty and two bounds are vacuous",
        ],
        "source_counts": {"unsafe": meta["source_unsafe"], "safe": meta["source_safe"]},
        "decision": "G5 is not scored in v01.1; the legacy numbers are retained for provenance only",
    }
    write_json(a_validity, "a_line_validity.json")

    registered = evaluate_registered_gates(deltas, paired, channel_summary,
                                           transfer, meta, CFG)
    corrected = evaluate_corrected_diagnostics(deltas, nesting, channel_summary,
                                                geo_null, support, CFG)
    write_json(registered, "as_registered_gates.json")
    write_json(corrected, "corrected_diagnostics.json")

    deviations = {
        "version": "v01.1",
        "frozen_files_modified": False,
        "registered_primary_K": Q["K_primary"],
        "legacy_v01_reporting_K": 8,
        "items": [
            {"id": "D01", "issue": "v01 mixed registered and post-hoc gate definitions",
             "resolution": "separate as_registered_gates.json and corrected_diagnostics.json"},
            {"id": "D02", "issue": "G4 was omitted",
             "resolution": "included explicitly as NOT_EVALUABLE"},
            {"id": "D03", "issue": "200 registered relaxation pairing permutations were absent",
             "resolution": "executed at K=4 and K=8"},
            {"id": "D04", "issue": "threshold pairs were not the frozen pairs",
             "resolution": "restored primary (100,150) and all three frozen sensitivity pairs"},
            {"id": "D05", "issue": "K=8 was silently treated as primary",
             "resolution": "K=4 is primary; K=8 is labelled resolution sensitivity"},
            {"id": "D06", "issue": "A-line implementation did not match its registered calibration",
             "resolution": "G5 marked NOT_EVALUABLE; legacy output retained"},
            {"id": "D07", "issue": "pooled rank/quantile maps are data-adaptive and menus are independently compressed",
             "resolution": "redundancy result is called a pipeline floor, not a sigma-algebra theorem test"},
            {"id": "D08", "issue": "run_all rebuilt the manifest before checking it",
             "resolution": "release manifest is immutable during reruns"},
        ],
    }
    write_json(deviations, "protocol_deviations.json")

    e = frame[frame.eol90.notna()].copy()
    y = np.log10(e.eol90)
    ssb = sum(len(group) * (np.log10(group.eol90).mean() - y.mean()) ** 2
              for _, group in e.groupby("domain"))
    ssw = sum(((np.log10(group.eol90) - np.log10(group.eol90).mean()) ** 2).sum()
              for _, group in e.groupby("domain"))
    eta_squared = float(ssb / (ssb + ssw))

    k4 = pairwise_all[pairwise_all.K == Q["K_primary"]]
    k8 = pairwise_all[pairwise_all.K == 8]
    summary = {
        "experiment": CFG["experiment"],
        "correction_version": "v01.1",
        "n_cells": int(len(frame)),
        "n_with_eol90": int(frame.eol90.notna().sum()),
        "n_labelled": int(len(labelled)),
        "aborted_cycles_removed": int(frame.n_aborted.sum()),
        "eol90_eol95_spearman": float(frame[["eol90", "eol95"]].dropna()
                                       .corr(method="spearman").iloc[0, 1]),
        "eta_squared_domain": eta_squared,
        "registered_primary_K": int(Q["K_primary"]),
        "registered_K4": {
            "min_pairwise_tv": float(k4.tv.min()),
            "hull_delta": float(k4.hull_delta.iloc[0]),
        },
        "exploratory_K8": {
            "min_pairwise_tv": float(k8.tv.min()),
            "hull_delta": float(k8.hull_delta.iloc[0]),
            "pairwise_over_hull": float(k8.tv.min() / k8.hull_delta.iloc[0]),
        },
        "registered_verdict": registered["overall"],
        "corrected_verdict": corrected["overall"],
    }
    write_json(summary, "summary.json")
    environment = {
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
        "scipy": scipy.__version__,
        "sklearn": sklearn.__version__,
        "note": "recorded for provenance; excluded from the canonical release manifest",
    }
    write_json(environment, "environment.json")
    write_json({"runtime_seconds": time.time() - started}, "runtime.json")
    print(json.dumps({"registered": registered["overall"],
                      "corrected": corrected["overall"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
