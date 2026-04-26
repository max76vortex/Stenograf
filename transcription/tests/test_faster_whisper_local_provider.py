from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path


TRANSCRIPTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRANSCRIPTION_DIR))

from asr_providers.base import AsrError, AsrRequest
from asr_providers.faster_whisper_local import FasterWhisperLocalProvider


class _FakeSegment:
    def __init__(self, text: str, start: float, end: float) -> None:
        self.text = text
        self.start = start
        self.end = end


class _FakeInfo:
    language = "ru"
    duration = 12.5


class _FakeWhisperModel:
    def __init__(self, model_size: str, device: str, compute_type: str) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.calls: list[tuple[str, dict[str, object]]] = []

    def transcribe(self, audio_path: str, **kwargs: object):
        self.calls.append((audio_path, kwargs))
        return (
            [
                _FakeSegment(" first line ", 0.0, 2.0),
                _FakeSegment(" ", 2.0, 2.5),
                _FakeSegment("second line", 2.5, 4.0),
            ],
            _FakeInfo(),
        )


class FasterWhisperLocalProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_fw_module = sys.modules.get("faster_whisper")
        fake_module = types.ModuleType("faster_whisper")
        fake_module.WhisperModel = _FakeWhisperModel
        sys.modules["faster_whisper"] = fake_module

    def tearDown(self) -> None:
        if self._orig_fw_module is None:
            sys.modules.pop("faster_whisper", None)
        else:
            sys.modules["faster_whisper"] = self._orig_fw_module

    def test_transcribe_returns_asr_result_for_valid_mp3(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            audio_path = Path(td) / "2026-04-26_001_test.mp3"
            audio_path.write_bytes(b"fake-mp3")

            provider = FasterWhisperLocalProvider(
                model="large-v3",
                device="cpu",
                compute_type="int8",
            )
            request = AsrRequest(
                audio_path=audio_path,
                language="ru",
                provider_id="faster-whisper-local",
                model="large-v3",
                runtime_options={
                    "beam_size": 5,
                    "best_of": 5,
                    "temperature": 0.0,
                    "vad_filter": False,
                    "initial_prompt": "",
                },
            )

            result = provider.transcribe(request)

            self.assertEqual(result.text, "first line\nsecond line")
            self.assertEqual(result.language_detected, "ru")
            self.assertEqual(result.duration_sec, 12.5)
            self.assertEqual(result.provider_id, "faster-whisper-local")
            self.assertEqual(result.model, "large-v3")
            self.assertEqual(len(result.segments), 2)

    def test_transcribe_raises_input_not_found_for_missing_file(self) -> None:
        provider = FasterWhisperLocalProvider(
            model="large-v3",
            device="cpu",
            compute_type="int8",
        )
        request = AsrRequest(
            audio_path=Path("C:/not-exists/audio.mp3"),
            language="ru",
            provider_id="faster-whisper-local",
            model="large-v3",
        )

        with self.assertRaises(AsrError) as exc_info:
            provider.transcribe(request)

        self.assertEqual(exc_info.exception.category, "input_not_found")


if __name__ == "__main__":
    unittest.main()
