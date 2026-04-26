from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path


TRANSCRIPTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRANSCRIPTION_DIR))

import transcribe_to_obsidian as tto
from asr_providers.base import AsrError, AsrRequest, AsrResult


class FakeProvider:
    provider_id = "faster-whisper-local"

    def __init__(self) -> None:
        self.fail_once_stems: set[str] = set()
        self.attempts: dict[str, int] = {}

    def transcribe(self, request: AsrRequest) -> AsrResult:
        stem = request.audio_path.stem
        self.attempts[stem] = self.attempts.get(stem, 0) + 1
        if stem in self.fail_once_stems and self.attempts[stem] == 1:
            raise AsrError(
                category="decode_failed",
                message="fake decode failure",
                provider_id=self.provider_id,
                model=request.model,
                retryable=True,
            )
        if "fail" in stem:
            raise AsrError(
                category="decode_failed",
                message="fake decode failure",
                provider_id=self.provider_id,
                model=request.model,
                retryable=True,
            )
        return AsrResult(
            text=f"transcript for {request.audio_path.name}",
            segments=[],
            language_detected="ru",
            duration_sec=None,
            provider_id=self.provider_id,
            provider_version="fake",
            model=request.model,
            runtime_options_effective=request.runtime_options,
            quality_flags=[],
            usage={},
            artifacts=[],
            created_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        )


class TranscribeFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_get_provider = tto.get_provider
        self._orig_argv = sys.argv[:]
        self.provider = FakeProvider()
        tto.get_provider = lambda *args, **kwargs: self.provider

    def tearDown(self) -> None:
        tto.get_provider = self._orig_get_provider
        sys.argv = self._orig_argv

    def run_main(self, *args: str) -> int:
        sys.argv = ["transcribe_to_obsidian.py", *args]
        try:
            tto.main()
        except SystemExit as exc:
            return int(exc.code or 0)
        return 0

    def test_batch_continues_after_one_file_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_dir = root / "input"
            output_dir = root / "out"
            input_dir.mkdir()
            output_dir.mkdir()
            (input_dir / "2026-04-26_001_ok.mp3").write_bytes(b"ok")
            (input_dir / "2026-04-26_002_fail.mp3").write_bytes(b"fail")
            (input_dir / "2026-04-26_003_ok.mp3").write_bytes(b"ok")
            manifest = root / "manifest.csv"

            rc = self.run_main(str(input_dir), str(output_dir), "--manifest", str(manifest))

            self.assertEqual(rc, 1)
            self.assertTrue((output_dir / "2026-04-26_001_ok.md").exists())
            self.assertFalse((output_dir / "2026-04-26_002_fail.md").exists())
            self.assertTrue((output_dir / "2026-04-26_003_ok.md").exists())

            with manifest.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                self.assertEqual(reader.fieldnames[:4], ["timestamp", "mp3_path", "md_name", "date"])
                self.assertIn("asr_provider", reader.fieldnames)
                self.assertIn("asr_status", reader.fieldnames)
                self.assertIn("error_category", reader.fieldnames)
                self.assertIn("elapsed_sec", reader.fieldnames)
                rows = list(reader)
            self.assertEqual([row["asr_status"] for row in rows], ["success", "failed", "success"])
            self.assertEqual(rows[1]["asr_error_category"], "decode_failed")
            self.assertEqual(rows[1]["error_category"], "decode_failed")
            self.assertTrue(float(rows[0]["elapsed_sec"]) >= 0.0)
            self.assertTrue(float(rows[1]["elapsed_sec"]) >= 0.0)
            self.assertTrue(float(rows[2]["elapsed_sec"]) >= 0.0)

    def test_legacy_manifest_header_stays_compatible_on_append(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_dir = root / "input"
            output_dir = root / "out"
            input_dir.mkdir()
            output_dir.mkdir()
            (input_dir / "2026-04-26_001_ok.mp3").write_bytes(b"ok")
            (input_dir / "2026-04-26_002_fail.mp3").write_bytes(b"fail")
            manifest = root / "manifest_legacy.csv"
            manifest.write_text("timestamp,mp3_path,md_name,date\n", encoding="utf-8")

            rc = self.run_main(str(input_dir), str(output_dir), "--manifest", str(manifest))

            self.assertEqual(rc, 1)
            raw_lines = manifest.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(raw_lines[0], "timestamp,mp3_path,md_name,date")
            self.assertEqual(len(raw_lines), 3)
            self.assertIn(",success,", raw_lines[1])
            self.assertIn(",failed,", raw_lines[2])
            self.assertTrue(raw_lines[1].count(",") >= 10)
            self.assertTrue(raw_lines[2].count(",") >= 10)

    def test_exit_zero_when_all_files_succeed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_dir = root / "input"
            output_dir = root / "out"
            input_dir.mkdir()
            output_dir.mkdir()
            (input_dir / "2026-04-26_001_ok.mp3").write_bytes(b"ok1")
            (input_dir / "2026-04-26_002_ok.mp3").write_bytes(b"ok2")

            rc = self.run_main(str(input_dir), str(output_dir))

            self.assertEqual(rc, 0)
            self.assertTrue((output_dir / "2026-04-26_001_ok.md").exists())
            self.assertTrue((output_dir / "2026-04-26_002_ok.md").exists())

    def test_exit_zero_when_all_files_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_dir = root / "input"
            output_dir = root / "out"
            input_dir.mkdir()
            output_dir.mkdir()
            (input_dir / "2026-04-26_001_ok.mp3").write_bytes(b"ok")
            existing_md = output_dir / "2026-04-26_001_ok.md"
            existing_md.write_text("already exists", encoding="utf-8")

            rc = self.run_main(str(input_dir), str(output_dir))

            self.assertEqual(rc, 0)
            self.assertEqual(existing_md.read_text(encoding="utf-8"), "already exists")

    def test_asset_failure_updates_meta_without_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_dir = root / "input"
            output_dir = root / "out"
            asset_root = root / "assets"
            input_dir.mkdir()
            output_dir.mkdir()
            (input_dir / "2026-04-26_001_fail.mp3").write_bytes(b"fail")
            manifest = root / "manifest.csv"

            rc = self.run_main(
                str(input_dir),
                str(output_dir),
                "--asset-root",
                str(asset_root),
                "--manifest",
                str(manifest),
            )

            self.assertEqual(rc, 1)
            meta_files = list(asset_root.rglob("meta.json"))
            self.assertEqual(len(meta_files), 1)
            meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
            self.assertEqual(meta["asr_status"], "failed")
            self.assertEqual(meta["asr_error_category"], "decode_failed")
            self.assertEqual(meta["versions"][-1]["asr_status"], "failed")
            self.assertEqual(meta["versions"][-1]["transcript_file"], "")
            self.assertFalse((meta_files[0].parent / "01_transcript__inbox.md").exists())
            self.assertEqual(list(output_dir.glob("*.md")), [])

    def test_existing_asset_failure_updates_meta_without_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            asset_dir = root / "asset"
            output_dir = root / "out"
            asset_dir.mkdir()
            output_dir.mkdir()
            (asset_dir / "2026-04-26_001_fail_asr.mp3").write_bytes(b"fail")
            meta_path = asset_dir / "meta.json"
            meta_path.write_text(
                json.dumps(
                    {
                        "audio_file": "2026-04-26_001_fail.mp3",
                        "source_audio_path": str(asset_dir / "2026-04-26_001_fail.mp3"),
                        "versions": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            rc = self.run_main(str(asset_dir), str(output_dir), "--existing-asset")

            self.assertEqual(rc, 1)
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertEqual(meta["asr_status"], "failed")
            self.assertEqual(meta["asr_provider"], "faster-whisper-local")
            self.assertEqual(meta["asr_error_category"], "decode_failed")
            self.assertEqual(meta["versions"][-1]["asr_status"], "failed")
            self.assertEqual(meta["versions"][-1]["transcript_file"], "")
            self.assertFalse((asset_dir / "01_transcript__inbox.md").exists())
            self.assertEqual(list(output_dir.glob("*.md")), [])

    def test_asset_failure_keeps_source_retryable_with_same_command(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            input_dir = root / "input"
            output_dir = root / "out"
            asset_root = root / "assets"
            input_dir.mkdir()
            output_dir.mkdir()
            source = input_dir / "2026-04-26_001_retry.mp3"
            source.write_bytes(b"retry")
            self.provider.fail_once_stems.add(source.stem)

            first_rc = self.run_main(str(input_dir), str(output_dir), "--asset-root", str(asset_root))

            self.assertEqual(first_rc, 1)
            self.assertTrue(source.exists())
            self.assertEqual(list(output_dir.glob("*.md")), [])

            second_rc = self.run_main(str(input_dir), str(output_dir), "--asset-root", str(asset_root))

            self.assertEqual(second_rc, 0)
            self.assertFalse(source.exists())
            meta_files = list(asset_root.rglob("meta.json"))
            self.assertEqual(len(meta_files), 1)
            self.assertTrue((meta_files[0].parent / "01_transcript__inbox.md").exists())
            meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
            self.assertEqual(meta["asr_status"], "success")
            self.assertEqual([v["asr_status"] for v in meta["versions"]], ["failed", "success"])


if __name__ == "__main__":
    unittest.main()
