from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d


FILE_RE = re.compile(
    r"(?P<cell>PJ\d{3})_(?P<block>\d{3})_(?P<number>\d{2})_"
    r"(?P<kind>GEIS|GCPL)_(?P<channel>C[A-B]\d)\.txt$"
)


class ExtractionError(RuntimeError):
    """A raw record failed an explicit validation check."""


@dataclass(frozen=True)
class CycleFiles:
    cell: str
    channel: str
    block: int
    step: int
    eis: Path
    charge: Path
    discharge: Path

    @property
    def cycle_index(self) -> int:
        return 1 + (self.block - 2) * 4 + self.step


def _read_tab(path: Path, required: tuple[str, ...]) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path, sep="\t")
    except Exception as exc:  # retain path and cause; never silently skip
        raise ExtractionError(f"cannot parse {path.name}: {exc}") from exc
    frame = frame.loc[:, ~frame.columns.str.startswith("Unnamed")]
    missing = [name for name in required if name not in frame.columns]
    if missing:
        raise ExtractionError(f"{path.name}: missing columns {missing}")
    if frame.empty:
        raise ExtractionError(f"{path.name}: empty table")
    return frame


def _positive_segments(current: np.ndarray, tol: float = 1e-6) -> list[np.ndarray]:
    indices = np.flatnonzero(current > tol)
    if indices.size == 0:
        return []
    cuts = np.flatnonzero(np.diff(indices) > 1) + 1
    return [segment for segment in np.split(indices, cuts) if segment.size >= 5]


def extract_eis(path: Path, log_frequency: np.ndarray) -> dict[str, object]:
    frame = _read_tab(path, ("freq/Hz", "Re(Z)/Ohm", "-Im(Z)/Ohm", "time/s"))
    data = frame.loc[:, ["freq/Hz", "Re(Z)/Ohm", "-Im(Z)/Ohm", "time/s"]].apply(
        pd.to_numeric, errors="coerce"
    )
    data = data.dropna().drop_duplicates(subset="freq/Hz")
    data = data[data["freq/Hz"] > 0].sort_values("freq/Hz")
    if len(data) < 40:
        raise ExtractionError(f"{path.name}: only {len(data)} valid EIS rows")
    log_f = np.log10(data["freq/Hz"].to_numpy(float))
    if log_f.min() > log_frequency.min() or log_f.max() < log_frequency.max():
        raise ExtractionError(
            f"{path.name}: frequency support [{log_f.min():.3f}, {log_f.max():.3f}] "
            f"does not cover [{log_frequency.min():.3f}, {log_frequency.max():.3f}]"
        )
    # Match the authors' released extractor: cubic interpolation on log-frequency.
    re_z = interp1d(log_f, data["Re(Z)/Ohm"].to_numpy(float), kind="cubic")(
        log_frequency
    )
    neg_im_z = interp1d(log_f, data["-Im(Z)/Ohm"].to_numpy(float), kind="cubic")(
        log_frequency
    )
    time = data["time/s"].to_numpy(float)
    return {
        "eis_rows": int(len(data)),
        "eis_min_hz": float(data["freq/Hz"].min()),
        "eis_max_hz": float(data["freq/Hz"].max()),
        "eis_start_s": float(np.nanmin(time)),
        "eis_end_s": float(np.nanmax(time)),
        "eis_duration_s": float(np.nanmax(time) - np.nanmin(time)),
        "eis_re": re_z,
        "eis_neg_im": neg_im_z,
    }


def extract_charge(path: Path) -> dict[str, float]:
    frame = _read_tab(
        path, ("time/s", "Ecell/V", "<I>/mA", "Capacity/mA.h", "ox/red")
    )
    data = frame.loc[:, ["time/s", "Ecell/V", "<I>/mA", "Capacity/mA.h", "ox/red"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()
    current = data["<I>/mA"].to_numpy(float)
    segments = _positive_segments(current)
    if len(segments) != 2:
        raise ExtractionError(
            f"{path.name}: expected two positive-current stages, found {len(segments)}"
        )
    first, second = segments
    time = data["time/s"].to_numpy(float)
    capacity = data["Capacity/mA.h"].to_numpy(float)
    voltage = data["Ecell/V"].to_numpy(float)
    positive = current > 1e-6
    return {
        "charge_start_s": float(time.min()),
        "charge_end_s": float(time.max()),
        "charge_duration_h": float((time[positive].max() - time[positive].min()) / 3600),
        "charge_stage1_ma": float(np.mean(current[first])),
        "charge_stage2_ma": float(np.mean(current[second])),
        "charge_stage1_h": float((time[first].max() - time[first].min()) / 3600),
        "charge_stage2_h": float((time[second].max() - time[second].min()) / 3600),
        "charge_capacity_mah": float(np.nanmax(capacity[positive])),
        "ocv_v": float(np.nanmean(voltage[:5])),
        "charge_vmax_v": float(np.nanmax(voltage)),
    }


def extract_discharge(path: Path) -> dict[str, float]:
    frame = _read_tab(
        path, ("time/s", "Ecell/V", "<I>/mA", "Capacity/mA.h", "ox/red")
    )
    data = frame.loc[:, ["time/s", "Ecell/V", "<I>/mA", "Capacity/mA.h", "ox/red"]].apply(
        pd.to_numeric, errors="coerce"
    ).dropna()
    mask = (data["<I>/mA"] < -1e-6) & (data["ox/red"] == 0)
    discharge = data.loc[mask]
    if len(discharge) < 10:
        raise ExtractionError(f"{path.name}: only {len(discharge)} discharge rows")
    current = discharge["<I>/mA"].to_numpy(float)
    capacity = discharge["Capacity/mA.h"].to_numpy(float)
    return {
        "discharge_start_s": float(data["time/s"].min()),
        "discharge_end_s": float(data["time/s"].max()),
        "discharge_capacity_mah": float(np.nanmax(capacity)),
        "discharge_current_ma": float(-np.nanmedian(current)),
        "discharge_vmin_v": float(np.nanmin(discharge["Ecell/V"])),
    }


def enumerate_cycles(cell_dir: Path) -> tuple[list[CycleFiles], list[dict[str, object]]]:
    candidates: list[CycleFiles] = []
    structural_errors: list[dict[str, object]] = []
    for eis in sorted(cell_dir.glob("*_GEIS_*.txt")):
        match = FILE_RE.match(eis.name)
        if not match:
            continue
        block = int(match.group("block"))
        number = int(match.group("number"))
        if block < 2 or number % 4 != 1:
            continue
        cell = match.group("cell")
        channel = match.group("channel")
        charge = cell_dir / f"{cell}_{block:03d}_{number + 1:02d}_GCPL_{channel}.txt"
        discharge = cell_dir / f"{cell}_{block:03d}_{number + 3:02d}_GCPL_{channel}.txt"
        missing = [p.name for p in (charge, discharge) if not p.exists()]
        if missing:
            structural_errors.append(
                {
                    "cell": cell,
                    "block": block,
                    "step": (number - 1) // 4,
                    "stage": "pairing",
                    "error": f"missing paired files: {missing}",
                }
            )
            continue
        candidates.append(
            CycleFiles(
                cell=cell,
                channel=channel,
                block=block,
                step=(number - 1) // 4,
                eis=eis,
                charge=charge,
                discharge=discharge,
            )
        )
    return candidates, structural_errors


def initial_capacity(cell_dir: Path) -> float:
    files = sorted(cell_dir.glob("*_000_02_GCPL_*.txt"))
    if len(files) != 1:
        raise ExtractionError(
            f"{cell_dir.name}: expected one initial capacity file, found {len(files)}"
        )
    return extract_discharge(files[0])["discharge_capacity_mah"]


def extract_dataset(
    raw_root: Path, n_frequency: int = 100
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    log_frequency = np.linspace(-1.66, 3.9, n_frequency)
    records: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    expected = 0

    cell_dirs = sorted(p for p in raw_root.glob("PJ*" ) if p.is_dir())
    for cell_dir in cell_dirs:
        try:
            cap0 = initial_capacity(cell_dir)
        except ExtractionError as exc:
            errors.append({"cell": cell_dir.name, "stage": "initial_capacity", "error": str(exc)})
            continue
        cycle_files, structural_errors = enumerate_cycles(cell_dir)
        expected += len(cycle_files) + len(structural_errors)
        errors.extend(structural_errors)
        previous_capacity = cap0
        cumulative_throughput = 0.0
        for item in cycle_files:
            try:
                eis = extract_eis(item.eis, log_frequency)
                charge = extract_charge(item.charge)
                discharge = extract_discharge(item.discharge)
                chronology = bool(
                    eis["eis_end_s"] <= charge["charge_start_s"]
                    and charge["charge_end_s"] <= discharge["discharge_start_s"]
                )
                row: dict[str, object] = {
                    "cell": item.cell,
                    "channel": item.channel,
                    "block": item.block,
                    "step": item.step,
                    "cycle": item.cycle_index,
                    "initial_capacity_mah": cap0,
                    "previous_capacity_mah": previous_capacity,
                    "previous_soh": previous_capacity / cap0,
                    "cumulative_throughput_mah": cumulative_throughput,
                    "chronology_ok": chronology,
                    "eis_file": item.eis.name,
                    "charge_file": item.charge.name,
                    "discharge_file": item.discharge.name,
                }
                row.update({k: v for k, v in eis.items() if k not in ("eis_re", "eis_neg_im")})
                row.update(charge)
                row.update(discharge)
                row["soh"] = discharge["discharge_capacity_mah"] / cap0
                for index, value in enumerate(eis["eis_re"]):
                    row[f"eis_re_{index:03d}"] = float(value)
                for index, value in enumerate(eis["eis_neg_im"]):
                    row[f"eis_neg_im_{index:03d}"] = float(value)
                records.append(row)
                previous_capacity = discharge["discharge_capacity_mah"]
                cumulative_throughput += charge["charge_capacity_mah"] + discharge["discharge_capacity_mah"]
            except ExtractionError as exc:
                errors.append(
                    {
                        "cell": item.cell,
                        "block": item.block,
                        "step": item.step,
                        "cycle": item.cycle_index,
                        "stage": "content",
                        "error": str(exc),
                    }
                )

    frame = pd.DataFrame.from_records(records).sort_values(["cell", "cycle"]).reset_index(drop=True)
    error_frame = pd.DataFrame.from_records(errors)
    metadata = {
        "n_cells_discovered": len(cell_dirs),
        "n_expected_cycles": expected,
        "n_complete_cycles": len(frame),
        "n_errors": len(error_frame),
        "n_frequency": n_frequency,
        "log10_frequency_grid": [float(log_frequency.min()), float(log_frequency.max())],
    }
    return frame, error_frame, metadata
