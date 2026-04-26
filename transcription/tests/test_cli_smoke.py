from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class CliSmokeTests(unittest.TestCase):
    def test_transcribe_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "transcription/transcribe_to_obsidian.py", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_coverage_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "transcription/check_coverage.py", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
