#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "MANIFEST.sha256"


def included(path: Path) -> bool:
    return (
        path.is_file()
        and path != TARGET
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )


rows = [
    f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}"
    for path in sorted(ROOT.rglob("*"))
    if included(path)
]
TARGET.write_text("\n".join(rows) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} entries")
