from __future__ import annotations

import json
import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_version(self) -> None:
        self.assertRegex((ROOT / "VERSION").read_text().strip(), r"^\d+\.\d+\.\d+$")

    def test_synthetic_registered_passes(self) -> None:
        for stage in ("smoke", "small"):
            path = ROOT / "experiments" / "synthetic_gates" / "results" / stage / "summary.json"
            self.assertEqual(json.loads(path.read_text())["status"], "PASS")

    def test_jones_dual_verdict(self) -> None:
        base = ROOT / "experiments" / "jones_eis_external" / "results"
        self.assertEqual(json.loads((base / "cross_temperature" / "summary.json").read_text())["status"], "FAIL")
        robustness = json.loads((base / "cross_temperature" / "robustness.json").read_text())
        self.assertEqual(robustness["forecast_robustness_gate"], "PASS")

    def test_nested_geometry(self) -> None:
        path = ROOT / "experiments" / "jones_eis_external" / "results" / "nested_geometry" / "summary.json"
        summary = json.loads(path.read_text())
        self.assertEqual(summary["status"], "PASS")
        self.assertTrue(summary["checks"]["nested_eis_dominates_old"])

    def test_severson_registered_failure_pattern(self) -> None:
        base = ROOT / "experiments" / "severson_matr_external"
        summary = json.loads((base / "results" / "full" / "summary.json").read_text())
        gates = summary["gates"]
        self.assertTrue(gates["G0_integrity"])
        self.assertTrue(gates["G1_curve5_beats_scalar100"])
        self.assertFalse(gates["G2_curve5_beats_permuted"])
        self.assertTrue(gates["G3_nonvacuous_certification"])
        self.assertFalse(gates["G4_transport_calibration"])
        self.assertFalse(gates["overall_pass"])

    def test_severson_lightweight_contract(self) -> None:
        base = ROOT / "experiments" / "severson_matr_external"
        with (base / "data" / "processed" / "registered_features.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            self.assertEqual(sum(1 for _ in csv.DictReader(stream)), 124)
        with (base / "results" / "full" / "external_predictions.csv").open(
            newline="", encoding="utf-8"
        ) as stream:
            decisions = {row["decision"] for row in csv.DictReader(stream)}
        self.assertNotIn("Certify", decisions)
        self.assertEqual(list(base.rglob("*.mat")), [])

    def test_zhu_verdict_layers_are_not_merged(self) -> None:
        base = ROOT / "experiments" / "zhu_relaxation_external" / "results"
        registered = json.loads((base / "as_registered_gates.json").read_text())
        corrected = json.loads((base / "corrected_diagnostics.json").read_text())
        self.assertEqual(registered["overall"]["status"], "NOT_ESTABLISHED")
        self.assertNotIn("overall_pass", registered)
        self.assertEqual(corrected["overall"]["status"], "DIAGNOSTIC_ONLY")
        self.assertFalse(corrected["overall"]["confirmatory_external_gate"])

    def test_zhu_external_geometry_contract(self) -> None:
        base = ROOT / "experiments" / "zhu_relaxation_external" / "results"
        summary = json.loads((base / "summary.json").read_text())
        self.assertEqual(summary["registered_primary_K"], 4)
        self.assertAlmostEqual(summary["registered_K4"]["min_pairwise_tv"], 0.25)
        self.assertAlmostEqual(summary["registered_K4"]["hull_delta"], 0.0, places=12)
        audit = json.loads((base / "eol_sensitivity_audit.json").read_text())
        self.assertEqual(audit["variants"], 27)
        self.assertTrue(audit["all_primary_endpoints_reproduced"])
        self.assertEqual(audit["maximum_domain_grade_changes"], 0)

    def test_pulsebat_registered_gate_and_independent_audit(self) -> None:
        base = ROOT / "experiments" / "pulsebat_procurement_external"
        gates = json.loads((base / "results" / "gates.json").read_text())
        self.assertTrue(gates["overall_pass"])
        self.assertTrue(all(gates["gates"].values()))
        audit = json.loads((base / "results" / "INDEPENDENT_AUDIT.json").read_text())
        self.assertTrue(audit["pass"])
        self.assertLess(audit["max_delta_absolute_error"], 1e-9)
        self.assertLess(audit["max_decisiveness_absolute_error"], 1e-9)

    def test_pulsebat_frontier_landmarks(self) -> None:
        base = ROOT / "experiments" / "pulsebat_procurement_external"
        with (base / "results" / "frontier.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        by_key = {(row["menu"], int(row["n"])): row for row in rows}
        self.assertAlmostEqual(float(by_key[("nameplate", 12)]["delta"]), 0.0)
        self.assertAlmostEqual(float(by_key[("nameplate", 12)]["decisiveness"]), 0.1)
        self.assertAlmostEqual(float(by_key[("pulse_0p5C", 1)]["delta"]), 0.527272727273)
        self.assertGreater(float(by_key[("pulse_0p5C", 6)]["decisiveness"]), 0.9999)

    def test_pulsebat_correction_contract(self) -> None:
        base = ROOT / "experiments" / "pulsebat_procurement_correction_v02" / "results" / "full"
        summary = json.loads((base / "audit_summary.json").read_text())
        self.assertEqual(summary["grid_points"], 40)
        self.assertLess(summary["max_hull_pairwise_difference"], 1e-8)
        self.assertAlmostEqual(summary["registered_point_reproduction"]["delta"], 0.5272727272727273)
        self.assertAlmostEqual(summary["soc10_ocv"]["delta"], 0.6272727272727273)
        low, high = summary["paired_contrast"]["difference_ci95"]
        self.assertLess(low, 0)
        self.assertGreater(high, 0)

    def test_nasa_randomized_identified_frontier_and_attainment(self) -> None:
        base = ROOT / "experiments" / "nasa_randomized_usage_gate" / "results"
        gates = json.loads((base / "L1_L2_gates.json").read_text())
        self.assertTrue(gates["G1_bound"])
        self.assertTrue(gates["G3_monotone"])
        self.assertEqual(gates["n_star"], 1)
        self.assertLess(gates["sion_max_residual"], 1e-6)
        attained = json.loads((base / "L3_adversarial.json").read_text())
        self.assertTrue(attained["collision_achieved"])
        self.assertAlmostEqual(attained["delta_adversarial_min"], 0.0)
        self.assertAlmostEqual(attained["D_adversarial"], 0.1)

    def test_battery_alt_structural_replication_and_negative_channel(self) -> None:
        base = ROOT / "experiments" / "battery_alt_reference_channel_gate" / "results"
        feasibility = json.loads((base / "G0_feasibility.json").read_text())
        self.assertFalse(feasibility["G0"]["passed"])
        gates = json.loads((base / "gates_v02.json").read_text())
        self.assertTrue(gates["G1_bound"]["passed"])
        self.assertTrue(gates["G3_monotone"]["passed"])
        self.assertTrue(gates["G4_gate_nstar_sion"]["passed"])
        self.assertTrue(gates["G2_attained"]["passed"])
        self.assertTrue(gates["G6_data_processing"]["passed"])
        obstruction = gates["permanent_obstruction"]["per_K"]["2"]
        self.assertFalse(obstruction["exact_pairwise_collision"])
        self.assertAlmostEqual(obstruction["Delta_1"], 0.0)
        self.assertEqual(obstruction["n_star"], 3)
        null = json.loads((base / "null_calibration_v02.json").read_text())
        self.assertAlmostEqual(null["p_right_Delta_20"], 0.206)
        transport = json.loads((base / "G7_rw_holdout.json").read_text())
        self.assertFalse(transport["G7a_arm_transport"]["passed"])


if __name__ == "__main__":
    unittest.main()
