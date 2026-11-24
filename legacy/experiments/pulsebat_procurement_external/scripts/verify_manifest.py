#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
failures = []
lines = (ROOT / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
for line in lines:
    expected, relative = line.split("  ", 1)
    path = ROOT / relative
    actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "MISSING"
    if actual != expected:
        failures.append(relative)
if failures:
    print("FAIL", failures)
    raise SystemExit(1)
print(f"PASS: {len(lines)}/{len(lines)}")

