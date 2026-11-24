#!/usr/bin/env python3
"""Maintainer-only builder for the canonical release manifest."""
import hashlib
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "raw"}
SKIP_FILES = {
    "MANIFEST.sha256",
    os.path.join("results", "runtime.json"),
    os.path.join("results", "environment.json"),
}


def tracked_files():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            relative = os.path.normpath(os.path.relpath(os.path.join(dirpath, filename), ROOT))
            if relative in SKIP_FILES or filename.endswith((".pyc", ".pyo")):
                continue
            files.append(relative)
    return sorted(files)


lines = []
for relative in tracked_files():
    with open(os.path.join(ROOT, relative), "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    lines.append(f"{digest}  {relative}")
with open(os.path.join(ROOT, "MANIFEST.sha256"), "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
print(f"release manifest: {len(lines)} files")
