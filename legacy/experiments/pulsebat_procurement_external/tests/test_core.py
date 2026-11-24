from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pulsebat_gate.core import convex_hull_tv, disjoint_block_laws, exact_decisiveness, multinomial_law  # noqa: E402


class CoreTests(unittest.TestCase):
    def test_multinomial_normalization(self) -> None:
        for n in [1, 3, 8]:
            self.assertAlmostEqual(float(multinomial_law(np.array([0.1, 0.2, 0.3, 0.4]), n).sum()), 1.0)

    def test_point_tv(self) -> None:
        self.assertAlmostEqual(convex_hull_tv(np.array([[0.8, 0.2]]), np.array([[0.3, 0.7]])), 0.5)

    def test_exact_nameplate_collision(self) -> None:
        pmfs = {(menu, chemistry, grade): np.array([1.0])
                for menu in ["nameplate"] for chemistry in ["LMO10", "LFP35"] for grade in ["safe", "unsafe"]}
        safe, unsafe = disjoint_block_laws(pmfs, "nameplate", 5)
        self.assertEqual(convex_hull_tv(safe, unsafe), 0.0)
        self.assertAlmostEqual(exact_decisiveness(safe, unsafe, 0.05, 0.05), 0.1)

    def test_released_gates(self) -> None:
        gates = json.loads((ROOT / "results" / "gates.json").read_text(encoding="utf-8"))
        self.assertTrue(gates["overall_pass"])


if __name__ == "__main__":
    unittest.main()

