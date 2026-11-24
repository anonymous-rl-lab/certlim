#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if path == MANIFEST:
        return False
    excluded_parts = {"__pycache__", ".pytest_cache", ".venv", ".mplconfig", ".frozen", ".git", ".github"}
    if excluded_parts.intersection(relative.parts):
        return False
    if "data" in relative.parts and "raw" in relative.parts:
        return False
    if "downloads" in relative.parts and path.suffix == ".zip":
        return False
    if path.suffix in {".pyc", ".pyo"}:
        return False
    return path.is_file()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    lines = []
    for path in sorted(path for path in ROOT.rglob("*") if included(path)):
        lines.append(f"{sha256(path)}  {path.relative_to(ROOT).as_posix()}")
    MANIFEST.write_text("\n".join(lines) + "\n")
    print(f"wrote {len(lines)} entries to {MANIFEST.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
