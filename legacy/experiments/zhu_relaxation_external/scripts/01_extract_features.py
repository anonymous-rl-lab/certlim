#!/usr/bin/env python3
"""Raw Zhu CSVs -> data/processed/features.csv.  Requires the downloaded archives."""
import argparse, json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from zhu_gate.labels import drop_aborted, first_sustained_crossing

ROOT = os.path.join(os.path.dirname(__file__), "..")
CFG = json.load(open(os.path.join(ROOT, "config", "registered.json")))
CHEM = {"d1": "NCA", "d2": "NCM"}          # d3 (NCM+NCA) excluded by protocol §1.1
GRID = np.arange(0, 1681, 120.0)


def parse_name(n):
    m = re.match(r"CY(\d+)-(\d+)_(\d+)-#(\d+)", n)
    return int(m.group(1)), {"025": 0.25, "05": 0.5, "1": 1.0}[m.group(2)], float(m.group(3))


def rest_after_charge(cycle):
    I, V, t = cycle["<I>/mA"].values, cycle["Ecell/V"].values, cycle["time/s"].values
    rest = np.abs(I) < 1.0
    runs, start = [], None
    for i, r in enumerate(rest):
        if r and start is None:
            start = i
        if (not r) and start is not None:
            if i - start >= 5:
                runs.append((start, i))
            start = None
    if start is not None and len(rest) - start >= 5:
        runs.append((start, len(rest)))
    for a, b in runs:
        if a > 0 and I[max(0, a - 3):a].mean() > 10:
            return t[a:b] - t[a], V[a:b]
    return None, None


def main(raw_root, out_path):
    E, inc = CFG["eol"], CFG["include"]
    rows, dropped = [], []
    for tag, chem in CHEM.items():
        folder = os.path.join(raw_root, tag)
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith(".csv"):
                continue
            name = fn[:-4]
            T, charge_c, discharge_c = parse_name(name)
            d = pd.read_csv(os.path.join(folder, fn),
                            usecols=["cycle number", "time/s", "Ecell/V", "<I>/mA",
                                     "Q discharge/mA.h", "Q charge/mA.h"])
            d.columns = [c.strip() for c in d.columns]
            cap = d.groupby("cycle number")["Q discharge/mA.h"].max()
            cap = cap[cap > 0]
            clean, n_abort = drop_aborted(cap, E["abort_window"], E["abort_factor"])
            eol90, c0 = first_sustained_crossing(clean, E["primary_frac"], E["sustain_k"])
            eol95, _ = first_sustained_crossing(clean, E["consistency_frac"], E["sustain_k"])
            rec = dict(cell_id=f"{chem}|{name}", chem=chem, T=T, charge_C=charge_c,
                       discharge_C=discharge_c, domain=f"{chem}_T{T}_C{charge_c}",
                       eol90=eol90, eol95=eol95, cap0=c0,
                       n_cycles=int(len(cap)), n_aborted=n_abort)
            ok = True
            for cy in (5, 10):
                sub = d[d["cycle number"] == cy]
                t, v = rest_after_charge(sub.reset_index(drop=True)) if len(sub) else (None, None)
                if t is None or t[-1] < inc["min_rest_seconds"]:
                    ok = False
                    break
                vg = np.interp(GRID, t, v)
                for j, val in enumerate(vg):
                    rec[f"rx{cy}_v{j}"] = float(val)
                rec[f"rx{cy}_dV"] = float(vg[-1] - vg[0])
                rec[f"rx{cy}_V0"] = float(vg[0])
            if not ok:
                dropped.append(dict(cell_id=rec["cell_id"], reason="rest window shorter than protocol minimum"))
                continue
            early = d[d["cycle number"] <= inc["evidence_max_cycle"]].groupby("cycle number")
            qd, qc = early["Q discharge/mA.h"].max(), early["Q charge/mA.h"].max()
            dur = early["time/s"].apply(lambda s: s.max() - s.min())
            rec.update(sm_qd_mean=float(qd.mean()),
                       sm_qd_slope=float(np.polyfit(qd.index, qd.values, 1)[0]),
                       sm_qd_last=float(qd.iloc[-1]), sm_qd_std=float(qd.std()),
                       sm_qc_mean=float(qc.mean()), sm_eff=float((qd / qc).mean()),
                       sm_dur_mean=float(dur.mean()),
                       sm_dur_slope=float(np.polyfit(dur.index, dur.values, 1)[0]))
            rows.append(rec)
    df = pd.DataFrame(rows)
    df.to_csv(out_path, index=False)
    pd.DataFrame(dropped).to_csv(os.path.join(os.path.dirname(out_path), "excluded_cells.csv"),
                                index=False)
    print(f"cells kept={len(df)}  excluded={len(dropped)}  "
          f"with EOL@90={int(df.eol90.notna().sum())}  aborted cycles removed={int(df.n_aborted.sum())}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True, help="directory containing d1/ and d2/ CSVs")
    p.add_argument("--out", default=os.path.join(ROOT, "data", "processed", "features.csv"))
    a = p.parse_args()
    main(a.raw, a.out)
