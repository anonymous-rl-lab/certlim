#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "MANIFEST.sha256"

lines = []
for path in sorted(ROOT.rglob("*")):
    if path.is_file() and path != TARGET and "__pycache__" not in path.parts:
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT).as_posix()}")
TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {len(lines)} entries")

