#!/usr/bin/env python3
from __future__ import annotations

import json
import csv
import importlib.util
import os
from pathlib import Path
import py_compile
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def check_python() -> None:
    files = [path for path in ROOT.rglob("*.py") if "__pycache__" not in path.parts]
    for path in files:
        py_compile.compile(str(path), doraise=True)
    print(f"PASS python_compile ({len(files)} files)")


def check_json() -> None:
    files = list(ROOT.rglob("*.json"))
    for path in files:
        json.loads(path.read_text())
    print(f"PASS json_parse ({len(files)} files)")


def check_synthetic_tests() -> None:
    project = ROOT / "experiments" / "synthetic_gates"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("synthetic unit tests failed")
    print("PASS synthetic_unit_tests")


def check_jones_tests() -> None:
    project = ROOT / "experiments" / "jones_eis_external"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("Jones parser contract tests failed")
    print("PASS jones_parser_contract_tests")


def check_jones_audit_results() -> None:
    project = ROOT / "experiments" / "jones_eis_external"
    result = subprocess.run(
        [sys.executable, "scripts/verify_audit_results.py"],
        cwd=project,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("Jones audit-result semantic verification failed")
    print("PASS jones_audit_result_semantics")


def check_severson_tests() -> None:
    project = ROOT / "experiments" / "severson_matr_external"
    test_file = project / "tests" / "test_core.py"
    sys.path.insert(0, str(project / "src"))
    try:
        spec = importlib.util.spec_from_file_location("severson_contract_tests", test_file)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load Severson/MATR contract tests")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tests = [
            value
            for name, value in vars(module).items()
            if name.startswith("test_") and callable(value)
        ]
        for test in tests:
            test()
    finally:
        sys.path.pop(0)
    if len(tests) != 4:
        raise RuntimeError(f"expected 4 Severson/MATR contract tests, ran {len(tests)}")
    print("PASS severson_matr_contract_tests")


def check_zhu_tests() -> None:
    project = ROOT / "experiments" / "zhu_relaxation_external"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project / "src")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        env=env,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("Zhu v01.1 contract tests failed")
    manifest = subprocess.run(
        [sys.executable, "scripts/verify_manifest.py"],
        cwd=project,
        check=False,
    )
    if manifest.returncode:
        raise RuntimeError("Zhu v01.1 internal manifest verification failed")
    print("PASS zhu_relaxation_contract_tests_and_manifest")


def check_pulsebat_tests() -> None:
    project = ROOT / "experiments" / "pulsebat_procurement_external"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project / "src")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        env=env,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("PulseBat contract tests failed")
    manifest = subprocess.run(
        [sys.executable, "scripts/verify_manifest.py"],
        cwd=project,
        check=False,
    )
    if manifest.returncode:
        raise RuntimeError("PulseBat internal manifest verification failed")
    print("PASS pulsebat_contract_tests_and_manifest")


def check_pulsebat_correction() -> None:
    project = ROOT / "experiments" / "pulsebat_procurement_correction_v02"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("PulseBat correction-overlay tests failed")
    manifest = subprocess.run(
        [sys.executable, "scripts/verify_manifest.py"],
        cwd=project,
        check=False,
    )
    if manifest.returncode:
        raise RuntimeError("PulseBat correction-overlay manifest failed")
    summary = json.loads((project / "results" / "full" / "audit_summary.json").read_text())
    if summary.get("grid_points") != 40:
        raise RuntimeError("PulseBat correction grid must contain 40 points")
    if summary.get("max_hull_pairwise_difference", 1.0) > 1e-8:
        raise RuntimeError("PulseBat pairwise-degeneracy audit exceeds tolerance")
    registered = summary.get("registered_point_reproduction", {})
    if abs(registered.get("delta", 0.0) - 0.5272727272727273) > 1e-12:
        raise RuntimeError("PulseBat registered point was not reproduced")
    soc10 = summary.get("soc10_ocv", {})
    if abs(soc10.get("delta", 0.0) - 0.6272727272727273) > 1e-12:
        raise RuntimeError("PulseBat SOC10 OCV landmark changed")
    contrast = summary.get("paired_contrast", {}).get("difference_ci95", [])
    if len(contrast) != 2 or not (contrast[0] < 0 < contrast[1]):
        raise RuntimeError("PulseBat paired contrast must remain inconclusive")
    print("PASS pulsebat_correction_overlay_and_manifest")


def check_nasa_randomized_tests() -> None:
    project = ROOT / "experiments" / "nasa_randomized_usage_gate"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project / "src")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        env=env,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("NASA Randomized Usage contract tests failed")
    manifest = subprocess.run(
        [sys.executable, "scripts/verify_manifest.py"],
        cwd=project,
        check=False,
    )
    if manifest.returncode:
        raise RuntimeError("NASA Randomized Usage internal manifest verification failed")
    print("PASS nasa_randomized_contract_tests_and_manifest")


def check_battery_alt_tests() -> None:
    project = ROOT / "experiments" / "battery_alt_reference_channel_gate"
    test_file = project / "tests" / "test_core.py"
    sys.path.insert(0, str(project / "src"))
    try:
        spec = importlib.util.spec_from_file_location("battery_alt_contract_tests", test_file)
        if spec is None or spec.loader is None:
            raise RuntimeError("cannot load Battery ALT contract tests")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        tests = [
            value
            for name, value in vars(module).items()
            if name.startswith("test_") and callable(value)
        ]
        for test in tests:
            test()
    finally:
        sys.path.pop(0)
    if len(tests) != 9:
        raise RuntimeError(f"expected 9 Battery ALT contract tests, ran {len(tests)}")
    manifest = subprocess.run(
        [sys.executable, "scripts/verify_manifest.py"],
        cwd=project,
        check=False,
    )
    if manifest.returncode:
        raise RuntimeError("Battery ALT internal manifest verification failed")
    print("PASS battery_alt_contract_tests_and_manifest")


def read_json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text())


def check_frozen_results() -> None:
    expected = {
        "experiments/synthetic_gates/results/smoke/summary.json": "PASS",
        "experiments/synthetic_gates/results/small/summary.json": "PASS",
        "experiments/jones_eis_external/results/smoke25/summary.json": "PASS",
        "experiments/jones_eis_external/results/smoke35_cubic/summary.json": "PASS",
        "experiments/jones_eis_external/results/small_cubic/summary.json": "FAIL",
        "experiments/jones_eis_external/results/cross_temperature/summary.json": "FAIL",
        "experiments/jones_eis_external/results/nested_geometry/summary.json": "PASS",
        "experiments/jones_eis_external/results/small_cubic_audit_rerun/summary.json": "FAIL",
        "experiments/jones_eis_external/results/cross_temperature_audit_rerun/summary.json": "FAIL",
        "experiments/jones_eis_external/results/nested_geometry_audit_rerun/summary.json": "COMPLETE",
    }
    for relative, status in expected.items():
        observed = read_json(relative).get("status")
        if observed != status:
            raise RuntimeError(f"{relative}: expected {status}, observed {observed}")
    robustness = read_json(
        "experiments/jones_eis_external/results/cross_temperature/robustness.json"
    )
    if robustness.get("forecast_robustness_gate") != "PASS":
        raise RuntimeError("Jones forecast robustness gate is not PASS")
    severson = read_json(
        "experiments/severson_matr_external/results/full/summary.json"
    )
    gates = severson.get("gates", {})
    expected_gates = {
        "G0_integrity": True,
        "G1_curve5_beats_scalar100": True,
        "G2_curve5_beats_permuted": False,
        "G3_nonvacuous_certification": True,
        "G4_transport_calibration": False,
        "overall_pass": False,
    }
    for key, expected_value in expected_gates.items():
        if gates.get(key) is not expected_value:
            raise RuntimeError(
                f"Severson gate {key}: expected {expected_value}, observed {gates.get(key)}"
            )
    feature_table = (
        ROOT / "experiments" / "severson_matr_external" /
        "data" / "processed" / "registered_features.csv"
    )
    with feature_table.open(newline="", encoding="utf-8") as stream:
        if sum(1 for _ in csv.DictReader(stream)) != 124:
            raise RuntimeError("Severson registered feature table is not 124 cells")
    predictions = (
        ROOT / "experiments" / "severson_matr_external" /
        "results" / "full" / "external_predictions.csv"
    )
    with predictions.open(newline="", encoding="utf-8") as stream:
        if any(row["decision"] == "Certify" for row in csv.DictReader(stream)):
            raise RuntimeError("Severson frozen result unexpectedly contains Certify")
    raw_mats = list(
        (ROOT / "experiments" / "severson_matr_external").rglob("*.mat")
    )
    if raw_mats:
        raise RuntimeError("MATR raw MATLAB files must not be bundled")
    zhu_base = ROOT / "experiments" / "zhu_relaxation_external"
    registered = read_json(
        "experiments/zhu_relaxation_external/results/as_registered_gates.json"
    )
    if registered.get("overall", {}).get("status") != "NOT_ESTABLISHED":
        raise RuntimeError("Zhu registered verdict must remain NOT_ESTABLISHED")
    if "overall_pass" in registered:
        raise RuntimeError("Zhu registered and corrected layers must not be merged")
    corrected = read_json(
        "experiments/zhu_relaxation_external/results/corrected_diagnostics.json"
    )
    if corrected.get("overall", {}).get("status") != "DIAGNOSTIC_ONLY":
        raise RuntimeError("Zhu corrected verdict must remain DIAGNOSTIC_ONLY")
    sensitivity = read_json(
        "experiments/zhu_relaxation_external/results/eol_sensitivity_audit.json"
    )
    if sensitivity.get("variants") != 27:
        raise RuntimeError("Zhu EOL 3x3x3 sensitivity grid is incomplete")
    if sensitivity.get("maximum_domain_grade_changes") != 0:
        raise RuntimeError("Zhu EOL sensitivity changed a frozen domain grade")
    if list(zhu_base.rglob("*.zip")):
        raise RuntimeError("Zhu raw archives must not be bundled")
    pulsebat_base = ROOT / "experiments" / "pulsebat_procurement_external"
    pulsebat_gates = read_json(
        "experiments/pulsebat_procurement_external/results/gates.json"
    )
    if pulsebat_gates.get("overall_pass") is not True:
        raise RuntimeError("PulseBat registered overall gate must remain PASS")
    if not all(pulsebat_gates.get("gates", {}).values()):
        raise RuntimeError("PulseBat registered subgates must remain PASS")
    pulsebat_audit = read_json(
        "experiments/pulsebat_procurement_external/results/INDEPENDENT_AUDIT.json"
    )
    if pulsebat_audit.get("pass") is not True:
        raise RuntimeError("PulseBat independent audit must remain PASS")
    if pulsebat_audit.get("max_delta_absolute_error", 1.0) > 1e-9:
        raise RuntimeError("PulseBat independent Delta audit exceeds tolerance")
    if pulsebat_audit.get("max_decisiveness_absolute_error", 1.0) > 1e-9:
        raise RuntimeError("PulseBat independent decisiveness audit exceeds tolerance")
    pulsebat_rows = pulsebat_base / "data" / "processed" / "observations.csv"
    with pulsebat_rows.open(newline="", encoding="utf-8") as stream:
        observations = list(csv.DictReader(stream))
    if len(observations) != 1510:
        raise RuntimeError("PulseBat processed table must contain 1510 SOC rows")
    batteries = {(row["chemistry"], row["ID"]) for row in observations}
    if len(batteries) != 151:
        raise RuntimeError("PulseBat processed table must contain 151 batteries")
    if list(pulsebat_base.rglob("*.xlsx")):
        raise RuntimeError("PulseBat source workbooks must not be bundled")
    nasa_base = ROOT / "experiments" / "nasa_randomized_usage_gate"
    nasa_gates = read_json(
        "experiments/nasa_randomized_usage_gate/results/L1_L2_gates.json"
    )
    if nasa_gates.get("G1_bound") is not True or nasa_gates.get("G3_monotone") is not True:
        raise RuntimeError("NASA Randomized registered main gates must remain PASS")
    if nasa_gates.get("n_star") != 1:
        raise RuntimeError("NASA Randomized n_star landmark changed")
    nasa_attainment = read_json(
        "experiments/nasa_randomized_usage_gate/results/L3_adversarial.json"
    )
    if nasa_attainment.get("collision_achieved") is not True:
        raise RuntimeError("NASA Randomized adversarial collision must remain achieved")
    if abs(nasa_attainment.get("delta_adversarial_min", 1.0)) > 1e-12:
        raise RuntimeError("NASA Randomized adversarial Delta landmark changed")
    if abs(nasa_attainment.get("D_adversarial", 0.0) - 0.1) > 1e-12:
        raise RuntimeError("NASA Randomized attainment landmark changed")
    alt_base = ROOT / "experiments" / "battery_alt_reference_channel_gate"
    alt_feasibility = read_json(
        "experiments/battery_alt_reference_channel_gate/results/G0_feasibility.json"
    )
    if alt_feasibility.get("G0", {}).get("passed") is not False:
        raise RuntimeError("Battery ALT G0 failure must remain recorded")
    alt_gates = read_json(
        "experiments/battery_alt_reference_channel_gate/results/gates_v02.json"
    )
    for key in ("G1_bound", "G3_monotone", "G4_gate_nstar_sion", "G2_attained", "G6_data_processing", "G9_heldout_packs"):
        if alt_gates.get(key, {}).get("passed") is not True:
            raise RuntimeError(f"Battery ALT {key} must remain PASS")
    alt_k2 = alt_gates.get("permanent_obstruction", {}).get("per_K", {}).get("2", {})
    if alt_k2.get("exact_pairwise_collision") is not False or alt_k2.get("n_star") != 3:
        raise RuntimeError("Battery ALT finite composite obstruction landmark changed")
    alt_null = read_json(
        "experiments/battery_alt_reference_channel_gate/results/null_calibration_v02.json"
    )
    if abs(alt_null.get("p_right_Delta_20", 0.0) - 0.206) > 1e-12:
        raise RuntimeError("Battery ALT negative-channel calibration changed")
    alt_transport = read_json(
        "experiments/battery_alt_reference_channel_gate/results/G7_rw_holdout.json"
    )
    if alt_transport.get("G7a_arm_transport", {}).get("passed") is not False:
        raise RuntimeError("Battery ALT/RW transport failure must remain recorded")
    for base in (nasa_base, alt_base):
        if list(base.rglob("*.zip")):
            raise RuntimeError(f"raw archives must not be bundled under {base.name}")
    print("PASS frozen_result_contract")


def main() -> int:
    check_python()
    check_json()
    check_synthetic_tests()
    check_jones_tests()
    check_jones_audit_results()
    check_severson_tests()
    check_zhu_tests()
    check_pulsebat_tests()
    check_pulsebat_correction()
    check_nasa_randomized_tests()
    check_battery_alt_tests()
    check_frozen_results()
    print("ALL REPOSITORY CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
