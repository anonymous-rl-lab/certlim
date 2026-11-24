"""Build the numerical abstract and NASA decision table from the released ledgers."""
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "TII_MAIN_MANUSCRIPT_v25.md"
EVIDENCE = ROOT / "evidence"
EXAMPLE_TARGET_PCT = 24.30


def read(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def pooled_nasa():
    registry = read(EVIDENCE / "decision_v22/results/procurement.csv")
    return next(row for row in registry if row["source"] == "confidence" and row["policy"] == "pooled")


def outputs():
    nasa = pooled_nasa()
    cutoff = 100 * float(nasa["cutoff_U"])
    lookup = 100 * float(nasa["full_L"])
    likelihood = 100 * float(nasa["lr_L"])
    headroom = math.ceil(float(nasa["lr_gap_U_pp"]) * 1e6) / 1e6
    safe, unsafe, ungraded = (int(nasa[k]) for k in ("safe", "unsafe", "unresolved"))
    graded = safe + unsafe
    total = graded + ungraded
    cetl = read(EVIDENCE / "CETL/results/metrics.csv")
    cetl_n = sum(int(r["n"]) for r in cetl if r["split"] == "test" and r["channel"] == "B")
    census = json.loads((EVIDENCE / "ReLiB/public_census/public_summary.json").read_text())
    qualified = census["by_grade"]["qualified"]
    leaf = json.loads((EVIDENCE / "Leaf/results/summary.json").read_text())
    charge_decisions = sum(r["same_visit"] != "REFER" for r in read(EVIDENCE / "Leaf/results/traces.csv"))
    abstract = (
        "When does a battery diagnostic need one more recorded field, and when is a simple decision rule already sufficient? "
        "We bound the worst-case fraction of attempts that can end in approval or rejection under separate limits on each error. "
        "A common confidence region determines which reference grades are resolved, provides a feasible rule for each candidate measurement, "
        "and bounds the decision rate of every rule using that measurement. "
        f"In NASA, {graded} of {total:,} stage-policy combinations were gradeable. With five independent readings per model and two 5% error budgets, "
        f"the cutoff-only upper bound was {cutoff:.3f}%. Recording the current band gave a feasible rate of {lookup:.3f}%. "
        f"A calibrated likelihood-ratio rule also met an illustrative {EXAMPLE_TARGET_PCT:.2f}% requirement and left at most {headroom:.6f} percentage points for further optimization. "
        f"In capacity screening, a charge-trace rule met both error bounds on {cetl_n:,} complete CETL holdout records under within-grade independence. "
        f"Applied unchanged to ReLiB, it rejected {qualified['wrong']:,} of {qualified['total']:,} confirmed qualified records. "
        f"In two Leaf donor packs, a secondary rule using the current visit’s charge decided {charge_decisions} of {leaf['distinct_visits']} recorded visits with zero observed errors. "
        "It met the 20% empirical target in each grade across the full schedule, where the prior-capacity rule fell short after mandatory reference visits were counted."
    )
    header = ["Evidence recorded", "Decision rule", "Bound on worst-case rate", "Rate (%)", f"At {EXAMPLE_TARGET_PCT:.2f}%"]
    rows = [
        ["Cutoff only", "Any rule", "Upper, all rules", f"{cutoff:.6f}", "Beyond reach"],
        ["Cutoff and current", "Full lookup", "Lower, feasible rule", f"{lookup:.6f}", "Meets target"],
        ["Cutoff and current", "Likelihood ratio", "Lower, feasible rule", f"{likelihood:.6f}", "Meets target"],
    ]
    caption = (
        f"**TABLE I. Is the current band needed at an illustrative {EXAMPLE_TARGET_PCT:.2f}% decision requirement? "
        f"All rows use the same {graded}/{total:,} gradeable NASA stage-policy models ({safe} safe, {unsafe} unsafe), "
        "five independent draws under each fixed model, a shared lookup across policies and two 5% error budgets. "
        f"Further rule optimization on the full channel can gain at most {headroom:.6f} percentage points over the likelihood ratio. "
        "Rates are rounded for display.**"
    )
    table = "\n".join("| " + " | ".join(row) + " |" for row in [header, ["---"]*len(header), *rows])
    return abstract, caption + "\n\n" + table


def render(text):
    abstract, table = outputs()
    text, count = re.subn(r"(?<=## Abstract\n\n).*?(?=\n\n\*\*Index Terms)", lambda _: abstract, text, flags=re.S)
    assert count == 1
    text, count = re.subn(r"^\*\*TABLE I\.[^\n]+\n\n(?:^\|[^\n]*\|\n?)+", lambda _: table + "\n", text, flags=re.M)
    assert count == 1
    return text


if __name__ == "__main__":
    DOC.write_text(render(DOC.read_text()))
