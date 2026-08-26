#!/usr/bin/env python3
"""Verify hashes, missing files, and unregistered extras."""
import hashlib
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SKIP_DIRS = {".git", ".pytest_cache", "__pycache__", "raw"}
SKIP_FILES = {
    "MANIFEST.sha256",
    os.path.join("results", "runtime.json"),
    os.path.join("results", "environment.json"),
}


def actual_files():
    files = set()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in filenames:
            relative = os.path.normpath(os.path.relpath(os.path.join(dirpath, filename), ROOT))
            if relative in SKIP_FILES or filename.endswith((".pyc", ".pyo")):
                continue
            files.add(relative)
    return files


expected = {}
with open(os.path.join(ROOT, "MANIFEST.sha256"), encoding="utf-8") as handle:
    for line in handle:
        digest, relative = line.rstrip("\n").split("  ", 1)
        expected[relative] = digest

bad = 0
for relative, digest in sorted(expected.items()):
    path = os.path.join(ROOT, relative)
    if not os.path.exists(path):
        print(f"MISSING  {relative}")
        bad += 1
        continue
    with open(path, "rb") as handle:
        observed = hashlib.sha256(handle.read()).hexdigest()
    if observed != digest:
        print(f"MISMATCH {relative}")
        bad += 1

extras = sorted(actual_files() - set(expected))
for relative in extras:
    print(f"UNLISTED {relative}")
    bad += 1
print(f"verified {len(expected)} entries; extras={len(extras)}; problems={bad}")
sys.exit(1 if bad else 0)
