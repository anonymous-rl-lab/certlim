#!/usr/bin/env python3
"""Verify the merged v25 release or replay its three capacity experiments from public inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "support"))
from release_files import verify_files
PAPER = ROOT / "paper_v25"
DATA = PAPER / "evidence"
SCRIPTS = PAPER / "scripts"
TARGETS = ("cetl", "relib", "leaf")


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify(*, working=False, runtime_paths=()):
    file_count = verify_files(ROOT, working=working, runtime_paths=runtime_paths)
    sys.path.insert(0, str(SCRIPTS))
    from check_paper import MAIN, SI, check_tables, check_v22
    from check_capacity import check as capacity
    from check_leaf import check as leaf
    check_tables()
    check_v22()
    capacity(MAIN, SI)
    leaf(MAIN, SI)
    print(f"Verified {file_count} release files, v25 numerical tables and capacity ledgers.", flush=True)


def run(script, *args, log):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    env.pop("PYTHONOPTIMIZE", None)
    print(f"Running {script.parent.name}/{script.name} {' '.join(map(str, args[:1]))}", flush=True)
    with log.open("a", encoding="utf-8") as output:
        result = subprocess.run([sys.executable, str(script), *map(str, args)], stdout=output,
                                stderr=subprocess.STDOUT, env=env)
    if result.returncode:
        raise RuntimeError(f"{script.name} exited with {result.returncode}. See {log}")


def compare(expected, actual, report):
    names = sorted(p.name for p in expected.iterdir() if p.is_file())
    if names != sorted(p.name for p in actual.iterdir() if p.is_file()):
        raise ValueError(f"Different output filenames: {actual}")
    for name in names:
        original = sha256(expected / name)
        rebuilt = sha256(actual / name)
        if original != rebuilt:
            raise ValueError(f"Byte mismatch: {actual / name}")
        report[str((expected / name).relative_to(DATA))] = rebuilt
    print(f"Matched {len(names)} files byte for byte: {expected.relative_to(DATA)}", flush=True)


def check_input(path, expected):
    if path is None:
        raise ValueError("Missing a required public input. Run raw --help for paths.")
    path = path.resolve()
    if sha256(path) != expected:
        raise ValueError(f"Source checksum differs from the frozen input: {path}")
    return path


def raw(args):
    verify(working=True, runtime_paths=(args.cetl_mat, args.relib_tar, args.leaf_zip, args.work_dir))
    selected = set(TARGETS if args.dataset == "all" else [args.dataset])
    mat = tar = leaf_zip = None
    if selected & {"cetl", "relib"}:
        lock = json.loads((DATA / "ReLiB/lock.json").read_text())
        mat = check_input(args.cetl_mat, lock["original_mat_sha256"])
    if "relib" in selected:
        lock = json.loads((DATA / "ReLiB/public_results/blind_lock.json").read_text())
        tar = check_input(args.relib_tar, lock["tar_sha256"])
    if "leaf" in selected:
        leaf_zip = check_input(args.leaf_zip, "a4952be5b9d960c57b208a523b90ef9923f65ee92767b46b6b1b88560a62c98c")
    args.work_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="v25-", dir=args.work_dir.resolve()))
    print(f"Replay workspace: {work}", flush=True)
    matched = {}
    ignored = shutil.ignore_patterns("results", "public_results", "public_census", "__pycache__")
    predictions = DATA / "CETL/results/predictions.csv"
    if selected & {"cetl", "relib"}:
        relib = work / "ReLiB"
        shutil.copytree(DATA / "ReLiB", relib, ignore=ignored)
    if "cetl" in selected:
        cetl = work / "CETL"
        shutil.copytree(DATA / "CETL", cetl, ignore=ignored)
        for name in ("run_pulsefree.py", "audit.py", "posthoc_two_fields.py"):
            run(cetl / name, mat, log=work / "cetl.log")
        compare(DATA / "CETL/results", cetl / "results", matched)
        predictions = cetl / "results/predictions.csv"
        run(relib / "verify_freeze.py", mat, log=work / "cetl.log")
    if "relib" in selected:
        (relib / "historical_signatures.txt").unlink()
        run(relib / "replay.py", "signature", mat, log=work / "relib.log")
        if sha256(relib / "historical_signatures.txt") != sha256(DATA / "ReLiB/historical_signatures.txt"):
            raise ValueError("Rebuilt ReLiB trace signatures differ")
        for name, mode in (("public_results", "score"), ("public_census", "census-score")):
            output = relib / name
            for stage in (mode, "adjudicate"):
                run(relib / "replay.py", stage, tar, "--out", output, log=work / "relib.log")
            if mode == "score":
                run(relib / "check_readings.py", mat, predictions, tar, "--out", output, log=work / "relib.log")
            compare(DATA / "ReLiB" / name, output, matched)
    if "leaf" in selected:
        leaf = DATA / "Leaf"
        output = work / "leaf_results"
        for stage in ("score", "adjudicate"):
            run(leaf / "replay.py", stage, leaf_zip, output, log=work / "leaf.log")
        run(leaf / "check.py", leaf_zip, output, log=work / "leaf.log")
        run(leaf / "compare.py", output, log=work / "leaf.log")
        compare(leaf / "results", output, matched)
    result = {"datasets": sorted(selected), "matched_result_files": len(matched), "sha256": matched}
    (work / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"Passed. {len(matched)} regenerated files matched. Report: {work / 'verification.json'}")


def nasa(args):
    from restore_nasa import restore

    verify(working=True, runtime_paths=(args.work_dir,))
    args.work_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="nasa-v25-", dir=args.work_dir.resolve()))
    print(f"NASA replay workspace: {work}", flush=True)
    layers = ("NASA_chain_v2", "review_v21", "decision_v22")
    for layer in layers:
        shutil.copytree(DATA / layer, work / layer,
                        ignore=shutil.ignore_patterns("results", "__pycache__", "nasa_steps.csv.gz"))
        (work / layer / "results").mkdir()
    (work / layers[0] / "results/fixed60").mkdir()
    restore(work / layers[0] / "data/nasa_steps.csv.gz")
    log = work / "nasa.log"
    for layer, script in ((layers[0], "reproduce.py"), (layers[1], "run.py"),
                          (layers[1], "verify.py"), (layers[2], "run_audit.py")):
        run(work / layer / script, log=log)
    matched = {}
    for layer in layers:
        expected = DATA / layer / "results"
        actual = work / layer / "results"
        names = {f.relative_to(expected) for f in expected.rglob("*") if f.is_file()}
        if names != {f.relative_to(actual) for f in actual.rglob("*") if f.is_file()}:
            raise ValueError(f"NASA result file set differs in {layer}")
        for name in sorted(names):
            checksum = sha256(actual / name)
            if checksum != sha256(expected / name):
                raise ValueError(f"NASA result differs: {layer}/{name}")
            matched[f"{layer}/results/{name.as_posix()}"] = checksum
        print(f"{layer}: {len(names)} files match byte for byte", flush=True)
    (work / "verification.json").write_text(json.dumps(matched, indent=2) + "\n")


def main():
    if not __debug__:
        raise RuntimeError("Run with ordinary Python so scientific assertions are enabled.")
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode")
    quick = modes.add_parser("verify", help="check the complete release file set and paper tables (default)")
    quick.add_argument("--working", action="store_true",
                       help="allow documented working outputs and bytecode caches")
    modes.add_parser("verify-tool", help="compare the installed certlim 0.2.1 with v25 evidence")
    n = modes.add_parser("nasa", help="rebuild and compare all three NASA result layers in a fresh workspace")
    n.add_argument("--work-dir", type=Path, default=Path("replay_runs"))
    legacy = modes.add_parser("legacy-workspace", help="export the original 592-file historical snapshot")
    legacy.add_argument("destination", type=Path, help="a new directory outside this release")
    replay = modes.add_parser("raw", help="from public inputs, blind actions through adjudication")
    replay.add_argument("--dataset", choices=("all", *TARGETS), default="all")
    replay.add_argument("--cetl-mat", type=Path, help="CETL and ReLiB independent audit")
    replay.add_argument("--relib-tar", type=Path, help="ReLiB uncompressed 15.5 Ah TAR")
    replay.add_argument("--leaf-zip", type=Path, help="Leaf C/20 workbook ZIP")
    replay.add_argument("--work-dir", type=Path, default=Path("replay_runs"))
    modes.add_parser("prepare-nasa", help="recreate the second NASA representation offline")
    args = parser.parse_args()
    if args.mode == "raw":
        raw(args)
    elif args.mode == "nasa":
        nasa(args)
    elif args.mode == "verify-tool":
        verify(working=True)
        subprocess.run([sys.executable, "-I", "-B", str(ROOT / "support/check_certlim.py")], check=True)
    elif args.mode == "legacy-workspace":
        verify(working=True)
        from legacy_workspace import materialize
        print(materialize(args.destination))
    elif args.mode == "prepare-nasa":
        sys.path.insert(0, str(ROOT / "support"))
        from restore_nasa import restore
        print(restore())
    else:
        verify(working=getattr(args, "working", False))


if __name__ == "__main__":
    main()
