#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
lines = (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
for line in lines:
    expected, relative = line.split("  ", 1)
    path = ROOT / relative
    if not path.is_file():
        raise SystemExit(f"MISSING: {relative}")
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != expected:
        raise SystemExit(f"MISMATCH: {relative}")
print(f"PASS: {len(lines)}/{len(lines)}")
