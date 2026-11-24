from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd


PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts"))

from run_cross_temperature_audit import (  # noqa: E402
    calibrated_thresholds,
    paired_effects,
)


class AuditRerunTests(unittest.TestCase):
    def test_crossed_thresholds_become_alert_interval(self) -> None:
        y = np.array([0, 0, 0, 1, 1, 1])
        probability = np.array([0.01, 0.02, 0.03, 0.97, 0.98, 0.99])
        low, high, metadata = calibrated_thresholds(y, probability, 0.10, 0.10)
        self.assertTrue(metadata["crossed_before_conservative_ordering"])
        self.assertLess(low, high)
        self.assertLessEqual(np.mean(probability[y == 1] <= low), 0.10)
        self.assertLessEqual(np.mean(probability[y == 0] >= high), 0.10)

    def test_paired_effects_are_computed_within_split(self) -> None:
        rows = []
        menus = [
            "actions",
            "eis_actions",
            "eis_actions_permuted",
            "old_history",
            "old_history_eis",
            "old_history_eis_permuted",
        ]
        for split in range(2):
            for index, menu in enumerate(menus):
                rows.append(
                    {
                        "split": split,
                        "menu": menu,
                        "rmse": 1.0 + split + 0.1 * index,
                        "auc": 0.5 + 0.01 * index,
                        "balanced_decisiveness": 0.5,
                        "unsafe_certify_error": 0.1,
                        "safe_reject_error": 0.1,
                    }
                )
        effects = paired_effects(pd.DataFrame(rows))
        self.assertEqual(len(effects), 8)
        selected = effects[effects["comparison"] == "eis_actions_vs_actions"]
        self.assertTrue(np.allclose(selected["rmse_gain_absolute"], -0.1))


if __name__ == "__main__":
    unittest.main()
