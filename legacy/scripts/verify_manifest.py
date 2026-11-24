#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    failures = []
    for line in MANIFEST.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"MISSING {relative}")
        elif sha256(path) != expected:
            failures.append(f"MISMATCH {relative}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"PASS: verified {len(MANIFEST.read_text().splitlines())} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
