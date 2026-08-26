from pathlib import Path
import sys
import unittest

import numpy as np


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from jones_eis.parser import (
    FILE_RE,
    CycleFiles,
    _positive_segments,
    extract_charge,
    extract_discharge,
    extract_eis,
)


CELL = PROJECT / "data" / "raw" / "chemistry2-35C" / "PJ296"


class JonesParserContractTests(unittest.TestCase):
    def test_filename_contract(self) -> None:
        match = FILE_RE.match("PJ296_002_01_GEIS_CA1.txt")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.group("cell"), "PJ296")
        self.assertEqual(int(match.group("block")), 2)
        self.assertEqual(int(match.group("number")), 1)

    def test_cycle_index_contract(self) -> None:
        item = CycleFiles(
            cell="PJ296",
            channel="CA1",
            block=3,
            step=2,
            eis=Path("eis.txt"),
            charge=Path("charge.txt"),
            discharge=Path("discharge.txt"),
        )
        self.assertEqual(item.cycle_index, 7)

    def test_two_stage_action_segmentation(self) -> None:
        current = np.array([0, 0, 80, 80, 80, 80, 80, 0, 0, 120, 120, 120, 120, 120, 0])
        segments = _positive_segments(current)
        self.assertEqual(len(segments), 2)
        self.assertTrue(np.array_equal(segments[0], np.arange(2, 7)))
        self.assertTrue(np.array_equal(segments[1], np.arange(9, 14)))

    @unittest.skipUnless(CELL.exists(), "Jones raw data are intentionally not bundled")
    def test_single_protocol_triplet(self) -> None:
        grid = np.linspace(-1.66, 3.9, 100)
        eis = extract_eis(CELL / "PJ296_002_01_GEIS_CA1.txt", grid)
        charge = extract_charge(CELL / "PJ296_002_02_GCPL_CA1.txt")
        discharge = extract_discharge(CELL / "PJ296_002_04_GCPL_CA1.txt")
        self.assertLessEqual(eis["eis_end_s"], charge["charge_start_s"])
        self.assertLessEqual(charge["charge_end_s"], discharge["discharge_start_s"])
        self.assertLess(50, charge["charge_stage1_ma"])
        self.assertLess(charge["charge_stage1_ma"], 200)
        self.assertLess(30, discharge["discharge_capacity_mah"])
        self.assertLess(discharge["discharge_capacity_mah"], 50)


if __name__ == "__main__":
    unittest.main()
