"""Minimal, chronology-aware extraction from the official MATLAB v7.3 files."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

try:
    import h5py
except ModuleNotFoundError:  # Lightweight result review does not read raw MAT files.
    h5py = None

from .registry import (
    BAD_BATCH1_IDS,
    BAD_BATCH3_IDS,
    CONTINUATION_BATCH2_IDS,
    CONTINUATION_LIFE_ADD,
    SCALAR_CHANNELS,
    SPLIT_BY_ID,
    STAT_NAMES,
)


def _deref_vector(handle: h5py.File, dataset: h5py.Dataset) -> np.ndarray:
    values = np.asarray(dataset)
    if h5py.check_dtype(ref=values.dtype) is None:
        return values.ravel(order="C").astype(float)
    refs = values.ravel(order="F")
    pieces = [np.asarray(handle[ref]).ravel(order="F") for ref in refs]
    return np.hstack(pieces).astype(float) if pieces else np.array([], dtype=float)


def _decode_matlab_chars(handle: h5py.File, ref) -> str:
    values = np.asarray(handle[ref]).ravel(order="F")
    return "".join(chr(int(value)) for value in values if int(value) != 0)


def parse_policy(policy: str) -> tuple[float, float, float]:
    match = re.search(
        r"([0-9.]+)C\(([0-9.]+)%\)-([0-9.]+)C?", policy.replace(" ", "")
    )
    if not match:
        raise ValueError(f"Unrecognized charging policy: {policy!r}")
    c1, switch_pct, c2 = map(float, match.groups())
    return c1, switch_pct / 100.0, c2


def summarize_window(cycles: np.ndarray, values: np.ndarray, stop: int) -> dict[str, float]:
    cycles = np.asarray(cycles, dtype=float)
    values = np.asarray(values, dtype=float)
    keep = (cycles >= 2) & (cycles <= stop) & np.isfinite(cycles) & np.isfinite(values)
    x = cycles[keep]
    y = values[keep]
    if not len(y):
        return {name: np.nan for name in STAT_NAMES}
    slope = np.polyfit(x, y, 1)[0] if len(y) >= 2 and np.ptp(x) > 0 else 0.0
    return {
        "start": float(y[0]),
        "end": float(y[-1]),
        "mean": float(np.mean(y)),
        "std": float(np.std(y)),
        "slope": float(slope),
        "min": float(np.min(y)),
        "max": float(np.max(y)),
        "delta": float(y[-1] - y[0]),
    }


def curve_features(delta_q: np.ndarray) -> dict[str, float]:
    delta_q = np.asarray(delta_q, dtype=float)
    delta_q = delta_q[np.isfinite(delta_q)]
    if len(delta_q) < 2:
        return {"log_abs_min": np.nan, "log_var": np.nan}
    eps = 1e-12
    return {
        "log_abs_min": float(np.log10(abs(np.min(delta_q)) + eps)),
        "log_var": float(np.log10(abs(np.var(delta_q, ddof=1)) + eps)),
    }


def _physical_cycle_indices(summary_cycles: np.ndarray) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for index, value in enumerate(np.asarray(summary_cycles).ravel()):
        if np.isfinite(value) and abs(value - round(value)) < 1e-6:
            mapping[int(round(value))] = index
    return mapping


def extract_batch(path: Path, batch_number: int, smoke_limit: int | None = None):
    if h5py is None:
        raise ModuleNotFoundError(
            "h5py is required only for rebuilding features from raw MATR files; "
            "install the experiment requirements before extraction"
        )
    records: list[dict[str, float | str]] = []
    audits: list[dict[str, object]] = []
    with h5py.File(path, "r") as handle:
        batch = handle["batch"]
        n_cells = int(batch["summary"].shape[0])
        for cell_index in range(n_cells):
            cell_id = f"b{batch_number}c{cell_index}"
            if batch_number == 1 and cell_id in BAD_BATCH1_IDS:
                continue
            if batch_number == 2 and cell_id in CONTINUATION_BATCH2_IDS:
                continue
            if batch_number == 3 and cell_id in BAD_BATCH3_IDS:
                continue
            if cell_id not in SPLIT_BY_ID:
                continue
            if smoke_limit is not None and sum(r["split"] == SPLIT_BY_ID[cell_id] for r in records) >= smoke_limit:
                continue

            life = float(np.asarray(handle[batch["cycle_life"][cell_index, 0]]).ravel()[0])
            life += CONTINUATION_LIFE_ADD.get(cell_id, 0)
            policy = _decode_matlab_chars(handle, batch["policy_readable"][cell_index, 0])
            c1, switch_soc, c2 = parse_policy(policy)

            summary_group = handle[batch["summary"][cell_index, 0]]
            summary = {
                channel: _deref_vector(handle, summary_group[channel])
                for channel in SCALAR_CHANNELS
            }
            summary_cycles = _deref_vector(handle, summary_group["cycle"])
            shortest = min([len(summary_cycles)] + [len(v) for v in summary.values()])
            summary_cycles = summary_cycles[:shortest]
            summary = {key: value[:shortest] for key, value in summary.items()}

            row: dict[str, float | str] = {
                "cell_id": cell_id,
                "split": SPLIT_BY_ID[cell_id],
                "batch": batch_number,
                "cycle_life": life,
                "policy_raw": policy,
                "protocol_c1": c1,
                "protocol_switch_soc": switch_soc,
                "protocol_c2": c2,
            }
            for horizon in (5, 100):
                for channel, values in summary.items():
                    for stat, value in summarize_window(summary_cycles, values, horizon).items():
                        row[f"s{horizon}_{channel}_{stat}"] = value

            cycles_group = handle[batch["cycles"][cell_index, 0]]
            qdlin_refs = cycles_group["Qdlin"]
            cycle_map = _physical_cycle_indices(summary_cycles)

            def qdlin_at(physical_cycle: int) -> np.ndarray:
                if physical_cycle not in cycle_map:
                    raise KeyError(
                        f"{cell_id}: physical cycle {physical_cycle} absent; "
                        f"available range={summary_cycles[:3]}...{summary_cycles[-3:]}"
                    )
                index = cycle_map[physical_cycle]
                if index >= qdlin_refs.shape[0]:
                    raise IndexError(
                        f"{cell_id}: summary index {index} exceeds Qdlin rows {qdlin_refs.shape[0]}"
                    )
                return np.asarray(handle[qdlin_refs[index, 0]]).ravel(order="F").astype(float)

            q4, q5 = qdlin_at(4), qdlin_at(5)
            q10, q100 = qdlin_at(10), qdlin_at(100)
            for name, values in (("curve5", q5 - q4), ("curve100", q100 - q10)):
                for stat, value in curve_features(values).items():
                    row[f"{name}_{stat}"] = value

            records.append(row)
            audits.append({
                "cell_id": cell_id,
                "split": SPLIT_BY_ID[cell_id],
                "raw_summary_length": int(len(summary_cycles)),
                "cycle_min": float(np.nanmin(summary_cycles)),
                "cycle_max": float(np.nanmax(summary_cycles)),
                "q4_points": int(len(q4)),
                "q5_points": int(len(q5)),
                "q10_points": int(len(q10)),
                "q100_points": int(len(q100)),
            })
    return records, audits
