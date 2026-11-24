"""Exact computational witnesses for the v04 certification-limit theory."""

from .core import (
    binary_proxy_joint_pmf,
    convex_hull_tv_lp,
    direct_observational_pmf,
    dual_separator_lp,
    hidden_observational_pmf,
    latent_flip_probability,
    policy_risk,
    proxy_delta,
    total_variation,
)

__all__ = [
    "binary_proxy_joint_pmf",
    "convex_hull_tv_lp",
    "direct_observational_pmf",
    "dual_separator_lp",
    "hidden_observational_pmf",
    "latent_flip_probability",
    "policy_risk",
    "proxy_delta",
    "total_variation",
]
