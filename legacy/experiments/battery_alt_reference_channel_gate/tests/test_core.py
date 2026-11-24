"""Regression tests for alt_gate.core, including the two bugs found in earlier packages."""
import os, sys
import numpy as np
from scipy.optimize import linprog
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
from alt_gate.core import (count_states, multinomial_pmf, hull_tv,
                           max_min_decisiveness, sion_gap)


def _dense_max_min(S, U, alpha, beta):
    """The pre-sparsification dense reference implementation."""
    K = S.shape[1]; NV = 2 * K + 1
    A, b = [], []
    for p in U:
        r = np.zeros(NV); r[:K] = p; A.append(r); b.append(alpha)
    for p in S:
        r = np.zeros(NV); r[K:2 * K] = p; A.append(r); b.append(beta)
    for p in np.vstack([S, U]):
        r = np.zeros(NV); r[:K] = -p; r[K:2 * K] = -p; r[-1] = 1.0
        A.append(r); b.append(0.0)
    for j in range(K):
        r = np.zeros(NV); r[j] = 1.0; r[K + j] = 1.0; A.append(r); b.append(1.0)
    c = np.zeros(NV); c[-1] = -1.0
    res = linprog(c, A_ub=np.array(A), b_ub=np.array(b),
                  bounds=[(0.0, 1.0)] * (2 * K) + [(0.0, 1.0)], method="highs")
    assert res.success
    return float(res.x[-1])


def test_sparse_matches_dense():
    """The sparse LP rewrite must reproduce the dense one exactly."""
    rng = np.random.default_rng(7)
    for _ in range(25):
        K = int(rng.integers(2, 7))
        S = rng.dirichlet(np.ones(K), size=int(rng.integers(1, 5)))
        U = rng.dirichlet(np.ones(K), size=int(rng.integers(1, 5)))
        a, b = float(rng.uniform(0, .3)), float(rng.uniform(0, .3))
        assert abs(max_min_decisiveness(S, U, a, b) - _dense_max_min(S, U, a, b)) < 1e-9


def test_multinomial_zero_probability_symbol():
    """Regression: 0*log(0) must be 0, not NaN.  A NaN mapped to -inf silently
    zeroed 41.5% of models in the NASA RW package and faked Delta == 0."""
    st = count_states(3, 3)
    p = np.array([0.5, 0.5, 0.0])
    pm = multinomial_pmf(p, st, 3)
    assert np.isfinite(pm).all()
    assert abs(pm.sum() - 1.0) < 1e-12
    assert (pm[st[:, 2] > 0] == 0).all()          # states touching the dead symbol
    assert abs(pm[np.all(st == [3, 0, 0], axis=1)][0] - 0.125) < 1e-12


def test_multinomial_normalises():
    rng = np.random.default_rng(3)
    for n in (1, 2, 5):
        for K in (2, 3, 4):
            p = rng.dirichlet(np.ones(K))
            assert abs(multinomial_pmf(p, count_states(n, K), n).sum() - 1.0) < 1e-10


def test_hull_tv_basics():
    P = np.array([[1.0, 0.0]]); Q = np.array([[0.0, 1.0]])
    assert abs(hull_tv(P, Q) - 1.0) < 1e-9
    assert abs(hull_tv(P, P) - 0.0) < 1e-9
    # overlapping hulls collide exactly
    S = np.array([[.8, .2], [.2, .8]]); U = np.array([[.5, .5]])
    assert hull_tv(S, U) < 1e-9


def test_sion_identity():
    """gamma*(n) = Delta_E(n)/2 for the hull game."""
    rng = np.random.default_rng(11)
    for _ in range(30):
        K = int(rng.integers(2, 6))
        S = rng.dirichlet(np.ones(K), size=3)
        U = rng.dirichlet(np.ones(K), size=3)
        assert abs(sion_gap(S, U) / 2.0 - hull_tv(S, U) / 2.0) < 1e-8


def test_bound_holds_and_is_not_generally_tight():
    """D <= min(1, alpha+beta+TV) always; the inequality is strict in general.
    (An earlier draft of this test asserted equality for every two-point experiment.
    That is false: equality is a boundary phenomenon, see the two tests below.)"""
    rng = np.random.default_rng(5)
    strict = 0
    for _ in range(40):
        K = int(rng.integers(2, 6))
        p, q = rng.dirichlet(np.ones(K)), rng.dirichlet(np.ones(K))
        tv = 0.5 * np.abs(p - q).sum()
        D = max_min_decisiveness(p[None, :], q[None, :], 0.05, 0.05)
        bound = min(1.0, 0.05 + 0.05 + tv)
        assert D <= bound + 1e-9
        strict += D < bound - 1e-6
    assert strict > 0


def test_attainment_at_collision():
    """Delta = 0 forces D = alpha + beta exactly -- the sharp case of the theorem."""
    rng = np.random.default_rng(13)
    for _ in range(20):
        K = int(rng.integers(2, 6))
        p = rng.dirichlet(np.ones(K))
        a, b = float(rng.uniform(.01, .3)), float(rng.uniform(.01, .3))
        assert abs(max_min_decisiveness(p[None, :], p[None, :], a, b) - (a + b)) < 1e-9
    # and for genuinely different models whose hulls still collide
    S = np.array([[.8, .2], [.2, .8]]); U = np.array([[.5, .5]])
    assert hull_tv(S, U) < 1e-9
    assert abs(max_min_decisiveness(S, U, .05, .05) - .10) < 1e-9


def test_attainment_at_saturation():
    """When alpha+beta+TV >= 1 the bound saturates and D = 1 is attained."""
    p = np.array([1.0, 0.0]); q = np.array([0.0, 1.0])          # TV = 1
    assert abs(max_min_decisiveness(p[None, :], q[None, :], 0.05, 0.05) - 1.0) < 1e-9


def test_data_processing_coarsening():
    """A deterministic coarsening cannot raise Delta."""
    rng = np.random.default_rng(2)
    for _ in range(20):
        S = rng.dirichlet(np.ones(4), size=3); U = rng.dirichlet(np.ones(4), size=3)
        g = np.array([[1, 0], [1, 0], [0, 1], [0, 1]], float)   # {0,1}->0, {2,3}->1
        assert hull_tv(S @ g, U @ g) <= hull_tv(S, U) + 1e-9
