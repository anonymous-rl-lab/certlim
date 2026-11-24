"""Materialize the v25 projection from the historical Parquet, checking both byte hashes."""
import gzip
import hashlib
import io
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "paper_v25/evidence/NASA_chain_v2"
TARGET = BASE / "data/nasa_steps.csv.gz"
COLUMNS = "cell arm temp stage step_k I_med V0 Vend Tmax dur_s".split()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def restore(target=TARGET):
    import pandas as pd

    provenance = json.loads((BASE / "INPUT_PROVENANCE.json").read_text())
    source = ROOT / "legacy/experiments/nasa_randomized_usage_gate/data/steps.parquet"
    if digest(source) != provenance["original_steps_parquet_sha256"]:
        raise ValueError("Original NASA Parquet checksum mismatch")
    expected = provenance["included_steps_csv_gz_sha256"]
    if target.exists():
        if digest(target) != expected:
            raise ValueError(f"Existing file differs from v25: {target}")
        return target
    try:
        frame = pd.read_parquet(source, columns=COLUMNS, engine="pyarrow")
    except ImportError:
        from parquet_snappy import read
        frame = read(source, COLUMNS)[COLUMNS]
    if len(frame) != provenance["rows"]:
        raise ValueError("NASA source row count mismatch")

    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as raw:
        temporary = Path(raw.name)
    try:
        with temporary.open("wb") as out:
            with gzip.GzipFile("nasa_steps.csv", mode="wb", fileobj=out, mtime=0, compresslevel=9) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as csv:
                    frame.to_csv(csv, index=False, lineterminator="\n")
        if digest(temporary) != expected:
            raise ValueError("Rebuilt CSV.GZ differs from the published v25 hash")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


if __name__ == "__main__":
    print(restore())
