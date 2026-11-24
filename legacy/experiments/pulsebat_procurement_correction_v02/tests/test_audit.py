from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_pulsebat.py"
SPEC = importlib.util.spec_from_file_location("audit_pulsebat", SCRIPT)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(AUDIT)


class CorrectiveAuditTests(unittest.TestCase):
    def test_specialized_two_block_solver_matches_general_lp(self) -> None:
        rng = np.random.default_rng(47)
        for _ in range(100):
            laws = []
            for _ in range(4):
                values = rng.gamma(1.0, 1.0, 4)
                laws.append(values / values.sum())
            p, q, r, s = laws
            pmfs = {
                ("x", "LMO10", "safe"): p,
                ("x", "LMO10", "unsafe"): q,
                ("x", "LFP35", "safe"): r,
                ("x", "LFP35", "unsafe"): s,
            }
            safe, unsafe = AUDIT.disjoint_block_laws(pmfs, "x", 1)
            general = AUDIT.convex_hull_tv(safe, unsafe)
            specialized = AUDIT.two_block_hull_tv(p, q, r, s)
            self.assertAlmostEqual(general, specialized, places=9)

    def test_registered_and_soc10_point_estimates(self) -> None:
        df = AUDIT.add_registered_columns(
            pd.read_csv(AUDIT.SOURCE / "data" / "processed" / "observations.csv")
        )
        eligible5, _ = AUDIT.symbols_and_thresholds(df, 5)
        eligible10, _ = AUDIT.symbols_and_thresholds(df, 10)
        pulse5, _ = AUDIT.delta_pairwise(eligible5, "pulse_0p5C")
        ocv10, _ = AUDIT.delta_pairwise(eligible10, "ocv")
        self.assertAlmostEqual(pulse5, 0.5272727272727273)
        self.assertAlmostEqual(ocv10, 0.6272727272727273)

    def test_released_columns_do_not_contain_format_or_history(self) -> None:
        columns = set(pd.read_csv(
            AUDIT.SOURCE / "data" / "processed" / "observations.csv", nrows=1
        ).columns)
        self.assertNotIn("format", columns)
        self.assertNotIn("history", columns)
        self.assertEqual(columns, {
            "chemistry", "ID", "Qn", "Q", "SOH", "SOC",
            "U1", "U3", "U7", "U11", "U15", "U19", "U21",
        })


if __name__ == "__main__":
    unittest.main()
