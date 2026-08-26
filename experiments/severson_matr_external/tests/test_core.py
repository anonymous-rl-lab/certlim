import numpy as np

from severson_gate.evaluate import _conformal_radius
from severson_gate.raw import curve_features, parse_policy, summarize_window


def test_policy_parser():
    assert parse_policy("5.4C(60%)-3.6C") == (5.4, 0.6, 3.6)


def test_summarize_window_obeys_horizon():
    cycles = np.arange(1, 11)
    values = 2.0 * cycles + 1.0
    result = summarize_window(cycles, values, 5)
    assert result["start"] == 5.0
    assert result["end"] == 11.0
    assert np.isclose(result["slope"], 2.0)


def test_curve_features_are_finite():
    result = curve_features(np.array([-0.3, -0.2, -0.1]))
    assert set(result) == {"log_abs_min", "log_var"}
    assert all(np.isfinite(value) for value in result.values())


def test_conformal_uses_finite_sample_order_statistic():
    scores = np.arange(1.0, 11.0)
    assert _conformal_radius(scores, 0.8) == 9.0
