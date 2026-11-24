"""Typeset both v25 manuscripts; optionally regenerate the three figures."""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--figures", action="store_true", help="Render figures using the included datasets first")
    args = parser.parse_args()
    subprocess.run([sys.executable, str(ROOT / "scripts/paper_results.py")], check=True)
    if args.figures:
        subprocess.run([sys.executable, str(ROOT / "scripts/make_main_figures.py")], check=True)
    for source, directory, stem, output in [
        ("make_ieee_latex.py", "latex", "main", "TII_Manuscript_v25.pdf"),
        ("make_si_latex.py", "latex_si", "si", "TII_Supplement_v25.pdf")
    ]:
        subprocess.run([sys.executable, str(ROOT / "scripts" / source)], check=True)
        for _ in range(2):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", stem + ".tex"],
                           cwd=ROOT / directory, check=True)
        shutil.copyfile(ROOT / directory / (stem + ".pdf"), ROOT / output)


if __name__ == "__main__":
    main()
