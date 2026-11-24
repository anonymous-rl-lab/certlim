"""Exercise release membership, digests, and the declared working-file boundary."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from release_files import digest, verify_files


class ReleaseMembership(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.tracked = self.root / "tracked.txt"
        self.tracked.write_bytes(b"registered")
        (self.root / "SHA256SUMS").write_text(f"{digest(self.tracked)}  tracked.txt\n")

    def test_clean_then_unlisted(self):
        self.assertEqual(verify_files(self.root), 1)
        (self.root / "extra.txt").touch()
        with self.assertRaisesRegex(ValueError, "Unlisted.*extra.txt"):
            verify_files(self.root)

    def test_missing_then_modified(self):
        self.tracked.unlink()
        with self.assertRaisesRegex(ValueError, "Missing.*tracked.txt"):
            verify_files(self.root)
        self.tracked.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            verify_files(self.root, working=True, runtime_paths=[self.tracked])

    def test_work_outputs_are_explicit(self):
        folder = self.root / "replay_runs"
        folder.mkdir()
        (folder / "output.csv").touch()
        with self.assertRaisesRegex(ValueError, "Unlisted"):
            verify_files(self.root)
        self.assertEqual(verify_files(self.root, working=True), 1)
        (self.root / "other.csv").touch()
        with self.assertRaisesRegex(ValueError, "Unlisted.*other.csv"):
            verify_files(self.root, working=True)

    def test_nested_unlisted_evidence_is_rejected(self):
        folder = self.root / "paper_v25/evidence"
        folder.mkdir(parents=True)
        (folder / "stale.csv").touch()
        with self.assertRaisesRegex(ValueError, "Unlisted.*stale.csv"):
            verify_files(self.root, working=True)


if __name__ == "__main__":
    unittest.main()
