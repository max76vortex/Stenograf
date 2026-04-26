from __future__ import annotations

from .base import AsrProvider
from .faster_whisper_local import FasterWhisperLocalProvider


DEFAULT_ASR_PROVIDER_ID = "faster-whisper-local"
SUPPORTED_ASR_PROVIDER_IDS = {DEFAULT_ASR_PROVIDER_ID}


def get_provider(
    provider_id: str,
    *,
    model: str,
    device: str,
    compute_type: str,
) -> AsrProvider:
    if provider_id == DEFAULT_ASR_PROVIDER_ID:
        return FasterWhisperLocalProvider(model=model, device=device, compute_type=compute_type)
    raise ValueError(
        f"Unsupported ASR provider: {provider_id}. "
        f"Supported: {', '.join(sorted(SUPPORTED_ASR_PROVIDER_IDS))}"
    )


def get_asr_provider(
    provider_id: str,
    *,
    model: str,
    device: str,
    compute_type: str,
) -> AsrProvider:
    return get_provider(
        provider_id,
        model=model,
        device=device,
        compute_type=compute_type,
    )
