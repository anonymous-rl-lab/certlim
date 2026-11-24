#!/usr/bin/env python3
"""Convert the Supplementary Information Markdown into a single-column LaTeX PDF.

Same discipline as the main-text converter: hand-assigned equation tags are kept
through ``\\tag`` inside ``equation*`` so an SI equation number can never drift,
and any construct the converter does not recognise raises rather than silently
disappearing. No author, affiliation, or repository string is emitted.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from table_widths import colspec

TEXTWIDTH_PT = 472.3      # article, a4paper, 2.2 cm margins

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SUPPLEMENTARY_INFORMATION_v25.md"
OUT = ROOT / "latex_si" / "si.tex"


def esc(s: str) -> str:
    """Escape LaTeX specials in text, leaving math and already-escaped runs alone."""
    parts = re.split(r"(\\\(.*?\\\)|`[^`]*`)", s, flags=re.S)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            if p.startswith("`"):
                # repository paths are long and unhyphenatable; let them break
                code = p[1:-1].replace("_", r"\_\allowbreak{}").replace("&", r"\&")
                code = code.replace("/", r"/\allowbreak{}")
                out.append(r"\texttt{%s}" % code)
            else:
                out.append("$" + p[2:-2] + "$")
            continue
        # \{ and \} in the source are literal braces and must survive as \{ \}.
        p = p.replace("\\{", "\x00").replace("\\}", "\x01")
        p = p.replace("\\", r"\textbackslash{}")
        for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("_", r"\_"),
                     ("{", r"\{"), ("}", r"\}"), ("$", r"\$")]:
            p = p.replace(a, b)
        p = p.replace("\x00", r"\{").replace("\x01", r"\}")
        p = p.replace("—", "---").replace("–", "--")
        p = p.replace("“", "``").replace("”", "''").replace("’", "'").replace("‘", "`")
        p = p.replace("×", r"$\times$").replace("≥", r"$\ge$").replace("≤", r"$\le$")
        p = p.replace("Δ", r"$\Delta$").replace("°", r"$^{\circ}$")
        p = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", p)
        p = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"\\emph{\1}", p)
        out.append(p)
    return "".join(out)


def breakable(s: str) -> str:
    """Let a line break after a slash outside math, so a run such as
    ``0.5C/1C/1.5C`` does not have to fit a narrow column on one line."""
    parts = re.split(r"(\$[^$]*\$)", s)
    return "".join(p if i % 2 else p.replace("/", r"/\allowbreak{}")
                   for i, p in enumerate(parts))

def convert_table(rows: list[str], caption: str) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]
    ncol = len(header)
    for row in body:
        if len(row) != ncol:
            raise SystemExit(f"table row has {len(row)} cells, expected {ncol}: {row}")
    # House rule: full line width, column shares proportional to their content,
    # body font size untouched. xltabular is tabularx that can break across
    # pages, which the longer SI tables need.
    spec = colspec([header] + body, TEXTWIDTH_PT)
    head_rows = [r"\hline",
                 " & ".join(r"\textbf{%s}" % breakable(esc(c)) for c in header) + r" \\",
                 r"\hline"]
    lines = [r"\begin{center}",
             r"\begin{xltabular}{\textwidth}{%s}" % spec,
             r"\caption*{%s}\\" % esc(caption)]
    lines += head_rows + [r"\endfirsthead"]
    lines += head_rows + [r"\endhead", r"\hline", r"\endfoot"]
    for row in body:
        lines.append(" & ".join(breakable(esc(c)) for c in row) + r" \\")
    lines += [r"\end{xltabular}", r"\end{center}"]
    return "\n".join(lines)


def main() -> None:
    text = SRC.read_text()
    body = text.split("\n", 1)[1]                      # drop the "# Supplementary Information" line
    title_line = "## Finite-Evidence Limits for Causal Safety Certification in Battery Management Systems"
    if title_line not in body:
        raise SystemExit("the SI title line moved; the LaTeX title block would duplicate it")
    body = body.replace(title_line + "\n", "", 1)     # already set by \maketitle
    out: list[str] = []
    lines = body.split("\n")
    i = 0
    tables = 0
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("#### "):
            out.append(r"\subsubsection*{%s}" % esc(ln[5:].strip())); i += 1; continue
        if ln.startswith("### "):
            out.append(r"\subsection*{%s}" % esc(ln[4:].strip())); i += 1; continue
        if ln.startswith("## "):
            out.append(r"\section*{%s}" % esc(ln[3:].strip())); i += 1; continue

        if ln.strip() == "---":
            i += 1; continue

        if ln.strip() == r"\[":
            j = i + 1
            buf = []
            while lines[j].strip() != r"\]":
                buf.append(lines[j]); j += 1
            out += [r"\begin{equation*}"] + buf + [r"\end{equation*}"]
            i = j + 1; continue

        # a bold caption line immediately followed by a pipe table
        mcap = re.match(r"^\*\*(Table S\d+\..*)$", ln.strip())
        if mcap:
            caption = ln.strip().lstrip("*")
            caption = re.sub(r"\*\*", "", caption)
            k = i + 1
            while k < len(lines) and not lines[k].strip().startswith("|"):
                if lines[k].strip():
                    raise SystemExit(f"unexpected text between caption and table: {lines[k]!r}")
                k += 1
            rows = []
            while k < len(lines) and lines[k].strip().startswith("|"):
                rows.append(lines[k]); k += 1
            out.append(convert_table(rows, caption))
            tables += 1
            i = k; continue

        if ln.strip().startswith("|"):
            raise SystemExit(f"table without a numbered caption at line {i+1}: {ln[:60]!r}")

        if re.match(r"^\d+\.\s", ln) or ln.startswith("- "):
            ordered = bool(re.match(r"^\d+\.\s", ln))
            env = "enumerate" if ordered else "itemize"
            out.append(r"\begin{%s}" % env)
            while i < len(lines) and (re.match(r"^\d+\.\s", lines[i]) or lines[i].startswith("- ")):
                out.append(r"\item " + esc(re.sub(r"^(\d+\.|-)\s", "", lines[i]))); i += 1
            out.append(r"\end{%s}" % env)
            continue

        out.append(esc(ln) if ln.strip() else "")
        i += 1

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(PREAMBLE % {"body": "\n".join(out)})
    print(f"wrote {OUT}  ({len(OUT.read_text().splitlines())} lines, {tables} tables)")


PREAMBLE = r"""\documentclass[10pt,a4paper]{article}
\usepackage[hmargin=2.2cm,vmargin=2.1cm]{geometry}
\usepackage{amsmath,amssymb,amsfonts,bm}
\usepackage{xltabular}
\usepackage{caption}
\usepackage{array}
\newcolumntype{Y}[1]{>{\hsize=#1\hsize\raggedright\arraybackslash}X}
\newcolumntype{Z}[1]{>{\hsize=#1\hsize\raggedleft\arraybackslash}X}
\usepackage{textcomp}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{parskip}
\setcounter{secnumdepth}{0}
\interdisplaylinepenalty=2500
\emergencystretch=3em
\allowdisplaybreaks
\title{\vspace{-1.5cm}\textbf{Supplementary Information}\\[0.3em]
\large Finite-Evidence Limits for Causal Safety Certification in Battery Management Systems}
\date{}
\begin{document}
\maketitle
\thispagestyle{empty}
%(body)s
\end{document}
"""

if __name__ == "__main__":
    sys.exit(main())
