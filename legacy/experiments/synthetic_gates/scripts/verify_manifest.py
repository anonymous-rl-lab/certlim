from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"
failures = []
for line in MANIFEST.read_text(encoding="utf-8").splitlines():
    expected, relative = line.split("  ", 1)
    path = ROOT / relative
    if not path.is_file():
        failures.append(f"missing: {relative}")
        continue
    observed = hashlib.sha256(path.read_bytes()).hexdigest()
    if observed != expected:
        failures.append(f"changed: {relative}")
if failures:
    raise SystemExit("\n".join(failures))
print("manifest verified")
