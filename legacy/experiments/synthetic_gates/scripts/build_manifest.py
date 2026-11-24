from __future__ import annotations

import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.sha256"


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    return (
        path.is_file()
        and path != MANIFEST
        and "__pycache__" not in relative.parts
        and path.suffix != ".pyc"
    )


rows = []
for path in sorted(path for path in ROOT.rglob("*") if included(path)):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
MANIFEST.write_text("\n".join(rows) + "\n", encoding="utf-8")
print(f"wrote {MANIFEST} with {len(rows)} entries")
