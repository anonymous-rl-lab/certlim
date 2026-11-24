from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from causal_certification.runner import run_stage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run preregistered v04 theory gates")
    parser.add_argument("stage", choices=("smoke", "small"))
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "gates.json")
    parser.add_argument("--output-root", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    summary = run_stage(args.config, args.stage, args.output_root)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["all_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
