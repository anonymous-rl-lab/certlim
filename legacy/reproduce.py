#!/usr/bin/env python3
"""Compatibility entry point for the historical v0.7.0 experiments."""

from pathlib import Path
import os
import subprocess
import sys
import tempfile

if __name__ == "__main__":
    sys.dont_write_bytecode = True
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "support"))
    from legacy_workspace import materialize

    # Quick verification is ephemeral. Retain recomputations for inspection.
    quick = "--list" in sys.argv or not any(arg in ("core", "full", "--tier=core", "--tier=full") for arg in sys.argv[1:])
    with tempfile.TemporaryDirectory() as transient:
        parent = Path(transient) if quick else Path(tempfile.mkdtemp(prefix="certlim-legacy-"))
        workspace = materialize(parent / "legacy")
        print(f"Historical v0.7.0 workspace: {workspace}", flush=True)
        env = dict(os.environ, PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH",""))
        result = subprocess.run([sys.executable, str(workspace / "reproduce.py"), *sys.argv[1:]],
                                cwd=workspace, env=env)
        raise SystemExit(result.returncode)
