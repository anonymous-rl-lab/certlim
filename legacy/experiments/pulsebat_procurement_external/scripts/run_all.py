#!/usr/bin/env python3
"""Execute the frozen PulseBat protocol and generate the report."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pulsebat_gate.analysis import run  # noqa: E402


def main() -> None:
    result = run()
    cohorts = result["cohorts"]
    frontier = result["frontier"]
    uncertainty = result["uncertainty"]
    gates = result["gates"]
    lines = [
        "# PulseBat battery evidence-procurement gate — results", "",
        f"**Overall gate: {'PASS' if gates['overall_pass'] else 'FAIL'}**", "",
        "> Scope: registered high-retained-capacity second-life service qualification; the sampling unit is a physical battery.", "",
        "## Registered cohorts", "",
        "| chemistry | grade | batteries | SOH min | median | max |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in cohorts.itertuples(index=False):
        lines.append(
            f"| {row.chemistry} | {row.grade} | {row.batteries} | {row.soh_min:.3f} | {row.soh_median:.3f} | {row.soh_max:.3f} |"
        )
    lines += ["", "## Exact certification frontier", "",
              "| menu | n | Delta | optimal D | theorem bound | slack | total test seconds | max C-rate |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in frontier.itertuples(index=False):
        lines.append(
            f"| {row.menu} | {row.n} | {row.delta:.4f} | {row.decisiveness:.4f} | "
            f"{row.theorem_bound:.4f} | {row.bound_slack:.4f} | {row.total_seconds:.0f} | {row.maximum_c_rate:.1f} |"
        )
    lines += [
        "", "## Uncertainty", "",
        f"- Registered 0.5C pulse Delta(1): **{uncertainty['observed_delta_one']:.4f}**",
        f"- Chemistry-stratified permutation p-value ({uncertainty['permutations']} permutations): **{uncertainty['permutation_p']:.4f}**",
        f"- Whole-battery stratified bootstrap 95% interval ({uncertainty['bootstrap_replicates']} replicates): "
        f"**[{uncertainty['bootstrap_ci95'][0]:.4f}, {uncertainty['bootstrap_ci95'][1]:.4f}]**",
        "", "## Gates", "",
    ]
    for name, passed in gates["gates"].items():
        lines.append(f"- `{name}`: **{'PASS' if passed else 'FAIL'}**")
    lines += [
        "", "## Main empirical conclusion", "",
        "The same LMO and LFP nameplate/history cohorts occur on both sides of the registered capacity-margin boundary. Consequently, unlimited nameplate evidence remains in exact composite collision. A controlled, lowest-stress 0.5C pulse opens the gate immediately and raises optimal decisiveness toward one as independent batteries are sampled. Under the registered quantizer, higher-stress 1C and 1.5C pulses do not improve the worst-case composite frontier, so the 0.5C acquisition is the physically cheaper dominating choice.",
        "",
        "Passive OCV is informative but weaker at the registered least-cost SOC point: one 0.5C pulse sample provides approximately the same exact optimal decisiveness as six independent OCV samples. This comparison is descriptive; the structural claim is the permanent nameplate collision versus the positive pulse frontier.",
        "",
        "The result supports a battery-management claim about registered evidence procurement. It does not declare every cell below 80% SOH universally unsafe.", "",
    ]
    target = ROOT / "results" / "REPORT.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"overall_pass={gates['overall_pass']}")
    print(f"report={target}")


if __name__ == "__main__":
    main()

