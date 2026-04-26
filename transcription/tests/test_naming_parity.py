from __future__ import annotations

import sys
import unittest
from pathlib import Path


TRANSCRIPTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRANSCRIPTION_DIR))

import check_coverage
import transcribe_to_obsidian
from asr_providers import get_provider
from asr_providers.base import AsrRequest, AsrResult
from naming import get_expected_md_name, slugify


class NamingParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_argv = sys.argv[:]

    def tearDown(self) -> None:
        sys.argv = self._orig_argv

    def test_slugify_matches_transcription_import(self) -> None:
        raw = "  2026-04-26_001 идея, проект !!!  "
        self.assertEqual(transcribe_to_obsidian.slugify(raw), slugify(raw))

    def test_slugify_truncation_and_fallback(self) -> None:
        self.assertEqual(slugify(" !!! "), "transcript")
        self.assertEqual(len(slugify("a" * 200)), 120)

    def test_normal_expected_name(self) -> None:
        root = Path("recordings")
        audio = root / "2026-04" / "2026-04-26_001 idea!.mp3"
        self.assertEqual(
            get_expected_md_name(audio, root, recursive=False),
            "2026-04-26_001-idea.md",
        )

    def test_recursive_expected_name_uses_relative_path(self) -> None:
        root = Path("recordings")
        audio = root / "2026-04" / "2026-04-26_001 idea!.mp3"
        self.assertEqual(
            get_expected_md_name(audio, root, recursive=True),
            "2026-04_2026-04-26_001-idea.md",
        )

    def test_check_coverage_uses_same_expected_name(self) -> None:
        root = Path("recordings")
        audio = root / "2026-04" / "2026-04-26_001 idea!.mp3"
        self.assertIs(check_coverage.get_expected_md_name, get_expected_md_name)
        self.assertEqual(
            check_coverage.get_expected_md_name(audio, root, recursive=True),
            get_expected_md_name(audio, root, recursive=True),
        )

    def test_get_provider_unknown_id_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            get_provider("unknown_id", model="large-v3", device="cpu", compute_type="int8")

    def test_asr_models_import_success(self) -> None:
        req = AsrRequest(audio_path=Path("a.mp3"), language="ru", provider_id="x", model="m")
        res = AsrResult(
            text="ok",
            segments=[],
            language_detected="ru",
            duration_sec=1.0,
            provider_id="x",
            provider_version="v1",
            model="m",
            runtime_options_effective={},
            quality_flags=[],
            usage={},
            artifacts=[],
            created_at="2026-04-26T00:00:00",
        )
        self.assertEqual(req.model, "m")
        self.assertEqual(res.text, "ok")

    def test_transcribe_cli_help_exits_zero(self) -> None:
        sys.argv = ["transcribe_to_obsidian.py", "--help"]
        with self.assertRaises(SystemExit) as exc_info:
            transcribe_to_obsidian.main()
        self.assertEqual(exc_info.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
