#!/usr/bin/env python3
import hashlib, os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
bad = missing = 0
listed = set()
for line in open(os.path.join(ROOT, "MANIFEST.sha256")):
    digest, rel = line.rstrip("\n").split("  ", 1)
    listed.add(rel)
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        print(f"MISSING  {rel}"); missing += 1; continue
    with open(p, "rb") as fh:
        if hashlib.sha256(fh.read()).hexdigest() != digest:
            print(f"MISMATCH {rel}"); bad += 1
print(f"verified {len(listed)} entries: {bad} mismatched, {missing} missing")
sys.exit(1 if (bad or missing) else 0)
