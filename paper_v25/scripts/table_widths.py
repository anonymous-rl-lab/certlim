# -*- coding: utf-8 -*-
"""Shared column-width rule for both LaTeX converters.

One rule, applied to every table in the main text and the SI:

* the table is set to the full line width;
* each column's share of that width grows with the amount of text in it;
* no size command is emitted, so the table is typeset in the body font.

Column shares are proportional to the printed length of the widest cell, then
floored so that the longest unbreakable token in a column still fits on one
line -- the floor is what keeps a text-heavy neighbour from squeezing a column
until LaTeX reports an overfull box.
"""
import re

TEXT_PT = 5.45       # mean advance width of one character at 10 pt
MONO_PT = 5.7        # typewriter is wider and never hyphenates
BOLD = 1.12          # header rows are bold
TABCOLSEP_PT = 6.0   # LaTeX default, applied twice per column


def _runs(cell: str):
    """(text, is_monospace) runs, with markup and math reduced to what prints."""
    out = []
    for part in re.split(r"(`[^`]*`)", cell):
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            out.append((part[1:-1], True))
            continue
        # A control sequence in math prints as a symbol, not as nothing: charge it
        # two characters so \(\to\) and \(\Delta\) are not measured as free.
        s = re.sub(r"\\\((.*?)\\\)",
                   lambda m: re.sub(r"\\[a-zA-Z]+", "xx", re.sub(r"[{}^_$]", "", m.group(1))),
                   part)
        out.append((s.replace("**", ""), False))
    return out


def _plain(cell: str) -> str:
    return "".join(s for s, _ in _runs(cell))


def _widest_token_pt(cell: str, bold: bool) -> float:
    """Width of the widest run of characters LaTeX cannot break apart.

    Spaces break, and the converters insert a break opportunity after a hyphen
    and after a slash, so only an unbroken run of letters and digits counts.
    """
    pieces, cur = [], []
    for s, mono in _runs(cell):
        for ch in s:
            if ch.isspace():
                pieces.append(cur); cur = []
            else:
                cur.append(MONO_PT if mono else TEXT_PT)
                if ch in "-/":
                    pieces.append(cur); cur = []
    pieces.append(cur)
    factor = BOLD if bold else 1.0
    return max((sum(p) for p in pieces), default=0.0) * factor


def is_numeric(column) -> bool:
    body = [c for c in column[1:] if c.strip()]
    if not body:
        return False
    return all(re.fullmatch(r"[-+]?[0-9][0-9.,]*\*?", _plain(c).strip()) for c in body)


def hsize_weights(cells, total_pt: float):
    """Weights summing to ncol, as tabularx requires of modified \\hsize columns."""
    ncol = len(cells[0])
    columns = [[row[j] for row in cells] for j in range(ncol)]
    desired = [max(max(len(_plain(c)) for c in col), 3) for col in columns]
    floor_pt = [max(_widest_token_pt(c, bold=(i == 0)) for i, c in enumerate(col))
                for col in columns]

    avail = total_pt - 2 * TABCOLSEP_PT * ncol
    # No single column may take more than 30 % of the line; if even the floors
    # cannot all be honoured, they are scaled down together rather than letting
    # one column starve the rest.
    floor_frac = [min(0.30, f / avail) for f in floor_pt]
    if sum(floor_frac) > 0.95:
        scale = 0.95 / sum(floor_frac)
        floor_frac = [f * scale for f in floor_frac]

    frac = [d / sum(desired) for d in desired]
    for _ in range(128):
        short = [j for j in range(ncol) if frac[j] < floor_frac[j] - 1e-9]
        if not short:
            break
        deficit = sum(floor_frac[j] - frac[j] for j in short)
        donors = [j for j in range(ncol) if j not in short]
        pool = sum(max(0.0, frac[j] - floor_frac[j]) for j in donors)
        if pool <= 1e-9:
            break
        for j in short:
            frac[j] = floor_frac[j]
        for j in donors:
            frac[j] -= deficit * max(0.0, frac[j] - floor_frac[j]) / pool

    w = [round(ncol * f, 4) for f in frac]
    k = w.index(max(w))
    w[k] = round(w[k] + (ncol - sum(w)), 4)
    return w


def colspec(cells, total_pt: float) -> str:
    w = hsize_weights(cells, total_pt)
    columns = [[row[j] for row in cells] for j in range(len(cells[0]))]
    return "".join(("Z{%s}" if is_numeric(col) else "Y{%s}") % f"{wj:g}"
                   for col, wj in zip(columns, w))
