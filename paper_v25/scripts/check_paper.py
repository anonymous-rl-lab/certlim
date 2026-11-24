"""Check the manuscript tables directly against the released NASA results."""
import csv
import hashlib
import re
from math import isclose
from paper_results import render
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evidence/NASA_chain_v2/results"
MAIN = (ROOT / "TII_MAIN_MANUSCRIPT_v25.md").read_text()
SI = (ROOT / "SUPPLEMENTARY_INFORMATION_v25.md").read_text()


def records(filename):
    with (RESULTS / filename).open(newline="") as source:
        return list(csv.DictReader(source))


def table(doc, caption):
    tail = doc.split(caption, 1)[1].split("\n\n", 1)[1].split("\n\n", 1)[0]
    return [[s.strip() for s in line.strip("|").split("|")]
            for line in tail.splitlines()[2:]]


def percent(row, key, digits):
    return f"{100 * float(row[key]):.{digits}f}"


def metric_rows(filename, keys, with_gain=False):
    result = []
    for row in records(filename):
        values = [row["n"], *[percent(row, k, 3) for k in keys]]
        if with_gain:
            values.append(f"{float(row['max_action_gain_pp']):.4f}")
        result.append(values)
    return result


def lookup(rows, **terms):
    matches = [r for r in rows if all(r[k] == v for k, v in terms.items())]
    assert len(matches) == 1, terms
    return matches[0]


def check_tables():
    front = metric_rows("corrected_frontier.csv",
                        ["cutoff_D", "four_D_lower", "four_D_upper"], True)
    def extra(filename):
        with (ROOT/"evidence/review_v21/results"/filename).open(newline="") as stream:
            return list(csv.DictReader(stream))
    comparison = extra("comparison.csv")
    def new(source, policy="pooled", method="lookup"):
        return lookup(comparison,source=source,policy=policy,n="5",method=method)
    def updated(rows,source):
        for row in rows:
            if row[0]=="5":
                row[2] = percent(new(source), "D_lower", 3)
                row[3] = percent(new(source), "D_upper", 3)
    updated(front,"missing")
    assert table(SI, "**Table S3.") == front
    assert render(MAIN) == MAIN, "Abstract or Table I differs from generated values"
    cs = metric_rows("confidence_frontier.csv", ["H_D_lower", "four_D_lower", "four_D_upper"])
    updated(cs,"confidence")
    assert table(SI, "**Table S9.") == cs
    labels={"Shared":"pooled","Uniform":"uniform","High":"skew_high","Low":"skew_low"}
    sources={"Missing":"missing","95%":"confidence"}
    def grade_text(r):
        return "/".join(r[k] for k in ("safe","unsafe","unresolved"))
    for src, label, counts, count, full, gain in table(SI, "**Table S14."):
        args=dict(source=sources[src],policy=labels[label])
        registry=lookup(extra("registration.csv"),**args)
        assert counts==grade_text(registry)
        if int(registry["safe"]) and int(registry["unsafe"]):
            cut=lookup(extra("cutoff.csv"),**args,n="5")
            four=new(**args)
            assert count==percent(cut,"D_lower",3) and full==percent(four,"D_lower",3)
            assert gain==f"{100*(float(four['D_lower'])-float(cut['D_lower'])):.3f}"
        else:
            assert [count,full,gain]==["—"]*3
    methods={"Full lookup":"lookup","Likelihood ratio":"LR","OOD distance":"OOD","Class-mass rank":"mass_rank"}
    for label,name,a,b,dec in table(SI, "**Table S15."):
        fit=new("confidence", labels[label], methods[name])
        assert [a,b,dec]==[percent(fit,key,d) for key,d in [("err_unsafe",2),("err_safe",2),("D_lower",3)]]
    for row, fit in zip(table(SI, "**Table S16."),extra("dependence.csv"),strict=True):
        assert row==[f"{float(fit['rho_max']):.2f}",*[percent(fit,k,d) for k,d in
                    [("err_unsafe",2),("err_safe",2),("D_lower",3)]]]
    for src,label,number,grades,dec in table(SI, "**Table S17."):
        fit=lookup(extra("cell_policy_summary.csv"),source=sources[src],policy=labels[label])
        assert number==fit["models"] and grades==grade_text(fit)
        assert dec==(" to ".join(percent(fit,k,3) for k in ["D_lower","D_upper"]) if fit["D_lower"] else "—")
    grades = records("legacy_grades.csv")
    assert Counter(r["grade"] for r in grades) == {"S": 443, "U": 528, "?": 568}
    assert len(set(r["cell"] for r in grades)) == 28
    assert len(set((r["cell"], r["stage"]) for r in grades)) == 513
    confidence = lookup(records("confidence_summary.csv"), scope="legacy")
    assert [confidence[k] for k in ("S", "U", "withheld")] == ["26", "250", "1263"]
    n5 = lookup(records("corrected_frontier.csv"), n="5")
    gain = 100 * (float(n5["four_D_upper"]) - float(n5["cutoff_D"]))
    assert .0808 < gain < .081

    primary = records("physical_summary.csv")
    secondary = records("ordered_summary.csv")
    def replay(method, fold, grade):
        rows = primary if method in {"cutoff_count", "load_and_cutoff", "mean_only_robust"} else secondary
        return lookup(rows, n="4", scope="missing_only", validation=fold, grade=grade, method=method)
    methods = ("cutoff_count", "load_and_cutoff", "plain_tiebreak", "mean_only_robust")
    for cells, method in zip(table(SI, "**Table S10."), methods, strict=True):
        safe = replay(method, "locked_14", "S")
        unsafe = replay(method, "locked_14", "U")
        assert cells[1:] == [percent(r, k, d)
                            for k, d in (("cell_equal_decisive", 2), ("cell_equal_error", 3))
                            for r in (safe, unsafe)]
    methods = ("load_and_cutoff", "ordered", "plain_tiebreak", "ordered_tiebreak")
    for cells, method in zip(table(SI, "**Table S11."), methods, strict=True):
        assert cells[1:] == [percent(replay(method, fold, "U"), k, 2)
                             for fold in ("locked_14", "LOCO_28")
                             for k in ("cell_equal_decisive", "cell_equal_error")]
    for cells, r in zip(table(SI, "**Table S12."), records("whole_cell_certificate.csv"), strict=True):
        grading = "/".join(r[k] for k in ("S", "U", "withheld"))
        digits = 4 if r["scope"] == "test14_frozen" else 2
        errors = [percent(r, k, digits) for k in ("unsafe_to_certify", "safe_to_reject")]
        feasible = max(float(r[k]) for k in ("unsafe_to_certify", "safe_to_reject")) <= .05000001
        assert cells[1:] == [grading, *errors, percent(r, "D_min", 2) if feasible else "—"]
    fixed = lookup(records("fixed60/whole_cell_certificate.csv"), scope="registered_28")
    assert [fixed[k] for k in ("S", "U", "withheld")] == ["23", "0", "5"]
    for grade, n in (("S", "8"), ("U", "2")):
        arm = lookup(records("arm_only_summary.csv"), task="whole_cell_CS", grade=grade)
        assert arm["correct"] == arm["n"] == n


def check_v22():
    def read_result(module, name):
        with (ROOT / "evidence" / module / "results" / name).open(newline="") as data:
            return list(csv.DictReader(data))

    acquire = read_result("decision_v22", "procurement.csv")
    registry = read_result("review_v21", "registration.csv")
    cuts = read_result("review_v21", "cutoff.csv")
    comparison = read_result("review_v21", "comparison.csv")
    assert len(acquire) == len(registry) == 8
    for row in acquire:
        key = {k: row[k] for k in ("source", "policy")}
        reg = lookup(registry, **key)
        assert all(row[k] == reg[k] for k in ("safe", "unsafe", "unresolved"))
        if not int(row["safe"]) or not int(row["unsafe"]):
            assert all(not row[k] for k in ("cutoff_U", "full_L", "gain_L_pp", "gain_U_pp"))
            continue
        cut = lookup(cuts, n="5", **key)
        full = lookup(comparison, method="lookup", n="5", **key)
        a, b = (float(cut[k]) for k in ("D_lower", "D_upper"))
        c, d = (float(full[k]) for k in ("D_lower", "D_upper"))
        expected = [b, c, 100 * max(0, c-b), 100 * (d-a)]
        for k, x in zip(("cutoff_U", "full_L", "gain_L_pp", "gain_U_pp"), expected):
            assert isclose(float(row[k]), x, abs_tol=1e-9)
        if row["lr_L"]:
            lr = float(lookup(comparison, method="LR", n="5", **key)["D_lower"])
            assert isclose(float(row["lr_gap_U_pp"]), 100 * (d-lr), abs_tol=1e-9)
            if row["lr_gain_fraction_L"]:
                assert lr >= b and isclose(float(row["lr_gain_fraction_L"]), (lr-b)/(d-a))
    # Check the printed choices against the underlying solvers independently
    # of the procurement summary used to generate Table I.
    pooled = dict(source="confidence", policy="pooled", n="5")
    cutoff = lookup(cuts, **pooled)
    unrestricted = lookup(comparison, method="lookup", **pooled)
    likelihood = lookup(comparison, method="LR", **pooled)
    displayed = table(MAIN, "**TABLE I.")
    choices = [
        ("Cutoff only", "Any rule", "Upper, all rules", cutoff, "D_upper", "Beyond reach"),
        ("Cutoff and current", "Full lookup", "Lower, feasible rule", unrestricted, "D_lower", "Meets target"),
        ("Cutoff and current", "Likelihood ratio", "Lower, feasible rule", likelihood, "D_lower", "Meets target"),
    ]
    for row, (field, rule, bound, fit, key, verdict) in zip(displayed, choices, strict=True):
        assert row == [field, rule, bound, percent(fit, key, 6), verdict]
        assert all(float(fit[side]) <= .05 for side in ("err_unsafe", "err_safe"))
    assert float(cutoff["D_upper"]) < .243 <= min(float(r["D_lower"]) for r in (unrestricted, likelihood))
    gap_pp = 100 * (float(unrestricted["D_upper"]) - float(likelihood["D_lower"]))
    assert .002233 < gap_pp <= .002234 and "0.002234 percentage points" in MAIN
    assert "0 safe, 137 unsafe and 376 unresolved" in MAIN
    for line, key in zip(table(SI, "**Table S18."),
                         [("confidence","pooled"),("confidence","skew_low"),("missing","skew_high")], strict=True):
        item=lookup(acquire, source=key[0], policy=key[1])
        assert line[1:] == [percent(item, "cutoff_U", 6), percent(item, "full_L", 6),
                            "/".join(item[k] for k in ("safe", "unsafe", "unresolved"))]
    t = read_result("decision_v22","transfer.csv")[0]
    test = lookup(records("whole_cell_certificate.csv"), scope="test14_frozen")
    assert all(isclose(float(t[a]),float(test[b])) for a,b in
               [("unsafe_bound","unsafe_to_certify"),("safe_bound","safe_to_reject"),("target_delta","delta_test")])
    assert isclose(float(t["margin"]),float(t["source_delta"])-float(t["rho_S"])-float(t["rho_U"]))
    assert 0 < float(t["margin"]) < float(t["target_delta"]) and float(t["safe_bound"]) < .05 < float(t["unsafe_bound"])
    deleted = read_result("decision_v22","deletion.csv")
    endpoints = sorted(deleted, key=lambda r:float(r["gain_pp"]))
    assert len({r["deleted"] for r in deleted})==28
    assert [(r["deleted"], round(float(r["gain_pp"]),3)) for r in (endpoints[0],endpoints[-1])]==[("RW26",6.800),("RW24",8.114)]
    timing = read_result("decision_v22","timing.csv")
    assert [(r["context"],int(r["cs_safe"]),int(r["cs_unsafe"]),round(float(r["gain_pp"]),3)) for r in timing] == [
        ("matched_start",0,137,7.561),("matched_previous",0,132,6.779)]
    grade = read_result("decision_v22","grade_example.csv")[0]
    assert (grade["cell"],grade["stage"]) == ("RW17","2")
    assert round(float(grade["risk_hi"]),6)==0.031511 and round(float(grade["confidence_hi"]),6)==0.188713


def check_structure():
    for doc, path in [(MAIN, "latex/main.tex"), (SI, "latex_si/si.tex")]:
        src = (ROOT / path).read_text()
        tags = re.findall(r"\\tag\{([^}]+)\}", doc)
        assert len(tags) == len(set(tags)) and tags == re.findall(r"\\tag\{([^}]+)\}", src)
    assert re.findall(r"^\*\*Table S(\d+)\.", SI, flags=re.M) == [str(i) for i in range(1, 21)]
    assert re.findall(r"^\[(\d+)\]", MAIN, flags=re.M) == [str(i) for i in range(1, 51)]
    assert len(list(RESULTS.rglob("*.csv"))) == 57
    for figure in ("fig1_workflow", "fig2_geometry", "fig3_validations"):
        for ext in ("pdf", "svg", "png"):
            assert (ROOT / "figures" / f"{figure}.{ext}").is_file()
    for folder in (ROOT / "evidence/NASA_chain_v2", ROOT):
        manifest = folder / "MANIFEST.sha256"
        if manifest.exists():
            for line in manifest.read_text().splitlines():
                checksum, path = line.split(maxsplit=1)
                assert hashlib.sha256((folder / path).read_bytes()).hexdigest() == checksum, path


if __name__ == "__main__":
    check_tables()
    check_v22()
    from check_capacity import check
    check(MAIN, SI)
    from check_leaf import check as check_leaf
    check_leaf(MAIN, SI)
    check_structure()
    print("PASS: main Tables I–III, Leaf schedules, CETL and ReLiB, NASA model extension and denominator example, Tables S19/S20, SI Tables S3/S9–S12/S14–S18, three evidence layers, acquisition/transfer/sensitivity outputs, equation tags, figures, references and available file checksums.")
