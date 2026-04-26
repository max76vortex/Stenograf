from __future__ import annotations

import os
import sys
import sysconfig
from datetime import datetime
from pathlib import Path

from .base import AsrError, AsrRequest, AsrResult


PROVIDER_ID = "faster-whisper-local"
PROVIDER_VERSION = "faster-whisper-local-v1"


def _prepend_nvidia_cublas_bin() -> None:
    """Windows: help ctranslate2 find cublas64_12.dll from nvidia-cublas-cu12."""
    if sys.platform != "win32":
        return
    try:
        purelib = Path(sysconfig.get_paths()["purelib"])
        bin_dir = purelib / "nvidia" / "cublas" / "bin"
        if (bin_dir / "cublas64_12.dll").is_file():
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


class FasterWhisperLocalProvider:
    provider_id = PROVIDER_ID

    def __init__(self, *, model: str, device: str, compute_type: str) -> None:
        self.model = model
        self.device = device
        self.compute_type = compute_type
        try:
            _prepend_nvidia_cublas_bin()
            from faster_whisper import WhisperModel

            self._model = WhisperModel(model, device=device, compute_type=compute_type)
        except Exception as exc:
            raise AsrError(
                category="provider_unavailable",
                message=str(exc),
                provider_id=self.provider_id,
                model=model,
                retryable=False,
                details={"device": device, "compute_type": compute_type},
            ) from exc

    def transcribe(self, request: AsrRequest) -> AsrResult:
        if not request.audio_path.is_file():
            raise AsrError(
                category="input_not_found",
                message=f"Audio file not found: {request.audio_path}",
                provider_id=self.provider_id,
                model=self.model,
                retryable=False,
            )

        try:
            text, segments, language_detected, duration_sec = self._transcribe_once(
                request,
                language=request.language,
                vad_enabled=bool(request.runtime_options.get("vad_filter", False)),
            )
            min_chars = int(request.runtime_options.get("min_text_chars_retry", 0) or 0)
            if min_chars > 0 and len(text.strip()) < min_chars:
                print(
                    f"  ! short transcript ({len(text.strip())} chars), retry with language=auto/vad=off"
                )
                retry_text, retry_segments, retry_language, retry_duration = self._transcribe_once(
                    request,
                    language=None,
                    vad_enabled=False,
                )
                if len(retry_text.strip()) > len(text.strip()):
                    text = retry_text
                    segments = retry_segments
                    language_detected = retry_language
                    duration_sec = retry_duration
        except AsrError:
            raise
        except Exception as exc:
            raise AsrError(
                category="decode_failed",
                message=str(exc),
                provider_id=self.provider_id,
                model=self.model,
                retryable=True,
                details={"audio_path": str(request.audio_path)},
            ) from exc

        quality_flags = []
        if not text.strip():
            quality_flags.append("empty_output")

        return AsrResult(
            text=text,
            segments=segments,
            language_detected=language_detected,
            duration_sec=duration_sec,
            provider_id=self.provider_id,
            provider_version=PROVIDER_VERSION,
            model=self.model,
            runtime_options_effective={
                **request.runtime_options,
                "device": self.device,
                "compute_type": self.compute_type,
            },
            quality_flags=quality_flags,
            usage={},
            artifacts=[],
            created_at=datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        )

    def _transcribe_once(
        self,
        request: AsrRequest,
        *,
        language: str | None,
        vad_enabled: bool,
    ) -> tuple[str, list[dict[str, object]], str | None, float | None]:
        runtime = request.runtime_options
        lang = None if language == "auto" else language
        kwargs = {
            "language": lang,
            "beam_size": int(runtime.get("beam_size", 5)),
            "best_of": int(runtime.get("best_of", 5)),
            "temperature": float(runtime.get("temperature", 0.0)),
            "vad_filter": vad_enabled,
        }
        initial_prompt = str(runtime.get("initial_prompt", "") or "")
        if initial_prompt:
            kwargs["initial_prompt"] = initial_prompt

        raw_segments, info = self._model.transcribe(str(request.audio_path), **kwargs)
        normalized_segments = []
        text_parts = []
        for segment in raw_segments:
            segment_text = segment.text.strip()
            if not segment_text:
                continue
            text_parts.append(segment_text)
            normalized_segments.append(
                {
                    "start": getattr(segment, "start", None),
                    "end": getattr(segment, "end", None),
                    "text": segment_text,
                }
            )
        return (
            "\n".join(text_parts),
            normalized_segments,
            getattr(info, "language", None),
            getattr(info, "duration", None),
        )
