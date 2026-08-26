#!/usr/bin/env python3
"""Write MANIFEST.sha256 over every tracked file except the manifest itself."""
import hashlib, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SKIP_DIRS = {".git", "__pycache__", "data/raw"}
lines = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    rel_dir = os.path.relpath(dirpath, ROOT)
    if any(rel_dir.startswith(s) for s in SKIP_DIRS):
        continue
    for fn in sorted(filenames):
        rel = os.path.normpath(os.path.join(rel_dir, fn))
        # results/runtime.csv carries wall-clock time and is expected to differ on rerun
        if rel in ("MANIFEST.sha256", os.path.join("results", "runtime.csv")):
            continue
        with open(os.path.join(dirpath, fn), "rb") as fh:
            lines.append(f"{hashlib.sha256(fh.read()).hexdigest()}  {rel}")
lines.sort(key=lambda l: l.split("  ", 1)[1])
with open(os.path.join(ROOT, "MANIFEST.sha256"), "w") as fh:
    fh.write("\n".join(lines) + "\n")
print(f"manifest: {len(lines)} files")
