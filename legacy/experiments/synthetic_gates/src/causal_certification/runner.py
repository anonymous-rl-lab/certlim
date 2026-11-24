from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from math import ceil, isfinite, log, sqrt
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy

from .core import (
    binary_proxy_joint_pmf,
    direct_observational_pmf,
    expectation,
    finite_block_frontier,
    grade,
    hidden_observational_pmf,
    policy_risk,
    proxy_delta,
    proxy_rule_exact_errors,
    pushforward_pmf,
    total_variation,
)


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"cannot serialize {type(value)}")


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, default=_json_default) + "\n",
        encoding="utf-8",
    )


def _config_hash(config_path: Path) -> str:
    return hashlib.sha256(config_path.read_bytes()).hexdigest()


def _gate(name: str, passed: bool, observed: Any, criterion: str) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "observed": observed, "criterion": criterion}


def _collision_and_policy_rows(q_values: list[float]) -> tuple[pd.DataFrame, pd.DataFrame]:
    collision_rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []
    for q in q_values:
        direct = direct_observational_pmf(q)
        hidden = hidden_observational_pmf(q)
        xor_direct = pushforward_pmf(direct, lambda x: x[0] ^ x[1])
        xor_hidden = pushforward_pmf(hidden, lambda x: x[0] ^ x[1])
        collision_rows.append(
            {
                "q": q,
                "old_evidence_tv": total_variation(direct, hidden),
                "xor_feature_tv": total_variation(xor_direct, xor_hidden),
                "direct_mass": sum(direct.values()),
                "hidden_mass": sum(hidden.values()),
                "max_cell_difference": max(abs(direct[k] - hidden[k]) for k in direct),
            }
        )

        # For pi_1 choose 1/2 < tau_S < tau_U < 1-q.
        high_gap = 0.5 - q
        high_safe = 0.5 + high_gap / 3.0
        high_unsafe = 0.5 + 2.0 * high_gap / 3.0
        # For pi_0 choose q < tau_S < tau_U < 1/2.
        low_safe = q + high_gap / 3.0
        low_unsafe = q + 2.0 * high_gap / 3.0
        for action, tau_safe, tau_unsafe in (
            (1, high_safe, high_unsafe),
            (0, low_safe, low_unsafe),
        ):
            for model in ("direct", "hidden"):
                risk = policy_risk(model, q, action)
                expected = (
                    "unsafe"
                    if action == 1 and model == "direct"
                    else "safe"
                    if action == 1 and model == "hidden"
                    else "safe"
                    if action == 0 and model == "direct"
                    else "unsafe"
                )
                policy_rows.append(
                    {
                        "q": q,
                        "policy_action": action,
                        "model": model,
                        "risk": risk,
                        "tau_safe": tau_safe,
                        "tau_unsafe": tau_unsafe,
                        "grade": grade(risk, tau_safe, tau_unsafe),
                        "expected_grade": expected,
                    }
                )
    return pd.DataFrame(collision_rows), pd.DataFrame(policy_rows)


def _proxy_geometry_rows(q_values: list[float], s_values: list[float]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for q in q_values:
        for s in s_values:
            direct = binary_proxy_joint_pmf("direct", q, s)
            hidden = binary_proxy_joint_pmf("hidden", q, s)
            delta = proxy_delta(q, s)
            direct_t = expectation(direct, lambda x: float(x[0] == x[2]))
            hidden_t = expectation(hidden, lambda x: float(x[0] == x[2]))
            direct_w = expectation(direct, lambda x: float(x[2]))
            hidden_w = expectation(hidden, lambda x: float(x[2]))
            rows.append(
                {
                    "q": q,
                    "s": s,
                    "delta_formula": delta,
                    "augmented_tv": total_variation(direct, hidden),
                    "direct_t_mean": direct_t,
                    "hidden_t_mean": hidden_t,
                    "t_mean_gap": hidden_t - direct_t,
                    "direct_w_mean": direct_w,
                    "hidden_w_mean": hidden_w,
                    "direct_mass": sum(direct.values()),
                    "hidden_mass": sum(hidden.values()),
                }
            )
    return pd.DataFrame(rows)


def _proxy_rates(
    q_values: list[float], s_values: list[float], sample_sizes: list[int]
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for q in q_values:
        for s in s_values:
            for n in sample_sizes:
                rows.append({"q": q, "s": s, **proxy_rule_exact_errors(q, s, n)})
    return pd.DataFrame(rows)


def _proxy_monte_carlo(stage: dict[str, Any], exact: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    seed_rows: list[dict[str, Any]] = []
    exact_index = exact.set_index(["q", "s", "n"])
    for seed in stage["random_seeds"]:
        rng = np.random.default_rng(seed)
        for key, row in exact_index.iterrows():
            q, s, n = key
            simulations = int(stage["simulations_per_seed"])
            critical = int(row["critical_count"])
            delta = float(row["delta"])
            direct_counts = rng.binomial(int(n), 0.5, size=simulations)
            hidden_counts = rng.binomial(int(n), 0.5 + delta, size=simulations)
            seed_rows.append(
                {
                    "seed": seed,
                    "q": q,
                    "s": s,
                    "n": int(n),
                    "simulations": simulations,
                    "direct_errors": int(np.count_nonzero(direct_counts >= critical)),
                    "hidden_errors": int(np.count_nonzero(hidden_counts < critical)),
                }
            )
    by_seed = pd.DataFrame(seed_rows)
    aggregate = (
        by_seed.groupby(["q", "s", "n"], as_index=False)
        .agg(
            simulations=("simulations", "sum"),
            direct_errors=("direct_errors", "sum"),
            hidden_errors=("hidden_errors", "sum"),
        )
        .merge(exact, on=["q", "s", "n"], how="left", validate="one_to_one")
    )
    aggregate["direct_error_empirical"] = aggregate["direct_errors"] / aggregate["simulations"]
    aggregate["hidden_error_empirical"] = aggregate["hidden_errors"] / aggregate["simulations"]
    for side in ("direct", "hidden"):
        p = aggregate[f"{side}_error_exact"]
        empirical = aggregate[f"{side}_error_empirical"]
        se = np.sqrt(p * (1.0 - p) / aggregate["simulations"])
        tolerance = np.maximum(
            float(stage["mc_sigma_multiplier"]) * se,
            float(stage["mc_absolute_tolerance_floor"]),
        )
        aggregate[f"{side}_mc_abs_error"] = np.abs(empirical - p)
        aggregate[f"{side}_mc_tolerance"] = tolerance
        aggregate[f"{side}_mc_pass"] = aggregate[f"{side}_mc_abs_error"] <= tolerance
    return by_seed, aggregate


def _augment_frontier(
    frontier: pd.DataFrame,
    alpha: float,
    beta: float,
    numerical_tolerance: float,
) -> pd.DataFrame:
    out = frontier.copy()
    threshold = 1.0 - alpha - beta
    confidence_log = max(log(1.0 / alpha), log(1.0 / beta))
    out["decisiveness_upper_bound"] = alpha + beta + out["delta"]
    out["no_alert_necessary_met"] = out["delta"] >= threshold
    blocks: list[float] = []
    totals: list[float] = []
    for n, delta in zip(out["n"], out["delta"]):
        if delta <= numerical_tolerance:
            blocks.append(float("inf"))
            totals.append(float("inf"))
        else:
            m = ceil(2.0 * confidence_log / (delta * delta))
            blocks.append(float(m))
            totals.append(float(n * m))
    out["hoeffding_blocks"] = blocks
    out["hoeffding_total_samples"] = totals
    return out


def _build_gates(
    contract: dict[str, Any],
    stage_name: str,
    collision: pd.DataFrame,
    policy: pd.DataFrame,
    proxy: pd.DataFrame,
    frontier: pd.DataFrame,
    proxy_rates: pd.DataFrame | None,
    proxy_mc: pd.DataFrame | None,
) -> list[dict[str, Any]]:
    tol = float(contract["numerical_tolerance"])
    landmarks = contract["preregistered_landmarks"]
    gates: list[dict[str, Any]] = []
    max_collision = float(collision["old_evidence_tv"].max())
    max_derived = float(collision["xor_feature_tv"].max())
    max_mass_residual = float(
        max(
            (collision["direct_mass"] - 1.0).abs().max(),
            (collision["hidden_mass"] - 1.0).abs().max(),
            (proxy["direct_mass"] - 1.0).abs().max(),
            (proxy["hidden_mass"] - 1.0).abs().max(),
        )
    )
    gates.append(_gate("G1_exact_old_evidence_collision", max_collision <= tol, max_collision, f"max TV <= {tol}"))
    gates.append(_gate("G2_policy_grade_flip", bool((policy["grade"] == policy["expected_grade"]).all()), int((policy["grade"] != policy["expected_grade"]).sum()), "zero grade mismatches for both policies"))
    gates.append(_gate("G3_data_processing_negative_control", max_derived <= tol, max_derived, f"TV of XOR-derived old evidence <= {tol}"))
    gates.append(_gate("G4_probability_normalization", max_mass_residual <= tol, max_mass_residual, f"max mass residual <= {tol}"))

    proxy_formula_residual = float(
        max(
            (proxy["augmented_tv"] - proxy["delta_formula"]).abs().max(),
            (proxy["t_mean_gap"] - proxy["delta_formula"]).abs().max(),
            (proxy["direct_t_mean"] - 0.5).abs().max(),
            (proxy["direct_w_mean"] - 0.5).abs().max(),
            (proxy["hidden_w_mean"] - 0.5).abs().max(),
        )
    )
    gates.append(_gate("G5_registered_proxy_breaks_gate", bool((proxy["augmented_tv"] > tol).all() and proxy_formula_residual <= tol), {"min_augmented_tv": float(proxy["augmented_tv"].min()), "max_formula_residual": proxy_formula_residual}, f"all augmented TV > {tol} and formula residual <= {tol}"))

    indexed = frontier.set_index("n")
    delta_1 = float(indexed.loc[1, "delta"])
    delta_2 = float(indexed.loc[2, "delta"])
    gamma_2 = float(indexed.loc[2, "gamma"])
    positive = frontier.loc[frontier["delta"] > tol, "n"]
    n_star = int(positive.min()) if not positive.empty else None
    landmark_residual = max(
        abs(delta_1 - float(landmarks["delta_1"])),
        abs(delta_2 - float(landmarks["delta_2"])),
        abs(gamma_2 - float(landmarks["gamma_2"])),
    )
    gates.append(_gate("G6_finite_block_landmarks", bool(landmark_residual <= tol and n_star == int(landmarks["n_star"])), {"delta_1": delta_1, "delta_2": delta_2, "gamma_2": gamma_2, "n_star": n_star, "max_residual": landmark_residual}, "Delta(1)=0, Delta(2)=1/8, gamma(2)=1/16, n*=2"))
    min_increment = float(frontier["delta"].diff().dropna().min())
    gates.append(_gate("G7_frontier_monotonicity", min_increment >= -tol, min_increment, f"min Delta(n)-Delta(n-1) >= -{tol}"))
    dual_rows = frontier[frontier["primal_dual_residual"].notna()]
    max_dual_residual = float(dual_rows["primal_dual_residual"].max())
    gates.append(_gate("G8_sion_primal_dual_identity", max_dual_residual <= tol, max_dual_residual, f"max |primal TV-dual gap| <= {tol}"))

    if stage_name == "small":
        threshold = 1.0 - float(contract["alpha"]) - float(contract["beta"])
        qualifying = frontier.loc[frontier["delta"] >= threshold, "n"]
        no_alert_min = int(qualifying.min()) if not qualifying.empty else None
        gates.append(_gate("G9_no_alert_necessary_threshold", no_alert_min == int(landmarks["no_alert_min_n"]), no_alert_min, f"first n with Delta(n)>=1-alpha-beta is {landmarks['no_alert_min_n']}"))

        finite_design = frontier[np.isfinite(frontier["hoeffding_total_samples"])]
        best_total = float(finite_design["hoeffding_total_samples"].min())
        best_n = int(finite_design.loc[finite_design["hoeffding_total_samples"] == best_total, "n"].min())
        design_ok = best_n == int(landmarks["hoeffding_optimal_block_n"]) and int(best_total) == int(landmarks["hoeffding_optimal_total_n"])
        gates.append(_gate("G10_hoeffding_block_design", design_ok, {"block_n": best_n, "total_n": int(best_total)}, f"argmin is n={landmarks['hoeffding_optimal_block_n']} with N={landmarks['hoeffding_optimal_total_n']}"))

        if proxy_rates is None or proxy_mc is None:
            gates.append(_gate("G11_proxy_exact_hoeffding_bound", False, None, "small stage requires exact proxy rates"))
            gates.append(_gate("G12_seeded_mc_matches_exact", False, None, "small stage requires seeded Monte Carlo"))
        else:
            max_bound_violation = float(
                max(
                    0.0,
                    (proxy_rates["direct_error_exact"] - proxy_rates["hoeffding_bound"]).max(),
                    (proxy_rates["hidden_error_exact"] - proxy_rates["hoeffding_bound"]).max(),
                )
            )
            gates.append(_gate("G11_proxy_exact_hoeffding_bound", max_bound_violation <= tol, max_bound_violation, f"both exact errors <= exp(-n delta^2/2)+{tol}"))
            mc_failures = int((~proxy_mc["direct_mc_pass"]).sum() + (~proxy_mc["hidden_mc_pass"]).sum())
            max_mc_ratio = float(
                max(
                    (proxy_mc["direct_mc_abs_error"] / proxy_mc["direct_mc_tolerance"]).max(),
                    (proxy_mc["hidden_mc_abs_error"] / proxy_mc["hidden_mc_tolerance"]).max(),
                )
            )
            gates.append(_gate("G12_seeded_mc_matches_exact", mc_failures == 0, {"failures": mc_failures, "max_error_to_tolerance_ratio": max_mc_ratio}, "zero condition-side failures under preregistered 5-SE/0.01 tolerance"))
    return gates


def _report_markdown(
    stage_name: str,
    config_hash: str,
    gates: list[dict[str, Any]],
    frontier: pd.DataFrame,
    proxy: pd.DataFrame,
    runtime_seconds: float,
    stage: dict[str, Any],
    contract: dict[str, Any],
) -> str:
    passed = all(gate["passed"] for gate in gates)
    lines = [
        f"# v04 生死门实验报告：{stage_name}",
        "",
        f"**总判定：{'PASS' if passed else 'FAIL'}**",
        "",
        f"- 理论版本：`{contract['theory_version']}`",
        f"- 实验版本：`{contract['experiment_version']}`",
        f"- 冻结配置 SHA-256：`{config_hash}`",
        f"- 运行时：{runtime_seconds:.3f} 秒（CPU；GPU 未使用；外部 API 成本 0 美元）",
        f"- 随机种子：{stage['random_seeds'] if stage['random_seeds'] else '无；本阶段为确定性精确计算'}",
        "",
        "## 门控结果",
        "",
        "| Gate | 结果 | 观测值 | 预注册判据 |",
        "|---|---:|---|---|",
    ]
    for gate in gates:
        observed = json.dumps(gate["observed"], ensure_ascii=False, default=_json_default)
        lines.append(f"| {gate['name']} | {'PASS' if gate['passed'] else 'FAIL'} | `{observed}` | {gate['criterion']} |")
    delta_1 = float(frontier.loc[frontier["n"] == 1, "delta"].iloc[0])
    delta_2 = float(frontier.loc[frontier["n"] == 2, "delta"].iloc[0])
    lines.extend(
        [
            "",
            "## 核心读数",
            "",
            f"- 旧证据有限块见证：`Delta(1)={delta_1:.12g}`，`Delta(2)={delta_2:.12g}`。",
            f"- 当前网格代理最弱分离：`min TV={float(proxy['augmented_tv'].min()):.12g}`；这验证注册成对 SCM，不外推为一般代理识别。",
        ]
    )
    if stage_name == "small":
        threshold = 1.0 - float(contract["alpha"]) - float(contract["beta"])
        no_alert_n = int(frontier.loc[frontier["delta"] >= threshold, "n"].min())
        finite = frontier[np.isfinite(frontier["hoeffding_total_samples"])]
        best_total = float(finite["hoeffding_total_samples"].min())
        best_n = int(finite.loc[finite["hoeffding_total_samples"] == best_total, "n"].min())
        lines.extend(
            [
                f"- 无 Alert 的必要距离首次在 `n={no_alert_n}` 达到；这是必要条件，不是充分构造。",
                f"- Hoeffding 构造的最优块长为 `n={best_n}`、总样本上界 `N={int(best_total)}`，严格大于最小破门块长 `n*=2`。",
            ]
        )
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "本报告是注册 SCM 类上的理论—代码验算。它验证精确碰撞、凸包距离、Sion 对偶、有限样本代理率及相应门槛；不构成电池、车辆或工业部署的经验验证。缓冲带 `Theta_A` 也不受极端区域二元规则保护。",
            "",
        ]
    )
    return "\n".join(lines)


def run_stage(config_path: Path, stage_name: str, output_root: Path) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if stage_name not in ("smoke", "small"):
        raise ValueError("stage must be 'smoke' or 'small'; formal scale is intentionally not registered")
    contract = config["contract"]
    stage = config[stage_name]
    output_dir = output_root / stage_name
    output_dir.mkdir(parents=True, exist_ok=True)

    collision, policy = _collision_and_policy_rows(stage["q_values"])
    proxy = _proxy_geometry_rows(stage["q_values"], stage["s_values"])
    frontier = pd.DataFrame(
        finite_block_frontier(
            contract["finite_block_safe_models"],
            contract["finite_block_unsafe_models"],
            range(1, int(stage["delta_n_max"]) + 1),
            int(stage["dual_n_max"]),
        )
    )
    frontier = _augment_frontier(
        frontier,
        float(contract["alpha"]),
        float(contract["beta"]),
        float(contract["numerical_tolerance"]),
    )

    rates: pd.DataFrame | None = None
    seed_mc: pd.DataFrame | None = None
    aggregate_mc: pd.DataFrame | None = None
    if stage["run_monte_carlo"]:
        rates = _proxy_rates(stage["q_values"], stage["s_values"], stage["proxy_sample_sizes"])
        seed_mc, aggregate_mc = _proxy_monte_carlo(stage, rates)

    gates = _build_gates(contract, stage_name, collision, policy, proxy, frontier, rates, aggregate_mc)
    elapsed = time.perf_counter() - started
    config_hash = _config_hash(config_path)
    summary = {
        "stage": stage_name,
        "status": "PASS" if all(gate["passed"] for gate in gates) else "FAIL",
        "all_gates_passed": all(gate["passed"] for gate in gates),
        "gate_count": len(gates),
        "runtime_seconds": elapsed,
        "config_sha256": config_hash,
        "theory_version": contract["theory_version"],
        "experiment_version": contract["experiment_version"],
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "formal_stage_registered": False,
    }
    runtime = {
        "runtime_seconds": elapsed,
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "gpu_used": False,
        "external_api_cost_usd": 0.0,
        "random_seeds": stage["random_seeds"],
        "simulations_per_seed": stage.get("simulations_per_seed", 0),
    }

    collision.to_csv(output_dir / "collision.csv", index=False)
    policy.to_csv(output_dir / "policy_flip.csv", index=False)
    proxy.to_csv(output_dir / "proxy_geometry.csv", index=False)
    frontier.to_csv(output_dir / "delta_frontier.csv", index=False)
    if rates is not None and seed_mc is not None and aggregate_mc is not None:
        rates.to_csv(output_dir / "proxy_exact_rates.csv", index=False)
        seed_mc.to_csv(output_dir / "proxy_mc_by_seed.csv", index=False)
        aggregate_mc.to_csv(output_dir / "proxy_mc_aggregate.csv", index=False)
    _write_json(output_dir / "config_snapshot.json", {"contract": contract, stage_name: stage})
    _write_json(output_dir / "gates.json", gates)
    _write_json(output_dir / "summary.json", summary)
    _write_json(output_dir / "runtime.json", runtime)
    (output_dir / "REPORT.md").write_text(
        _report_markdown(stage_name, config_hash, gates, frontier, proxy, elapsed, stage, contract),
        encoding="utf-8",
    )
    return summary
