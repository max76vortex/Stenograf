from __future__ import annotations

import sys
import unittest
from pathlib import Path


TRANSCRIPTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRANSCRIPTION_DIR))

from asr_providers.registry import (
    DEFAULT_ASR_PROVIDER_ID,
    SUPPORTED_ASR_PROVIDER_IDS,
    get_provider,
)


class AsrProviderRegistryTests(unittest.TestCase):
    def test_default_provider_is_allowlisted(self) -> None:
        self.assertEqual(DEFAULT_ASR_PROVIDER_ID, "faster-whisper-local")
        self.assertIn(DEFAULT_ASR_PROVIDER_ID, SUPPORTED_ASR_PROVIDER_IDS)
        self.assertIn("speech2text-transcriptions", SUPPORTED_ASR_PROVIDER_IDS)

    def test_unsupported_provider_id_fails_explicitly(self) -> None:
        with self.assertRaises(ValueError) as exc_info:
            get_provider(
                "unsupported-provider",
                model="large-v3",
                device="cpu",
                compute_type="int8",
            )
        msg = str(exc_info.exception)
        self.assertIn("Unsupported ASR provider", msg)
        self.assertIn("unsupported-provider", msg)
        self.assertIn("faster-whisper-local", msg)
        self.assertIn("speech2text-transcriptions", msg)


if __name__ == "__main__":
    unittest.main()
