from __future__ import annotations

import sys
import unittest
from pathlib import Path


TRANSCRIPTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRANSCRIPTION_DIR))

from naming import get_expected_md_name, slugify


class NamingLayerTests(unittest.TestCase):
    def test_slugify(self) -> None:
        self.assertEqual(slugify("  idea @@@  test  "), "idea-test")
        self.assertEqual(slugify("   "), "transcript")

    def test_get_expected_md_name_flat(self) -> None:
        root = Path(r"D:\recordings")
        audio = root / "2023-10-01_001.mp3"
        self.assertEqual(
            get_expected_md_name(audio, root, recursive=False),
            "2023-10-01_001.md",
        )

    def test_get_expected_md_name_recursive(self) -> None:
        root = Path(r"D:\recordings")
        audio = root / "2023-10" / "2023-10-01_001.mp3"
        self.assertEqual(
            get_expected_md_name(audio, root, recursive=True),
            "2023-10_2023-10-01_001.md",
        )

    def test_parity_transcribe_and_coverage(self) -> None:
        # Import both scripts to ensure they share the same naming function.
        import check_coverage  # pylint: disable=import-outside-toplevel
        import transcribe_to_obsidian  # pylint: disable=import-outside-toplevel

        root = Path(r"D:\recordings")
        audio = root / "2023-10" / "2023-10-01_001.mp3"
        expected = get_expected_md_name(audio, root, recursive=True)

        self.assertIs(check_coverage.get_expected_md_name, get_expected_md_name)
        self.assertIs(transcribe_to_obsidian.get_expected_md_name, get_expected_md_name)
        self.assertEqual(check_coverage.get_expected_md_name(audio, root, True), expected)
        self.assertEqual(transcribe_to_obsidian.get_expected_md_name(audio, root, True), expected)


if __name__ == "__main__":
    unittest.main()
