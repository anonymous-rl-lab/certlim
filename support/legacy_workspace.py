"""Recreate the byte-exact v0.7.0 release in a separate writable directory."""

import hashlib
import os
from pathlib import Path
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "support/legacy_files"


def materialize(destination):
    destination = Path(destination).resolve()
    if destination.exists() or destination.is_relative_to(ROOT):
        raise ValueError("Choose a new legacy workspace outside the release tree")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as stage:
        work = Path(stage) / "legacy"
        for entry in (STORE / "SHA256SUMS").read_text().splitlines():
            expected, name = entry.split("  ", 1)
            out = work / name
            out.parent.mkdir(parents=True, exist_ok=True)
            source = ROOT / "legacy" / name.removeprefix(".frozen/")
            if name == "reproduce.py":
                source = STORE / "reproduce_0_7_0.py"
            shutil.copy2(source, out)
            with out.open("rb") as contents:
                if hashlib.file_digest(contents, "sha256").hexdigest() != expected:
                    raise ValueError(f"Historical source checksum mismatch: {name}")
        if os.path.lexists(destination):
            raise FileExistsError(destination)
        work.rename(destination)
    return destination
