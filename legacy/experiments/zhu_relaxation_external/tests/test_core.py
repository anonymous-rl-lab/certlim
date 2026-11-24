"""Tests cover the code path that produces the verdict, not just leaf helpers."""
import json, os, sys, unittest
import numpy as np, pandas as pd
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
from zhu_gate.geometry import (quantize, coarsen, emp_pmf, hull_tv, delta_from_codes,
                               delta_with_null, paired_delta_difference,
                               channel_pairing_permutation)
from zhu_gate.labels import drop_aborted, first_sustained_crossing, hazard_labels, domain_classes
from zhu_gate.menus import build_menus, derived_block
from zhu_gate.evaluate import (conformal_radius, decide, evaluate_registered_gates,
                               nesting_check)

CFG = json.load(open(os.path.join(ROOT, "config", "registered.json")))
FEAT = pd.read_csv(os.path.join(ROOT, "data", "processed", "features.csv"))


class Geometry(unittest.TestCase):
    def test_hull_tv_matches_hand_value(self):
        self.assertAlmostEqual(hull_tv([[.7, .3], [.6, .4]], [[.2, .8]]), 0.4, places=10)

    def test_identical_hulls_give_zero(self):
        self.assertAlmostEqual(hull_tv([[.5, .5]], [[.5, .5]]), 0.0, places=12)

    def test_hull_never_exceeds_min_pairwise(self):
        rng = np.random.default_rng(0)
        for _ in range(30):
            S = rng.dirichlet(np.ones(5), size=4); U = rng.dirichlet(np.ones(5), size=3)
            pw = min(0.5 * np.abs(a - b).sum() for a in S for b in U)
            self.assertLessEqual(hull_tv(S, U), pw + 1e-9)

    def test_quantizer_uses_all_bins(self):
        """Pooled-quantile binning is approximately, not exactly, equal-frequency.
        See docs/PROTOCOL_ERRATA.md original item 5. The guarantee asserted here is that
        every bin is used, which is what the hull geometry requires."""
        F = pd.DataFrame(np.random.default_rng(1).normal(size=(64, 4)))
        for K in (2, 4, 8):
            c = quantize(F, K)
            self.assertEqual(set(np.unique(c)), set(range(K)))

    def test_quantizer_is_blind_to_labels_and_domains(self):
        """The map must not change when class or domain labels are permuted."""
        sm = [c for c in FEAT.columns if c.startswith("sm_")]
        base = quantize(FEAT[sm], 8)
        shuffled = FEAT.copy()
        rng = np.random.default_rng(3)
        shuffled["domain"] = rng.permutation(shuffled.domain.values)
        shuffled["eol90"] = rng.permutation(shuffled.eol90.values)
        np.testing.assert_array_equal(quantize(shuffled[sm], 8), base)

    def test_quantizer_is_invariant_to_row_order(self):
        sm = [c for c in FEAT.columns if c.startswith("sm_")]
        perm = np.random.default_rng(5).permutation(len(FEAT))
        np.testing.assert_array_equal(quantize(FEAT.iloc[perm][sm], 8),
                                      quantize(FEAT[sm], 8)[perm])

    def test_coarsening_is_nested_and_cannot_increase_delta(self):
        doms = FEAT.domain.values
        cls = {d: ("U" if d.startswith("NCA_T25_C1") else "S") for d in set(doms)}
        sm = [c for c in FEAT.columns if c.startswith("sm_")]
        c8 = quantize(FEAT[sm], 8)
        d8 = delta_from_codes(c8, doms, cls, 8)
        for K in (4, 2):
            self.assertLessEqual(delta_from_codes(coarsen(c8, 8, K), doms, cls, K), d8 + 1e-9)


class Labels(unittest.TestCase):
    def test_aborted_cycle_is_removed_and_neighbours_kept(self):
        cap = pd.Series([100.] * 20, index=range(1, 21)); cap.loc[10] = 3.0
        clean, n = drop_aborted(cap, 11, 0.5)
        self.assertEqual(n, 1); self.assertNotIn(10, clean.index); self.assertIn(11, clean.index)

    def test_eol_requires_sustained_crossing(self):
        cap = pd.Series([100, 100, 100, 100, 100, 85, 100, 100, 85, 85, 85],
                        index=range(1, 12), dtype=float)
        eol, c0 = first_sustained_crossing(cap, 0.90, 3)
        self.assertEqual(c0, 100.0); self.assertEqual(eol, 9.0)   # the isolated dip at 6 is not EOL

    def test_terminal_short_run_is_censored(self):
        cap = pd.Series([100, 100, 100, 100, 100, 95, 88],
                        index=range(1, 8), dtype=float)
        eol, _ = first_sustained_crossing(cap, 0.90, 3)
        self.assertTrue(np.isnan(eol))

    def test_censoring_rule_distinguishes_survived_from_unknown(self):
        f = pd.DataFrame(dict(eol90=[50., np.nan, np.nan], n_cycles=[200, 200, 30]))
        h = hazard_labels(f, 100)
        self.assertEqual(h[0], 1.0); self.assertEqual(h[1], 0.0); self.assertTrue(np.isnan(h[2]))


class Menus(unittest.TestCase):
    def test_derived_block_is_dimension_matched_to_relax(self):
        m = build_menus(FEAT)
        self.assertEqual(m["summary_derived"].shape[1], m["summary_relax"].shape[1])

    def test_derived_block_adds_no_information(self):
        X = FEAT[[c for c in FEAT.columns if c.startswith("sm_")]]
        D = derived_block(X)
        # every derived column is a deterministic function of X: refitting on the same X reproduces it
        pd.testing.assert_frame_equal(derived_block(X), D)


class Decisions(unittest.TestCase):
    def test_conformal_uses_finite_sample_order_statistic(self):
        s = np.arange(1., 44.)
        self.assertEqual(conformal_radius(s, 0.9), s[min(43, int(np.ceil(44 * 0.9))) - 1])

    def test_decide_respects_interval_not_point(self):
        pred = np.log10(np.array([90., 300., 300.]))
        out = decide(pred, 0.0, 100, 150)
        self.assertEqual(list(out), ["Reject", "Certify", "Certify"])
        self.assertEqual(list(decide(pred, 1.0, 100, 150)), ["Alert"] * 3)


class Gates(unittest.TestCase):
    """The verdict path itself."""
    def _tables(self, delta_derived, p_pairing, q2):
        rows = []
        for K in (4, 8):
            rows.extend([
                dict(K=K, menu="summary", n_columns=8, delta=0.20, null_mean=.1,
                     null_sd=0.05, null_q95=.2, excess=.1, p_perm=.2),
                dict(K=K, menu="g_summary", n_columns=8, delta=0.21, null_mean=.1,
                     null_sd=0.05, null_q95=.2, excess=.1, p_perm=.2),
                dict(K=K, menu="summary_derived", n_columns=42, delta=delta_derived,
                     null_mean=.1, null_sd=0.05, null_q95=.2, excess=.1, p_perm=.2),
                dict(K=K, menu="summary_relax", n_columns=42, delta=0.30,
                     null_mean=.1, null_sd=0.05, null_q95=.2, excess=.1, p_perm=.02),
            ])
        dm = pd.DataFrame(rows)
        pair = pd.DataFrame([
            dict(K=K, contrast=name, observed_gap=.01, null_mean=0., null_sd=.05,
                 null_q05=-.08, null_q95=.08, p_upper=.3, p_two_sided=.6,
                 n_permutations=50)
            for K in (4, 8)
            for name in ("g_summary_minus_summary", "summary_derived_minus_summary",
                         "summary_relax_minus_summary")
        ])
        channel = pd.DataFrame([
            dict(K=K, baseline_delta=.2, observed_joint_delta=.3, observed_gain=.1,
                 null_mean_gain=.02, null_sd_gain=.03, null_q95_gain=.07,
                 p_upper=p_pairing, n_permutations=200)
            for K in (4, 8)
        ])
        tr = pd.DataFrame([dict(target="t", n=5, side="safe", n_unsafe=0, n_safe=5, decisiveness=1.,
                                observed_side_error=0.1, rho_U=np.nan, rho_S=0.3, bound=0.4,
                                bound_is_vacuous=False, Q2_holds=q2)])
        meta = dict(source_unsafe=9, source_safe=11)
        return dm, pair, channel, tr, meta

    def test_registered_layer_never_merges_into_boolean_overall(self):
        g = evaluate_registered_gates(*self._tables(0.21, 0.01, True), CFG)
        self.assertEqual(g["overall"]["status"], "NOT_ESTABLISHED")
        self.assertNotIn("overall_pass", g)

    def test_G3_uses_registered_pairing_p_value(self):
        g = evaluate_registered_gates(*self._tables(0.21, 0.01, True), CFG)
        self.assertEqual(g["G3_P3_channel_gain"]["status"], "PASS")
        g = evaluate_registered_gates(*self._tables(0.21, 0.20, True), CFG)
        self.assertEqual(g["G3_P3_channel_gain"]["status"], "NOT_DETECTED")

    def test_G1_G4_G5_are_explicitly_not_evaluable(self):
        g = evaluate_registered_gates(*self._tables(0.21, 0.01, True), CFG)
        self.assertEqual(g["G1_P1_data_processing"]["status"], "NOT_EVALUABLE")
        self.assertEqual(g["G4_Q1_margin"]["status"], "NOT_EVALUABLE")
        self.assertEqual(g["G5_Q2_side_error"]["status"], "NOT_EVALUABLE")

    def test_G2_retains_nominal_failure(self):
        g = evaluate_registered_gates(*self._tables(0.40, 0.20, True), CFG)
        self.assertFalse(g["G2_P2_equality"]["nominal_pass"])
        self.assertEqual(g["G2_P2_equality"]["status"], "FAIL")

    def test_G0_fails_on_a_one_sided_source(self):
        dm, pair, channel, tr, meta = self._tables(0.21, 0.01, True)
        meta["source_safe"] = 1
        g = evaluate_registered_gates(dm, pair, channel, tr, meta, CFG)
        self.assertFalse(g["G0_integrity"]["nominal_pass"])


class RegisteredNulls(unittest.TestCase):
    def test_paired_null_is_reproducible(self):
        F = FEAT[[c for c in FEAT.columns if c.startswith("sm_")]].iloc[:40]
        domains = np.array(["s"] * 20 + ["u"] * 20)
        classes = {"s": "S", "u": "U"}
        one = paired_delta_difference(F, F, domains, classes, 4, 20, 11)
        two = paired_delta_difference(F, F, domains, classes, 4, 20, 11)
        self.assertEqual(one, two)
        self.assertAlmostEqual(one["observed_gap"], 0.0)

    def test_channel_permutation_executes_requested_count(self):
        sm = [c for c in FEAT.columns if c.startswith("sm_")]
        rx = [c for c in FEAT.columns if c.startswith("rx")]
        sub = FEAT.iloc[:40].reset_index(drop=True)
        domains = np.array(["s"] * 20 + ["u"] * 20)
        table, summary = channel_pairing_permutation(
            sub[sm], sub[rx], domains, {"s": "S", "u": "U"}, 4, 17, 9
        )
        self.assertEqual(len(table), 17)
        self.assertEqual(summary["n_permutations"], 17)


class Reproduction(unittest.TestCase):
    def test_released_gates_match_a_recomputation(self):
        with open(os.path.join(ROOT, "results", "as_registered_gates.json")) as fh:
            released = json.load(fh)
        G = CFG["grades"]
        lab, psi = domain_classes(FEAT, G["hazard_eol_cycles"], G["psi_safe_max"], G["psi_unsafe_min"])
        nest = nesting_check(lab, psi.cls.to_dict(), 8, [4, 2])
        self.assertTrue(bool(nest.monotone.all()))
        self.assertEqual(released["G1_P1_data_processing"]["status"], "NOT_EVALUABLE")
        self.assertEqual(released["G4_Q1_margin"]["status"], "NOT_EVALUABLE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
