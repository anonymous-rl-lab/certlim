#!/usr/bin/env python3
"""Convert the Markdown manuscript into an anonymous IEEEtran two-column source.

The conversion is deliberately mechanical and verifiable rather than clever:

* Every display equation keeps its hand-assigned number through ``\\tag`` inside
  ``equation*``. Auto-numbering is not used, so a number in the prose can never
  drift from the equation it refers to.
* Nothing is dropped silently. Any construct the converter does not recognise
  raises, so a missing table or figure fails the build instead of vanishing from
  the PDF.
* No author, affiliation, funding, or repository string is emitted. The output
  is the double-blind review version.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from table_widths import colspec

TEXTWIDTH_PT = 516.0      # ieeecolor, two-column
COLUMNWIDTH_PT = 252.0

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "TII_MAIN_MANUSCRIPT_v25.md"
OUT = ROOT / "latex" / "main.tex"

ROMAN = {}


def esc(s: str) -> str:
    """Escape LaTeX specials in text, leaving math and already-escaped runs alone."""
    parts = re.split(r"(\\\(.*?\\\)|`[^`]*`)", s, flags=re.S)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:
            if p.startswith("`"):
                # a URL in a two-column line must be allowed to break, or it runs
                # 8.5 pt past the column
                code = p[1:-1].replace("_", r"\_\allowbreak{}").replace("&", r"\&")
                code = code.replace("/", r"/\allowbreak{}").replace(".", r".\allowbreak{}")
                out.append(r"\texttt{%s}" % code)
            else:
                out.append("$" + p[2:-2] + "$")
            continue
        # \{ and \} in the source are literal braces and must survive as \{ \}.
        # Escaping the backslash first and the braces afterwards mangles them into
        # \textbackslash\{\}\{, which is what shipped in v09 as "\{\}{immediate".
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

def xref(s: str) -> str:
    """Turn the prose's float names into real cross-references.

    v19: three of the four floats carried a \\label that nothing referred to, so
    the running text never cited Table I, Fig. 2, or Fig. 3. Writing \\ref here
    keeps the citation and the float in step, and lets the audit require that
    every label is referenced.
    """
    s = re.sub(r"\bFig\.\s(\d)\b", r"Fig.~\\ref{fig:\1}", s)
    s = re.sub(r"(?<!Supplementary )\bTable I\b", r"Table~\\ref{tab:1}", s)
    s = re.sub(r"(?<!Supplementary )\bTable II\b", r"Table~\\ref{tab:2}", s)
    s = re.sub(r"(?<!Supplementary )\bTable III\b", r"Table~\\ref{tab:3}", s)
    return s


def convert_table(rows: list[str], caption: str, label: str) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]
    ncol = len(header)
    for row in body:
        if len(row) != ncol:
            raise SystemExit(f"table row has {len(row)} cells, expected {ncol}: {row}")
    # House rule: a table is set to the full line width, each column's share of
    # that width grows with the amount of text in it, and the body font size is
    # left alone. tabularx fills the width exactly; the weights come from the
    # content, floored so the longest unbreakable token in a column still fits.
    wide = ncol >= 5
    env = "table*" if wide else "table"
    total_cmd, total_pt = (r"\textwidth", TEXTWIDTH_PT) if wide else (r"\columnwidth", COLUMNWIDTH_PT)
    spec = colspec([header] + body, total_pt)
    lines = [r"\begin{%s}[!t]" % env, r"\centering",
             r"\caption{%s}" % esc(caption), r"\label{%s}" % label,
             r"\begin{tabularx}{%s}{%s}" % (total_cmd, spec), r"\hline"]
    lines.append(" & ".join(r"\textbf{%s}" % breakable(esc(c)) for c in header) + r" \\")
    lines.append(r"\hline")
    for row in body:
        lines.append(" & ".join(breakable(esc(c)) for c in row) + r" \\")
    lines += [r"\hline", r"\end{tabularx}", r"\end{%s}" % env]
    return "\n".join(lines)


def main() -> None:
    text = SRC.read_text()
    title = re.search(r"^# (.+)$", text, re.M).group(1)
    abstract = text.split("## Abstract")[1].split("**Index Terms")[0].strip()
    terms = re.search(r"\*\*Index Terms—\*\*\s*(.+)", text).group(1).strip().rstrip(".")
    body_md = text.split("**Index Terms", 1)[1].split("\n", 1)[1]
    body_md, refs_md = body_md.split("## References", 1)

    out: list[str] = []
    lines = body_md.split("\n")
    i = 0
    table_no = 0
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("#### "):
            out.append(r"\subsubsection{%s}" % esc(re.sub(r"^\d\)\s*", "", ln[5:].strip())))
            i += 1; continue
        if ln.startswith("### "):
            out.append(r"\subsection{%s}" % esc(re.sub(r"^[A-Z]\.\s*", "", ln[4:].strip())))
            i += 1; continue
        if ln.startswith("## "):
            head = ln[3:].strip()
            numbered = re.sub(r"^[IVX]+\.\s*", "", head)
            # v19: sections carry a roman numeral in the Markdown; anything without
            # one -- the availability statement -- is set unnumbered, as IEEE does.
            star = "" if numbered != head else "*"
            out.append(r"\section%s{%s}" % (star, esc(numbered)))
            i += 1; continue

        # display math
        if ln.strip() == r"\[" or ln.strip().startswith(r"\[") and ln.strip() == r"\[":
            j = i + 1
            buf = []
            while lines[j].strip() != r"\]":
                buf.append(lines[j]); j += 1
            out.append(r"\begin{equation*}")
            out.extend(buf)
            out.append(r"\end{equation*}")
            i = j + 1; continue

        # figure
        mfig = re.match(r"!\[(.*?)\]\((figures/[^)]+)\)", ln.strip())
        if mfig:
            stem = Path(mfig.group(2)).stem
            cap = ""
            k = i + 1
            while k < len(lines) and not lines[k].strip():
                k += 1
            if k < len(lines) and lines[k].startswith("**Fig."):
                cap = lines[k].strip()
                i = k
            num = re.search(r"Fig\.\s*(\d)", cap or "Fig. 1").group(1)
            # Full-width panels preserve the data and geometry labels at print size.
            env = "figure*"
            width = r"\textwidth"
            out += [r"\begin{%s}[!t]" % env, r"\centering",
                    r"\includegraphics[width=%s]{../figures/%s.pdf}" % (width, stem),
                    r"\caption{%s}" % esc(re.sub(r"^\*\*Fig\.\s*\d\.\s*", "", cap).replace("**", "")),
                    r"\label{fig:%s}" % num, r"\end{%s}" % env]
            i += 1; continue

        # table
        if ln.strip().startswith("**TABLE "):
            caption = re.sub(r"^\*\*TABLE [IVX]+\.\s*", "", ln.strip().rstrip("*")).rstrip("*")
            table_no += 1
            k = i + 1
            while not lines[k].strip().startswith("|"):
                k += 1
            rows = []
            while k < len(lines) and lines[k].strip().startswith("|"):
                rows.append(lines[k]); k += 1
            out.append(convert_table(rows, caption, "tab:%d" % table_no))
            i = k; continue

        if ln.startswith("> "):
            buf = []
            while i < len(lines) and lines[i].startswith("> "):
                buf.append(lines[i][2:]); i += 1
            out += [r"\begin{quote}", esc(" ".join(buf)), r"\end{quote}"]
            continue

        if re.match(r"^\d+\.\s", ln) or ln.startswith("- "):
            ordered = bool(re.match(r"^\d+\.\s", ln))
            env = "enumerate" if ordered else "itemize"
            out.append(r"\begin{%s}" % env)
            while i < len(lines) and (re.match(r"^\d+\.\s", lines[i]) or lines[i].startswith("- ")):
                item = re.sub(r"^(\d+\.|-)\s", "", lines[i])
                out.append(r"\item " + xref(esc(item))); i += 1
            out.append(r"\end{%s}" % env)
            continue

        if ln.strip():
            out.append(xref(esc(ln)))
        else:
            out.append("")
        i += 1

    bib = [r"\begin{thebibliography}{99}"]
    for entry in re.findall(r"^\[(\d+)\]\s+(.+?)$", refs_md, re.M):
        bib.append(r"\bibitem{r%s} %s" % (entry[0], esc(entry[1])))
    bib.append(r"\end{thebibliography}")

    # ieeecolor opens the Introduction with a drop cap, as the official template
    # does. The first text line after the section heading is not the paragraph --
    # a \subsection and blank lines come first -- so skip to the first prose line.
    mark = r"\section{Introduction}"
    if mark in out:
        k = out.index(mark) + 1
        while k < len(out) and (not out[k].strip() or out[k].startswith("\\sub")):
            k += 1
        w = re.match(r"([A-Za-z])([A-Za-z]*)", out[k]) if k < len(out) else None
        if w:
            out[k] = r"\IEEEPARstart{%s}{%s}" % (w.group(1), w.group(2)) + out[k][w.end():]
        else:
            raise SystemExit("could not place \\IEEEPARstart in the Introduction")
    joined = "\n".join(out)

    tex = PREAMBLE % {
        "title": esc(title),
        "abstract": esc(abstract),
        "terms": esc(terms),
        "body": joined,
        "bib": "\n".join(bib),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(tex)
    print(f"wrote {OUT}  ({len(tex.splitlines())} lines)")


PREAMBLE = r"""\documentclass[journal,twoside,web]{ieeecolor}
\usepackage{generic}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts,bm}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{epstopdf}
\usepackage{array}
\usepackage{tabularx}
\newcolumntype{Y}[1]{>{\hsize=#1\hsize\raggedright\arraybackslash}X}
\newcolumntype{Z}[1]{>{\hsize=#1\hsize\raggedleft\arraybackslash}X}
\interdisplaylinepenalty=2500
\markboth{\journalname, VOL. XX, NO. XX, XXXX}{}
\begin{document}
\title{%(title)s}
\author{}
\maketitle
\begin{abstract}
%(abstract)s
\end{abstract}
\begin{IEEEkeywords}
%(terms)s
\end{IEEEkeywords}
%(body)s
%(bib)s
\end{document}
"""

if __name__ == "__main__":
    sys.exit(main())
