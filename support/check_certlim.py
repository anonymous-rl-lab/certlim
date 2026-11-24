"""Cross-check the installed certlim release with the v25 paper evidence."""
import csv
import hashlib
import json
from pathlib import Path
from importlib.metadata import version
from zipfile import ZipFile

import numpy as np
from scipy.optimize import brentq
from scipy.stats import binom
import certlim as cl


def require(value, message):
    if not value:
        raise AssertionError(message)


def rows(path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def paper(e):
    from importlib.resources import files

    data = files("certlim").joinpath("data")
    with data.joinpath("sources.csv").open() as fp:
        source_rows = list(csv.DictReader(fp))
    for row in source_rows:
        require(
            hashlib.sha256((e / row["v25_evidence_path"]).read_bytes()).hexdigest()
            == row["sha256"],
            row,
        )
    nasa = e / "NASA_chain_v2/results"
    results = e / "review_v21/results"
    registry = {}
    for src, name in [
        ("missing", "legacy_grades"),
        ("confidence", "legacy_confidence_sets"),
    ]:
        aa = rows(nasa / (name + ".csv"))
        registry[src] = [
            (
                r["policy"],
                cl.BandModel(
                    "/".join(r[k] for k in ("cell", "stage", "policy")),
                    *(r[k] for k in ("qhi", "lo0", "hi0", "lo1", "hi1")),
                ),
            )
            for r in aa
        ]
    table = rows(results / "comparison.csv")
    frozen = rows(results / "lookups.csv")
    worst = 0.0
    count = 0
    numerical_overflow = 0.0
    for row in table:
        key = ("source", "policy", "method", "n")
        matches = [r for r in frozen if all(r[k] == row[k] for k in key)]
        count += len(matches)
        n = int(row["n"])
        ss = cl.count_states(n, 4)
        coords = {
            tuple(int(r[k]) for k in ("low_no", "low_cut", "high_no", "high_cut")): (
                float(r["certify"]),
                float(r["reject"]),
            )
            for r in matches
        }
        c, r = np.array([coords[tuple(x)] for x in ss]).T
        numerical_overflow = max(
            numerical_overflow, float(np.max(c + r) - 1), float(-min(c.min(), r.min()))
        )
        c = np.maximum(c, 0)
        r = np.maximum(r, 0)
        norm = np.maximum(1, c + r)
        rule = cl.ThreeStateRule(n, 4, c / norm, r / norm, 0.05, 0.05, 0.0, ss)
        ms = [
            m
            for pol, m in registry[row["source"]]
            if row["policy"] == "pooled" or row["policy"] == pol
        ]
        res = cl.evaluate_rule(rule, ms)
        ref = [float(row[k]) for k in ("err_unsafe", "err_safe", "D_lower")]
        worst = max(
            worst,
            float(
                np.max(
                    abs(
                        np.array(ref)
                        - [
                            res.unsafe_approval_upper,
                            res.safe_rejection_upper,
                            res.decisiveness_lower,
                        ]
                    )
                )
            ),
        )
    require(
        worst < 1e-8 and count == 720 and len(table) == 24, "published lookup mismatch"
    )
    d = cl.design_measurement(cl.nasa_registry(), n=5, target=0.243)
    require(d.status == "additional_band_required", "NASA decision")
    return dict(
        source_files=len(source_rows),
        rules=len(table),
        lookup_rows=count,
        max_abs_error=worst,
        max_roundoff_in_published_lookup=numerical_overflow,
        registered=d.counts,
        event_upper=d.event.upper,
        band_lower=d.band_event.lower,
        band_upper=d.band_event.upper,
    )


def capacities(e):
    groups = {}

    def group(case, scope, grades_actions):
        tally = {}
        for grade, action, count, hours in grades_actions:
            k = (grade, action)
            old = tally.get(k, [0, 0.0])
            tally[k] = [
                old[0] + count,
                None if old[1] is None or hours is None else old[1] + hours,
            ]
        shipped = cl.audit_screen(cl.screening_example(case)[scope])
        for grade, acts in shipped["actions_by_grade"].items():
            for act, n in acts.items():
                require(tally.get((grade, act), [0])[0] == n, (case, scope, grade, act))
        dc = sum(n for (g, a), (n, h) in tally.items() if a != "REFER")
        total = sum(n for n, h in tally.values())
        require(
            (dc, total) == (shipped["decisive"], shipped["records"]), "screen totals"
        )
        hrs = [h for (_, a), (_, h) in tally.items() if a != "REFER"]
        h = sum(hrs) if all(x is not None for x in hrs) else None
        sh = shipped["reference_hours_on_decisions"]
        require(
            (h is None and sh is None) or (sh is not None and abs(h - sh) < 1e-8),
            "workload",
        )
        groups[case + "/" + scope] = dict(rows=total, decisive=dc, hours=h)

    for ch in ("A", "B"):
        group(
            "cetl",
            "complete_" + ch,
            (
                (
                    "qualified" if r["grade"] == "True" else "below",
                    ("REFER", "FAIL", "PASS")[int(r[ch])],
                    1,
                    float(r["discharge_h"]),
                )
                for r in rows(e / "CETL/results/predictions.csv")
                if r["split"] == "test"
            ),
        )
        counts = []
        for r in rows(e / "CETL/results/audit_all_heldout.csv"):
            if r["scope"] != "refer_on_charge_invalid" or r["channel"] != ch:
                continue
            g = "qualified" if r["grade"] == "P" else "below"
            n, err, nd = (int(r[k]) for k in ("n", "errors", "decisions"))
            fail = err if g == "qualified" else nd - err
            counts += [
                (g, "PASS", nd - fail, None),
                (g, "FAIL", fail, None),
                (g, "REFER", n - nd, None),
            ]
        group("cetl", "all_" + ch, counts)
    for scope in ("public_census", "public_results"):
        group(
            "relib",
            scope,
            (
                (r["grade"], r["action"], 1, None)
                for r in rows(e / "ReLiB" / scope / "cell_results.csv")
            ),
        )
    traces = rows(e / "Leaf/results/traces.csv")
    by = {(r["cell"], int(r["visit"])): r for r in traces}

    def action(v):
        return "PASS" if v > 24.375 else ("FAIL" if v < 21.125 else "REFER")

    for scope in ("prior_optional", "prior_all", "same_visit_all"):
        out = []
        for r in traces:
            i = int(r["visit"])
            if scope == "prior_optional" and i % 2:
                continue
            a = (
                action(float(r["charge_Ah"]))
                if scope == "same_visit_all"
                else (
                    action(float(by[(r["cell"], i - 1)]["reference_Ah"]))
                    if i % 2 == 0
                    else "REFER"
                )
            )
            g = "qualified" if float(r["reference_Ah"]) >= 22.75 else "below"
            out.append((g, a, 1, float(r["reference_h"])))
        group("leaf", scope, out)
    for target in (None, 0.2):
        metrics = cl.audit_screen(
            cl.screening_example("cetl")["complete_B"],
            inference="iid",
            min_decisiveness=target,
        )
        for v in metrics["grade_metrics"].values():
            n, k, d = v["records"], v["errors"], v["decisive"]
            tail = 0.05 / (4 if target is not None else 2)
            up = brentq(lambda p: binom.cdf(k, n, p) - tail, 0, 1)
            require(abs(up - v["error_upper"]) < 1e-10, "error interval")
            if target:
                lower = brentq(lambda p: binom.sf(d - 1, n, p) - tail, 0, 1)
                require(
                    abs(lower - v["decisiveness_lower"]) < 1e-10, "decision interval"
                )
    return groups


def main():
    root = Path(__file__).resolve().parents[1]
    require(version("certlim") == cl.__version__ == "0.2.1", "Install the bundled certlim 0.2.1 wheel")
    dist = root / "packages/certlim-0.2.1-py3-none-any.whl"
    installed = Path(cl.__file__).resolve().parent.parent
    with ZipFile(dist) as archive:
        for item in archive.namelist():
            if item.startswith("certlim/") and not item.endswith("/"):
                require((installed / item).read_bytes() == archive.read(item), f"Installed file differs: {item}")
    evidence = root / "paper_v25/evidence"
    results = dict(version=cl.__version__, nasa=paper(evidence), capacity=capacities(evidence))
    print(json.dumps(results, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
