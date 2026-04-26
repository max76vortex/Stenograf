from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class AsrRequest:
    audio_path: Path
    language: str | None
    provider_id: str
    model: str
    runtime_options: dict[str, object] = field(default_factory=dict)
    source_metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class AsrResult:
    text: str
    segments: list[dict[str, object]]
    language_detected: str | None
    duration_sec: float | None
    provider_id: str
    provider_version: str
    model: str
    runtime_options_effective: dict[str, object]
    quality_flags: list[str]
    usage: dict[str, object]
    artifacts: list[str]
    created_at: str


class AsrError(Exception):
    def __init__(
        self,
        *,
        category: str,
        message: str,
        provider_id: str,
        model: str,
        retryable: bool,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.category = category
        self.message = message
        self.provider_id = provider_id
        self.model = model
        self.retryable = retryable
        self.details = details or {}


class AsrProvider(Protocol):
    provider_id: str

    def transcribe(self, request: AsrRequest) -> AsrResult:
        ...
