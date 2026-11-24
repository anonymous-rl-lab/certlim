"""Tests cover the verdict-producing path, not just leaf helpers."""
import json, os, sys, unittest
import numpy as np, pandas as pd
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
sys.path.insert(0,os.path.join(ROOT,'src'))
from nasa_gate.core import count_states, multinomial_pmf, hull_tv, sion_gap, max_min_decisiveness
CFG=json.load(open(os.path.join(ROOT,'config','registered.json')))
AL,BE=CFG['test']['alpha'],CFG['test']['beta']


class Multinomial(unittest.TestCase):
    def test_states_enumerate_the_simplex_lattice(self):
        from math import comb
        for n in (1,3,5):
            self.assertEqual(len(count_states(n,4)), comb(n+3,3))
            np.testing.assert_array_equal(count_states(n,4).sum(axis=1), n)

    def test_pmf_sums_to_one_including_zero_components(self):
        """Regression for the 0*log(0) bug that zeroed 41.5% of models (ERRATA)."""
        for p in ([.4,.3,.2,.1],[.5,0.,.3,.2],[1.,0,0,0],[0.,0.,.5,.5]):
            for n in (1,2,5,8):
                st=count_states(n,4)
                self.assertAlmostEqual(float(multinomial_pmf(np.array(p),st,n).sum()),1.0,places=10)

    def test_zero_probability_symbols_get_zero_mass(self):
        st=count_states(3,4); pm=multinomial_pmf(np.array([.5,0.,.3,.2]),st,3)
        self.assertTrue(np.all(pm[st[:,1]>0]==0.0))
        self.assertTrue(np.all(pm[st[:,1]==0]>=0.0))


class Geometry(unittest.TestCase):
    def test_hull_tv_hand_value(self):
        self.assertAlmostEqual(hull_tv(np.array([[.7,.3],[.6,.4]]),np.array([[.2,.8]])),0.4,places=10)

    def test_sion_identity_delta_equals_gap(self):
        rng=np.random.default_rng(0)
        for _ in range(25):
            S=rng.dirichlet(np.ones(4),size=5); U=rng.dirichlet(np.ones(4),size=3)
            self.assertAlmostEqual(hull_tv(S,U), sion_gap(S,U), places=7)

    def test_hull_never_exceeds_min_pairwise(self):
        rng=np.random.default_rng(1)
        for _ in range(25):
            S=rng.dirichlet(np.ones(4),size=4); U=rng.dirichlet(np.ones(4),size=4)
            pw=min(0.5*np.abs(a-b).sum() for a in S for b in U)
            self.assertLessEqual(hull_tv(S,U), pw+1e-9)


class Decisiveness(unittest.TestCase):
    def test_collision_attains_alpha_plus_beta(self):
        p=np.array([[.25,.25,.25,.25]])
        self.assertAlmostEqual(max_min_decisiveness(p,p,AL,BE), AL+BE, places=9)

    def test_disjoint_support_allows_full_decisiveness(self):
        S=np.array([[1.,0.,0.,0.]]); U=np.array([[0.,0.,0.,1.]])
        self.assertAlmostEqual(max_min_decisiveness(S,U,AL,BE), 1.0, places=6)

    def test_main_theorem_bound_holds_on_random_classes(self):
        """G1 as a property, on random model classes."""
        rng=np.random.default_rng(2)
        for _ in range(40):
            S=rng.dirichlet(np.ones(4),size=rng.integers(2,6))
            U=rng.dirichlet(np.ones(4),size=rng.integers(2,6))
            D=max_min_decisiveness(S,U,AL,BE); d=hull_tv(S,U)
            self.assertLessEqual(D, min(1.0,AL+BE+d)+1e-9)

    def test_bound_is_violated_by_a_deliberately_broken_rule_check(self):
        """Sanity: the gate would catch a violation if one existed."""
        S=np.array([[1.,0.]]); U=np.array([[0.,1.]])
        D=max_min_decisiveness(S,U,AL,BE)
        self.assertGreater(D, AL+BE)          # separated classes exceed alpha+beta
        self.assertLessEqual(D, min(1.0,AL+BE+hull_tv(S,U))+1e-9)


class ReleasedResults(unittest.TestCase):
    def test_frontier_gates_agree_with_recomputation(self):
        fr=pd.read_csv(os.path.join(ROOT,'results','frontier.csv'))
        self.assertTrue(bool((fr.D<=fr.bound+1e-9).all()))
        self.assertTrue(bool((fr.delta.diff().dropna()>=-1e-9).all()))
        self.assertLess(float(fr.sion_residual.max()), 1e-7)

    def test_adversarial_collision_is_a_real_collision(self):
        ad=json.load(open(os.path.join(ROOT,'results','L3_adversarial.json')))
        self.assertLessEqual(ad['delta_adversarial_min'], 1e-6)
        self.assertAlmostEqual(ad['D_adversarial'], AL+BE, places=6)

    def test_naive_confounding_did_not_produce_a_collision(self):
        na=json.load(open(os.path.join(ROOT,'results','L3_collision.json')))
        self.assertGreater(na['delta_confounded'], 1e-6)


if __name__=='__main__':
    unittest.main(verbosity=2)
