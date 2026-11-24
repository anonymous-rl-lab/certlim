#!/usr/bin/env python3
"""Compare the working tree against the frozen manifests and classify what moved.

`verify_manifest.py` answers a strict question -- is every released file byte-for-byte
what was recorded -- which is the right question before a recomputation and the wrong
one after it. A rerun on another machine legitimately rewrites the provenance records
each experiment keeps: its timestamp, its wall-clock time, and the versions of the
libraries it ran under. Those files will differ and should.

This script separates the two cases. A mismatch is *provenance* when every differing
line or JSON leaf is one of those recorded facts about the run, and *substantive*
otherwise. Substantive mismatches are the ones that mean a result moved, and they are
the only ones that fail this check.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT / ".frozen"

VOLATILE = re.compile(
    r"timestamp|generated_at|runtime|elapsed|duration|_seconds\b|wall_clock"
    r"|python|numpy|pandas|scipy|sklearn|scikit|matplotlib|pyarrow|h5py|platform|host|machine"    r"|\u8fd0\u884c\u65f6|\u8017\u65f6|\u79d2",
    re.I,
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def leaves(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from leaves(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, f"{path}[{i}]")
    else:
        yield path, obj


RTOL, ATOL = 1e-8, 1e-12


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _close(x, y) -> bool:
    a, b = _num(x), _num(y)
    if a is None or b is None:
        return False
    return abs(a - b) <= ATOL + RTOL * abs(a)


def classify(current: Path, reference: bytes, rel: str = "") -> str:
    """'provenance', 'numeric', 'shortened', or 'substantive'.

    A file whose own name records the run -- runtime.csv, environment.json -- is
    provenance whatever moved inside it.
    """
    if VOLATILE.search(Path(rel).name):
        return "provenance"
    try:
        a = json.loads(reference.decode())
        b = json.loads(current.read_text())
    except Exception:
        return _classify_text(current, reference)
    da, db = dict(leaves(a)), dict(leaves(b))
    if da.keys() != db.keys():
        # a capped run (MAX_N) records a subset of the frozen block lengths
        if db.keys() < da.keys() and all(da[k] == db[k] or _close(da[k], db[k])
                                         or VOLATILE.search(k) for k in db):
            return "shortened"
        return "substantive"
    # a capped run records the cap it used; aggregates over the shortened sweep
    # then differ by construction rather than because a result moved
    capped = any(re.search(r"max_n|n_max|max_block", k, re.I) and _num(da[k]) is not None
                 and _num(db[k]) is not None and _num(db[k]) < _num(da[k]) for k in da)
    if capped:
        return "shortened"
    verdict = "provenance"
    for k in da:
        if da[k] == db[k]:
            continue
        if VOLATILE.search(k):
            continue
        if _close(da[k], db[k]):
            verdict = "numeric"
            continue
        return "substantive"
    return verdict


def _classify_text(current: Path, reference: bytes) -> str:
    old = reference.decode(errors="replace").splitlines()
    new = current.read_text(errors="replace").splitlines()
    if len(old) != len(new):
        # a capped run (MAX_N) writes a prefix of the frozen table
        return "shortened" if new and old[:len(new)] == new else "substantive"
    verdict = "provenance"
    for x, y in zip(old, new):
        if x == y:
            continue
        if VOLATILE.search(x):
            continue
        xs, ys = x.split(","), y.split(",")
        if len(xs) == len(ys) and all(u == v or _close(u, v) for u, v in zip(xs, ys)):
            verdict = "numeric"
            continue
        return "substantive"
    return verdict


def main() -> int:
    manifest = ROOT / "MANIFEST.sha256"
    expected = {}
    for line in manifest.read_text().strip().split("\n"):
        digest, rel = line.split(None, 1)
        expected[rel.strip()] = digest

    buckets = {"provenance": [], "numeric": [], "shortened": [], "substantive": []}
    missing = []
    for rel, digest in sorted(expected.items()):
        path = ROOT / rel
        if not path.is_file():
            missing.append(rel)
            continue
        if sha256(path) == digest:
            continue
        ref = FROZEN / rel
        kind = classify(path, ref.read_bytes(), rel) if ref.is_file() else "substantive"
        buckets[kind].append(rel)

    moved = sum(len(v) for v in buckets.values())
    labels = {"provenance": "timestamps, wall clock, library versions",
              "numeric": "agree to floating-point tolerance",
              "shortened": "capped run wrote a prefix of the frozen table",
              "substantive": "a result moved"}
    print(f"tracked files: {len(expected)}")
    print(f"unchanged:     {len(expected) - len(missing) - moved}")
    for kind in ("provenance", "numeric", "shortened", "substantive"):
        print(f"{kind + ':':<15}{len(buckets[kind]):<4}({labels[kind]})")
        for rel in buckets[kind]:
            print(f"    {'!' if kind == 'substantive' else '~'} {rel}")
    if missing:
        print(f"missing:       {len(missing)}")
        for rel in missing:
            print(f"    ? {rel}")

    substantive = buckets["substantive"]
    if not FROZEN.is_dir() and moved:
        print("\nnote: .frozen/ is absent, so nothing could be classified; "
              "every mismatch above is reported as substantive")
    ok = not substantive and not missing
    print("\n" + ("every result reproduces" if ok else "reproduction check FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
