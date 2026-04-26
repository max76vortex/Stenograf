# Task Delta 01: ASR Provider Abstraction

## Goal

Create the v1.2 ASR provider boundary so Core/MAS Delivery no longer imports or instantiates `faster_whisper.WhisperModel` directly. The default implementation remains local `faster-whisper-local`, preserving existing CLI defaults and output behavior.

## Inputs

- `current-run/technical_specification.md` v1.2-delta.
- `current-run/architecture.md`, sections ASR Provider Abstraction, faster-whisper-local Provider, Provider Selection and Config.
- `current-run/architecture_review.md`, planning comments about concrete provider placement.
- Existing code:
  - `transcription/transcribe_to_obsidian.py`
  - `transcription/transcribe_gui.py`
  - `transcription/ingest_phone_recordings.py`
  - `transcription/transcription_limit_dispatcher.py`

## Planned Changes

- Add provider package:
  - `transcription/asr_providers/__init__.py`
  - `transcription/asr_providers/base.py`
  - `transcription/asr_providers/faster_whisper_local.py`
  - `transcription/asr_providers/registry.py`
- In `base.py`, define provider-neutral types:
  - `AsrRequest`
  - `AsrResult`
  - `AsrError`
  - `AsrProvider` protocol/base class.
- In `faster_whisper_local.py`, implement `FasterWhisperLocalProvider`.
  - This file is the only Core delivery file allowed to import or instantiate `WhisperModel`.
  - Map current CLI options into `WhisperModel(...).transcribe(...)`.
  - Preserve retry behavior for `--min-text-chars-retry`.
- In `registry.py`, define:
  - `DEFAULT_ASR_PROVIDER_ID = "faster-whisper-local"`.
  - allowlisted provider lookup for `faster-whisper-local`.
  - explicit rejection for unsupported provider ids.
- Refactor `transcribe_to_obsidian.py` so it obtains an ASR provider from the registry and calls it through `AsrRequest`.
- Do not add or enable external/API providers in this task.

## Acceptance Criteria

- [x] `transcribe_to_obsidian.py` does not import `faster_whisper` or reference `WhisperModel`.
- [x] `WhisperModel` import/instantiation exists only in `transcription/asr_providers/faster_whisper_local.py`, excluding docs/tests.
- [x] Existing CLI defaults still resolve to `faster-whisper-local`, `large-v3`, `device=cuda`, `compute_type=float16`.
- [x] Existing output Markdown shape, frontmatter fields, asset transcript names, and manifest leading columns remain compatible by intent.
- [x] Unsupported provider ids fail explicitly and cannot silently fall back to another provider.
- [x] `transcribe_gui.py`, `ingest_phone_recordings.py`, and `transcription_limit_dispatcher.py` continue to call the same CLI rather than adding separate ASR code.

## Tests / Report Path

Report:

- `multi-agent-system/current-run/reports/task_delta_01_provider_abstraction_report.md`

Checks recorded in the report:

- `python transcription/transcribe_to_obsidian.py --help`
- `python transcription/check_coverage.py --help`
- import-level check for `transcribe_to_obsidian`
- static search confirming `WhisperModel` placement.

## Non-Scope Guards

- No default provider switch away from `faster-whisper-local`.
- No Nexara/Yandex/Deepgram/GigaAM provider implementation.
- No Ghost/CMS/n8n posting or mandatory LLM/manual editing.

## Status

- [ ] Planned
- [ ] In progress
- [x] Done.
