from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_certification.core import (  # noqa: E402
    bernoulli_count_pmfs,
    binary_proxy_joint_pmf,
    convex_hull_tv_lp,
    direct_observational_pmf,
    dual_separator_lp,
    grade,
    hidden_observational_pmf,
    latent_flip_probability,
    policy_risk,
    proxy_delta,
    proxy_rule_exact_errors,
    pushforward_pmf,
    total_variation,
)


class TestExactCollision(unittest.TestCase):
    def test_exact_old_evidence_collision_and_data_processing(self) -> None:
        for q in (0.05, 0.2, 0.45):
            direct = direct_observational_pmf(q)
            hidden = hidden_observational_pmf(q)
            self.assertAlmostEqual(total_variation(direct, hidden), 0.0, places=14)
            direct_xor = pushforward_pmf(direct, lambda x: x[0] ^ x[1])
            hidden_xor = pushforward_pmf(hidden, lambda x: x[0] ^ x[1])
            self.assertAlmostEqual(total_variation(direct_xor, hidden_xor), 0.0, places=14)
            self.assertAlmostEqual(sum(direct.values()), 1.0, places=14)
            self.assertAlmostEqual(sum(hidden.values()), 1.0, places=14)

    def test_latent_flip_equation(self) -> None:
        for q in (0.01, 0.2, 0.49):
            r = latent_flip_probability(q)
            self.assertAlmostEqual(2.0 * r * (1.0 - r), q, places=14)

    def test_policy_dependent_role_flip(self) -> None:
        q = 0.2
        self.assertAlmostEqual(policy_risk("direct", q, 1), 0.8)
        self.assertAlmostEqual(policy_risk("hidden", q, 1), 0.5)
        self.assertAlmostEqual(policy_risk("direct", q, 0), 0.2)
        self.assertAlmostEqual(policy_risk("hidden", q, 0), 0.5)
        self.assertEqual(grade(0.8, 0.6, 0.7), "unsafe")
        self.assertEqual(grade(0.5, 0.6, 0.7), "safe")
        self.assertEqual(grade(0.2, 0.3, 0.4), "safe")
        self.assertEqual(grade(0.5, 0.3, 0.4), "unsafe")


class TestFiniteBlockGeometry(unittest.TestCase):
    def test_preregistered_landmarks_and_sion_duality(self) -> None:
        safe_1 = bernoulli_count_pmfs((0.25, 0.75), 1)
        unsafe_1 = bernoulli_count_pmfs((0.5,), 1)
        safe_2 = bernoulli_count_pmfs((0.25, 0.75), 2)
        unsafe_2 = bernoulli_count_pmfs((0.5,), 2)
        primal_1 = convex_hull_tv_lp(safe_1, unsafe_1)
        primal_2 = convex_hull_tv_lp(safe_2, unsafe_2)
        dual_2 = dual_separator_lp(safe_2, unsafe_2)
        self.assertAlmostEqual(primal_1.delta, 0.0, places=12)
        self.assertAlmostEqual(primal_2.delta, 0.125, places=12)
        self.assertAlmostEqual(dual_2.gap, primal_2.delta, places=12)
        self.assertAlmostEqual(dual_2.gamma, 0.0625, places=12)

    def test_frontier_is_monotone_on_audit_range(self) -> None:
        deltas = []
        for n in range(1, 17):
            safe = bernoulli_count_pmfs((0.25, 0.75), n)
            unsafe = bernoulli_count_pmfs((0.5,), n)
            deltas.append(convex_hull_tv_lp(safe, unsafe).delta)
        self.assertTrue(np.all(np.diff(deltas) >= -1e-10))


class TestRegisteredProxy(unittest.TestCase):
    def test_proxy_tv_and_statistic_gap_equal_delta(self) -> None:
        for q in (0.05, 0.2, 0.45):
            for s in (0.05, 0.2, 0.45):
                direct = binary_proxy_joint_pmf("direct", q, s)
                hidden = binary_proxy_joint_pmf("hidden", q, s)
                delta = proxy_delta(q, s)
                direct_t = sum(prob * (a == w) for (a, _h, w), prob in direct.items())
                hidden_t = sum(prob * (a == w) for (a, _h, w), prob in hidden.items())
                self.assertAlmostEqual(total_variation(direct, hidden), delta, places=12)
                self.assertAlmostEqual(hidden_t - direct_t, delta, places=12)
                self.assertGreater(delta, 0.0)

    def test_exact_errors_respect_hoeffding(self) -> None:
        for n in (16, 64, 256):
            result = proxy_rule_exact_errors(0.2, 0.15, n)
            self.assertLessEqual(result["direct_error_exact"], result["hoeffding_bound"] + 1e-12)
            self.assertLessEqual(result["hidden_error_exact"], result["hoeffding_bound"] + 1e-12)


if __name__ == "__main__":
    unittest.main()
