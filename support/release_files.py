"""Check release file membership as well as the contents of each listed file."""

from collections import Counter
import hashlib
import os
from pathlib import Path

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_files(root, *, working=False, runtime_paths=()):
    root = Path(root).resolve()
    rows = (root / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    parsed = [row.split("  ", 1) for row in rows]
    counts = Counter(name for _, name in parsed)
    if any(n != 1 for n in counts.values()):
        raise ValueError("Repeated path in release manifest")
    expected = {name: value for value, name in parsed}
    allowed = set()
    if working:
        allowed = {root / "raw", root / "replay_runs"}
        allowed.update(Path(p).resolve() for p in runtime_paths if p is not None)
        # An explicitly supplied working path cannot mask release files or the release root.
        allowed = {p for p in allowed if p.is_relative_to(root) and p != root
                   and not any((root / name).is_relative_to(p) for name in expected)}
    present = set()
    for directory, dirs, files in os.walk(root):
        parent = Path(directory)
        for name in dirs[:]:
            path = parent / name
            if (parent == root and name == ".git") or path in allowed:
                dirs.remove(name)
            elif path.is_symlink():
                raise ValueError(f"Unexpected directory symlink: {path.relative_to(root)}")
        for name in files:
            path = parent / name
            if (parent == root and name == ".git") or path in allowed:
                continue
            rel = path.relative_to(root).as_posix()
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Expected regular file: {rel}")
            if working and parent.name == "__pycache__" and path.suffix == ".pyc":
                continue
            present.add(rel)
    present.discard("SHA256SUMS")
    missing = sorted(expected.keys() - present)
    extra = sorted(present - expected.keys())
    if missing or extra:
        raise ValueError(f"Release file set differs. Missing: {missing}. Unlisted: {extra}")
    for rel, checksum in expected.items():
        if digest(root / rel) != checksum:
            raise ValueError(f"Release checksum mismatch: {rel}")
    return len(expected)
