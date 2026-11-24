#!/usr/bin/env python3
"""Generate the three publication figures from the included experimental outputs.

The script performs no model fitting and no resampling. It reads only released
CSV/JSON results and writes vector PDF/SVG plus 600-dpi PNG previews.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
EVIDENCE = ROOT / "evidence"
BLUE = "#2F5D8C"
LIGHT_BLUE = "#DCEAF5"
RED = "#A64B47"
LIGHT_RED = "#F3DEDC"
AMBER = "#B77A1F"
GREEN = "#39735A"
INK = "#202124"
MID = "#6B7075"
GRID = "#D9DDE1"


def configure() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.0,
            "axes.labelsize": 8.0,
            "axes.titlesize": 8.5,
            "xtick.labelsize": 7.0,
            "ytick.labelsize": 7.0,
            "legend.fontsize": 7.0,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.hashsalt": "tii-paper-v03",
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.03,
        }
    )


def save_all(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUT / f"{stem}.pdf",
        metadata={"Creator": "make_main_figures.py", "CreationDate": None, "ModDate": None},
    )
    fig.savefig(OUT / f"{stem}.svg", metadata={"Creator": "make_main_figures.py", "Date": None})
    fig.savefig(OUT / f"{stem}.png", dpi=600, metadata={"Software": "make_main_figures.py"})
    plt.close(fig)


def arrow(ax, start, end, color=MID, style="-|>", lw=1.4):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle=style,
            mutation_scale=9,
            linewidth=lw,
            color=color,
            shrinkA=2,
            shrinkB=2,
        )
    )


def make_figure1() -> None:
    """Show what each certificate changes for a measurement or a reference test."""
    from paper_results import EXAMPLE_TARGET_PCT, pooled_nasa
    import json
    from decimal import Decimal, ROUND_CEILING

    nasa = pooled_nasa()
    cutoff = 100 * float(nasa["cutoff_U"])
    lookup = 100 * float(nasa["full_L"])
    remaining = Decimal(nasa["lr_gap_U_pp"]).quantize(Decimal("0.000001"), rounding=ROUND_CEILING)
    census = json.loads((EVIDENCE / "ReLiB/public_census/public_summary.json").read_text())
    qualified = census["by_grade"]["qualified"]
    wrong = 100 * qualified["wrong"] / qualified["total"]
    fig = plt.figure(figsize=(7.12, 2.34))
    ax = fig.add_axes([0, 0, 1, 1], xlim=(0, 7.12), ylim=(0, 2.34))
    ax.axis("off")

    # Left branch compares rules on one registered task. The right branch checks
    # a specific frozen rule against the grades of a different reference archive.
    deep_blue, deep_red = "#214F70", "#853F34"
    ax.text(.04, 2.24, "NASA   /   FIELD AND RULE SELECTION", color=deep_blue, size=8.3, weight="bold", va="center")
    ax.text(4.82, 2.24, "ReLiB   /   EXTERNAL RULE CHECK", color=deep_red, size=8.3, weight="bold", va="center")
    ax.plot([.04, 4.57], [2.10, 2.10], lw=1.25, color=deep_blue)
    ax.plot([4.82, 7.06], [2.10, 2.10], lw=1.25, color=deep_red)
    ax.text(.04, 1.96, "Grade models using one confidence region.", color=INK, size=9, weight="bold", va="top")
    ax.text(.04, 1.67, "Propagate that region to each channel. Bound its best rule\nand certify the rate of a rule that can be issued.",
            color=INK, size=8.4, va="top", linespacing=1.26)
    ax.text(4.82, 1.96, "Apply the frozen CETL rule.", color=INK, size=9, weight="bold", va="top")
    ax.text(4.82, 1.67, "Check its actions against\nrecorded reference grades.",
            color=INK, size=8.4, va="top", linespacing=1.26)

    ax.plot([1.13, 3.47], [1.18, 1.18], color=deep_blue, lw=.85)
    ax.plot([2.3, 2.3], [1.34, 1.18], color=deep_blue, lw=.85)
    for x, color, top in [(1.13, deep_blue, 1.18), (3.47, deep_blue, 1.18), (5.95, deep_red, 1.33)]:
        ax.annotate("", xy=(x, 1.00), xytext=(x, top),
                    arrowprops={"arrowstyle": "-|>", "color": color, "lw": .8, "mutation_scale": 7,
                                "shrinkA": 0, "shrinkB": 0})
    cards = [
        (.04, 2.19, "Keep the current band", f"Cutoff ceiling: {cutoff:.3f}%\nWith current: {lookup:.3f}%\nExample target: {EXAMPLE_TARGET_PCT:.2f}%", deep_blue, "#EEF4F8"),
        (2.38, 2.19, "Use the simpler rule", f"The likelihood ratio meets\nthe target. At most {remaining}\npercentage points remain.", deep_blue, "#EEF4F8"),
        (4.82, 2.24, "Retain the reference test", f"{wrong:.2f}% of confirmed qualified\nrecords were rejected. The\nfalse-reject budget is 5%.", deep_red, "#F8F1EE"),
    ]
    for x, width, title, body, color, fill in cards:
        ax.add_patch(mpl.patches.Rectangle((x, .04), width, .94, facecolor=fill, edgecolor="none"))
        ax.plot([x, x + width], [.98, .98], color=color, lw=1.2)
        ax.text(x+.11, .83, title, size=9.1, weight="bold", color=color, va="top")
        ax.text(x+.11, .59, body, size=8.2, color=INK, va="top", linespacing=1.26)
    save_all(fig, "fig1_workflow")


def clean_axis(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, color=GRID, linewidth=0.55, alpha=0.75)
    ax.set_axisbelow(True)


def make_figure2() -> None:
    """The one distinction the paper turns on, in two panels.

    Reduced from four panels to two. The dropped panels showed the exact-value
    branch, which panel (b) already carries, and the separation-versus-
    procurement contrast, which Section V-C states and Fig. 3 instantiates.
    Both panels are schematics; this figure reads no released artifact.
    """
    fig = plt.figure(figsize=(7.16, 2.28))
    gs = fig.add_gridspec(1, 2, wspace=0.14, left=0.015, right=0.985,
                          top=0.83, bottom=0.10)

    def hull(ax, xy, w, h, safe):
        ax.add_patch(Ellipse(xy, w, h,
                             facecolor=LIGHT_BLUE if safe else LIGHT_RED,
                             edgecolor=BLUE if safe else RED, lw=1.1,
                             alpha=1.0 if safe else 0.86, zorder=1))

    def models(ax, pts, safe):
        ax.scatter([p[0] for p in pts], [p[1] for p in pts],
                   marker="o" if safe else "^", s=13,
                   color=BLUE if safe else RED, zorder=3)

    # (a) Delayed separation: hulls meet at one unit, part at n_star.
    ax = fig.add_subplot(gs[0, 0])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.0, 1.10, "a", transform=ax.transAxes, weight="bold", fontsize=9.5)
    ax.text(0.055, 1.10, "Delayed separation", transform=ax.transAxes, fontsize=8.5)

    hull(ax, (0.155, 0.545), 0.27, 0.40, True)
    hull(ax, (0.275, 0.500), 0.27, 0.40, False)
    models(ax, [(0.078, 0.62), (0.112, 0.44)], True)
    models(ax, [(0.352, 0.56), (0.288, 0.40)], False)
    ax.text(0.215, 0.855, r"$n=1$", ha="center", fontsize=8)
    ax.text(0.215, 0.135, r"$\Delta=0$", ha="center", color=MID, fontsize=8)

    arrow(ax, (0.445, 0.52), (0.565, 0.52), color=INK, lw=1.1)
    ax.text(0.505, 0.615, r"$\times\,n$", ha="center", fontsize=7.5, color=INK)

    hull(ax, (0.775, 0.700), 0.25, 0.26, True)
    hull(ax, (0.815, 0.360), 0.25, 0.26, False)
    models(ax, [(0.715, 0.72), (0.815, 0.68)], True)
    models(ax, [(0.760, 0.375), (0.865, 0.345)], False)
    ax.plot([0.625, 0.965], [0.530, 0.530], color=GREEN, lw=1.0, ls=(0, (3, 2)))
    ax.text(0.795, 0.855, r"$n=n_\star$", ha="center", fontsize=8)
    ax.text(0.795, 0.135, r"$\Delta>0$", ha="center", color=GREEN, fontsize=8)

    ax.text(0.5, -0.045, "hulls meet, but no safe-unsafe pair coincides: repetition opens the gate",
            ha="center", transform=ax.transAxes, fontsize=7.2, color=MID)

    # (b) Permanent obstruction: one pair is exactly equal.
    ax = fig.add_subplot(gs[0, 1])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(0.0, 1.10, "b", transform=ax.transAxes, weight="bold", fontsize=9.5)
    ax.text(0.055, 1.10, "Permanent obstruction", transform=ax.transAxes, fontsize=8.5)

    hull(ax, (0.360, 0.545), 0.30, 0.42, True)
    hull(ax, (0.560, 0.545), 0.30, 0.42, False)
    models(ax, [(0.255, 0.61), (0.320, 0.44)], True)
    models(ax, [(0.665, 0.60), (0.600, 0.43)], False)

    ax.scatter([0.460], [0.545], marker="o", s=22, color=BLUE, zorder=4)
    ax.scatter([0.460], [0.545], marker="^", s=16, color=RED, zorder=5)
    ax.add_patch(Ellipse((0.460, 0.545), 0.055, 0.115, fill=False, edgecolor=INK, lw=0.9, zorder=6))
    ax.annotate(r"$P_{\theta_\mathrm{S}}^{\mathsf{E}}=P_{\theta_\mathrm{U}}^{\mathsf{E}}$",
                (0.460, 0.612), (0.460, 0.865), ha="center", fontsize=8,
                arrowprops=dict(arrowstyle="-", lw=0.8, color=INK))
    ax.text(0.460, 0.135, r"$\Delta(n)=0$ for every $n$", ha="center", color=MID, fontsize=8)

    ax.text(0.5, -0.045,
            r"one identical pair fixes decisiveness at $\min(1,\alpha+\beta)$ for every $n$",
            ha="center", transform=ax.transAxes, fontsize=7.2, color=MID)

    save_all(fig, "fig2_geometry")


def make_figure3() -> None:
    fig = plt.figure(figsize=(7.16, 3.35))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.03, 1.0, 1.28], wspace=0.38)

    # A: NASA randomized usage.
    ax = fig.add_subplot(gs[0, 0])
    stats = pd.read_csv(EVIDENCE / "decision_v22/results/procurement.csv").set_index(["source","policy"])
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.axis("off")
    ax.text(-.06,1.04,"A",transform=ax.transAxes,weight="bold",fontsize=10)
    ax.set_title("Value of logging current",loc="left",pad=2)
    ax.text(0,.92,"Five readings · gain (pp)",fontsize=7.3,color=MID)
    ax.text(0,.80,"Policy",fontsize=7.1,weight="bold")
    ax.text(.55,.80,"Fixed",fontsize=7.1,weight="bold",ha="right")
    ax.text(.99,.80,"95% CS",fontsize=7.1,weight="bold",ha="right")
    ax.axhline(.765,color=MID,lw=.7)
    for pos,(key,label) in enumerate([("pooled","Shared"),("uniform","Uniform"),("skew_high","High"),("skew_low","Low")]):
        y=.68-.145*pos
        ax.text(0,y,label,fontsize=7.4)
        for source,x,color in [("missing",.55,INK),("confidence",.99,BLUE)]:
            row=stats.loc[source,key]
            text=f"{row.gain_L_pp:.3f}" if row.safe and row.unsafe else "0 safe"
            ax.text(x,y,text,fontsize=7.6,ha="right",color=color if row.safe and row.unsafe else MID)
        ax.axhline(y-.044,color=GRID,lw=.45)
    ax.text(0,.11,"0 safe: bilateral gain",fontsize=7,color=MID)
    ax.text(0,.05,"cannot be estimated",fontsize=7,color=MID)

    # B: ALT finite gate closure.
    ax = fig.add_subplot(gs[0, 1])
    alt = pd.read_csv(EVIDENCE / "figure_data/frontier_v02.csv")
    for k, color, marker in [(2, BLUE, "o"), (4, GREEN, "s"), (8, AMBER, "^")]:
        d = alt[alt["K"] == k]
        ax.plot(d["n"], d["Delta"], color=color, marker=marker, ms=2.8, label=f"K={k}")
    for nstar, color in [(3, BLUE), (2, GREEN), (1, AMBER)]:
        ax.scatter([nstar], [0], marker="|", s=90, color=color, linewidths=1.7, zorder=5)
    ax.set_xlabel("Independent evidence units n")
    ax.set_ylabel(r"Hull distance $\Delta(n)$")
    ax.set_ylim(-0.01, 0.49)
    ax.set_xlim(0.5, 20.5)
    ax.text(-0.18, 1.04, "B", transform=ax.transAxes, weight="bold", fontsize=10)
    ax.set_title("Finite-order gate closure", loc="left", pad=2)
    clean_axis(ax)
    ax.legend(frameon=False, loc="upper left", handlelength=1.8)

    # The K=2 closure is the nontrivial branch but is invisible at panel scale,
    # so it is redrawn in its own units. No new quantity is introduced: the inset
    # plots the same frontier_v02 column multiplied by 1e3.
    inset = ax.inset_axes([0.435, 0.115, 0.545, 0.425])
    two = alt[alt["K"] == 2].sort_values("n")
    inset.plot(two["n"], two["Delta"] * 1e3, color=BLUE, marker="o", ms=1.9, lw=0.85)
    inset.scatter([1, 2], [0.0, 0.0], color=BLUE, s=8, zorder=4)
    inset.axvline(3, color=MID, lw=0.7, ls=":")
    inset.set_xlim(0.5, 20.5)
    inset.set_ylim(-0.09, 1.5)
    inset.set_xticks([1, 3, 10, 20])
    inset.set_yticks([0.0, 0.5, 1.0])
    inset.tick_params(labelsize=5.2, length=2.0, pad=1.1)
    inset.set_title(r"$K{=}2$ alone, $\Delta\times10^{3}$", fontsize=5.8, pad=1.4, loc="left")
    inset.text(3.9, 0.72, r"$n_\star=3$", color=BLUE, fontsize=5.9)
    inset.grid(True, color=GRID, linewidth=0.4, alpha=0.8)
    inset.set_axisbelow(True)
    for side in ("top", "right"):
        inset.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        inset.spines[side].set_color(MID)
        inset.spines[side].set_linewidth(0.6)
    inset.set_facecolor("white")

    # C: PulseBat SOC x menu grid.
    ax = fig.add_subplot(gs[0, 2])
    pulse = pd.read_csv(EVIDENCE / "figure_data/soc_menu_uncertainty.csv")
    menu_order = ["ocv", "pulse_0p5C", "pulse_1C", "pulse_1p5C"]
    menu_labels = ["OCV", "0.5C", "1C", "1.5C"]
    socs = sorted(pulse["soc"].unique())
    grid = pulse.pivot(index="soc", columns="menu", values="observed_delta_one").loc[socs, menu_order].to_numpy()
    pgrid = pulse.pivot(index="soc", columns="menu", values="permutation_p").loc[socs, menu_order].to_numpy()
    im = ax.imshow(grid, cmap="viridis", vmin=0, vmax=0.70, aspect="auto", origin="upper")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            val = grid[i, j]
            star = "*" if pgrid[i, j] <= 0.05 else ""
            color = "white" if val < 0.32 else INK
            ax.text(j, i, f"{val:.2f}{star}", ha="center", va="center", fontsize=5.7, color=color, weight="bold" if star else "normal")
    ax.add_patch(plt.Rectangle((0.5, -0.5), 1, 1, fill=False, edgecolor="white", lw=1.7))
    ax.add_patch(plt.Rectangle((-0.5, 0.5), 1, 1, fill=False, edgecolor="white", lw=1.7))
    ax.set_xticks(range(4), menu_labels)
    ax.set_yticks(range(len(socs)), [str(x) for x in socs])
    ax.set_xlabel("Evidence menu")
    ax.set_ylabel("SOC (%)")
    ax.text(-0.16, 1.04, "C", transform=ax.transAxes, weight="bold", fontsize=10)
    ax.set_title("Operating point", loc="left", pad=2)
    cbar = fig.colorbar(im, ax=ax, fraction=0.047, pad=0.03)
    cbar.set_label(r"$\Delta(1)$", rotation=90, labelpad=3)
    save_all(fig, "fig3_validations")


def main() -> None:
    configure()
    make_figure1()
    make_figure2()
    make_figure3()


if __name__ == "__main__":
    main()
