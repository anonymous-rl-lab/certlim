#!/usr/bin/env python3
"""Check every headline number in the paper against the artifact that produced it.

Each row below names a claim as it is printed in the manuscript, the released
artifact it comes from, and how to read the value out of that artifact. Nothing
here recomputes a result: the point is to catch a number in the paper drifting
away from the file it is supposed to come from, in either direction.

Exit status is 0 when every claim matches, 1 otherwise.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "experiments"
TOL = 5e-7


def _csv(rel: str) -> pd.DataFrame:
    return pd.read_csv(E / rel)


def _json(rel: str):
    return json.loads((E / rel).read_text())


def claims():
    """(section, claim as printed, value in the paper, value from the artifact)."""
    nasa = _csv("nasa_randomized_usage_gate/results/frontier.csv")
    adv = _json("nasa_randomized_usage_gate/results/L3_adversarial.json")
    alt = _csv("battery_alt_reference_channel_gate/results/frontier_v02.csv")
    pb = _csv("pulsebat_procurement_external/results/frontier.csv")
    grid = _csv("pulsebat_procurement_correction_v02/results/full/soc_menu_uncertainty.csv")
    e12 = _json("nasa_confidence_and_baselines/results/e1_e2.json")
    h2h = _csv("nasa_confidence_and_baselines/results/e3_head_to_head.csv")
    sens = _json("nasa_confidence_and_baselines/results/sensitivity.json")

    def alt_delta(k, n):
        row = alt[(alt.K == k) & (alt.n == n)]
        return float(row.iloc[0]["Delta"])

    def grid_delta(soc, menu):
        row = grid[(grid.soc == soc) & (grid.menu == menu)]
        return float(row.iloc[0]["observed_delta_one"])

    lr = h2h[(h2h.channel == "adversarial") & (h2h.n == 5)
             & (h2h.method == "likelihood ratio") & (h2h.tuned_for == "accuracy")].iloc[0]
    coh = next(r for r in e12["E1"] if r["registration"] == "cohort")
    unit = next(r for r in e12["E1"] if r["registration"] == "unit")

    yield "Table I", "Delta(1), NASA frontier", 0.1494, float(nasa.iloc[0]["delta"])
    yield "Table I", "Delta(20), NASA frontier", 0.5558, float(nasa.iloc[-1]["delta"])
    yield "Table I", "exact D(1)", 0.1121, float(nasa.iloc[0]["D"])
    yield "Table I", "exact D(20)", 0.4747, float(nasa.iloc[-1]["D"])
    yield "VI-A", "frontier points evaluated", 11, len(nasa)
    yield "(27)", "adversarial Delta", 0.0, float(adv["delta_adversarial_min"])
    yield "(27)", "adversarial decisiveness", 0.10, float(adv["D_adversarial"])
    yield "(28)", "ALT Delta_{K=2}(1) is zero", True, abs(alt_delta(2, 1)) <= 1e-9
    yield "(28)", "ALT Delta_{K=2}(2) is zero", True, abs(alt_delta(2, 2)) <= 1e-9
    yield "VI-B", "ALT Delta_{K=2}(3) positive", True, alt_delta(2, 3) > 1e-9
    yield "VI-B", "ALT (K,n) combinations", 30, len(alt)
    yield "V-B", "largest program, count states", 19448, int(alt["n_states"].max())
    yield "(29)", "chemistry-control Delta", 0.0, float(pb[pb.menu == "nameplate"].delta.max())
    yield "VI-C", "registered SOC 5%, 0.5C pulse", 0.5273, grid_delta(5, "pulse_0p5C")
    yield "(30)", "diagnostic SOC 10%, OCV", 0.6273, grid_delta(10, "ocv")
    yield "VI-C", "grid points evaluated", 40, len(grid)
    yield "S9.1", "cohort plug-in Delta(1)", 0.4918, coh["delta_plugin"]
    yield "S9.1", "cohort certificate non-vacuous", True, coh["verdict"] == "non-vacuous"
    yield "S9.1", "unit certificate vacuous", True, unit["verdict"] == "vacuous"
    yield "S9.2", "cross-grade pairs", 389664, e12["E2"]["n_pairs"]
    yield "S9.2", "minimum pairwise TV", 0.152644, e12["E2"]["min_pairwise_tv"]
    yield "VI-A", "baseline balanced accuracy", 0.943, round(float(lr.balanced_accuracy), 3)
    yield "VI-A", "worst unsafe certified", 0.747, round(float(lr.wc_unsafe_certify), 3)
    yield "S9.5", "sensitivity prediction S3 rejected", False, sens["verdicts"]["S3_slack_matches_exact_within_0.01"]
    yield "S9.5", "sensitivity S1 holds", True, sens["verdicts"]["S1_cohort_always_non_vacuous"]


def main() -> int:
    bad = 0
    print(f"{'where':<10}{'claim':<40}{'paper':>12}{'artifact':>14}  ")
    print("-" * 80)
    for where, claim, paper, got in claims():
        if isinstance(paper, bool) or isinstance(got, bool):
            ok = bool(paper) == bool(got)
        elif isinstance(paper, int) and isinstance(got, int):
            ok = paper == got
        else:
            ok = abs(float(paper) - float(got)) <= max(TOL, 5e-5 * max(1.0, abs(float(paper))))
        bad += not ok
        p = f"{paper}" if isinstance(paper, (bool, int)) else f"{paper:.6g}"
        g = f"{got}" if isinstance(got, (bool, int)) else f"{got:.6g}"
        print(f"{where:<10}{claim:<40}{p:>12}{g:>14}  {'ok' if ok else 'MISMATCH'}")
    print("-" * 80)
    print(f"{'all headline numbers match the artifacts' if not bad else f'{bad} mismatch(es)'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
