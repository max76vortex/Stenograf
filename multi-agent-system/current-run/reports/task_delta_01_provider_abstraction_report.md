# Task Delta 01 Report: ASR Provider Abstraction

## Status

- Result: completed, ready for code review.
- Blocking questions: none.
- Scope guard: no external/API ASR provider was added or enabled.

## Changes Implemented (Code + Tests)

- Core abstraction package used by delivery code:
  - `transcription/asr_providers/base.py`
  - `transcription/asr_providers/faster_whisper_local.py`
  - `transcription/asr_providers/registry.py`
  - `transcription/asr_providers/__init__.py`
- `transcription/transcribe_to_obsidian.py` uses `AsrRequest`/`AsrResult` and provider lookup via registry; direct `faster_whisper`/`WhisperModel` usage removed.
- Added test `transcription/tests/test_asr_provider_registry.py`:
  - default provider allowlist check;
  - explicit failure for unsupported provider ids (no silent fallback).

## Test Report

### Added or Updated Tests

- Added: `transcription/tests/test_asr_provider_registry.py` (2 tests).
- Existing regression tests used:
  - `transcription/tests/test_faster_whisper_local_provider.py`
  - `transcription/tests/test_transcribe_failures.py`
  - `transcription/tests/test_cli_smoke.py`
  - full suite via `transcription/tests/test_*.py`

### Tests Executed

- `python transcription/transcribe_to_obsidian.py --help`
- `python transcription/check_coverage.py --help`
- `python -c "import sys; sys.path.insert(0, 'transcription'); import transcribe_to_obsidian; print('import-ok')"`
- `python -m unittest discover -s transcription/tests -p "test_*.py"`
- Static checks:
  - `transcribe_to_obsidian.py` has no `faster_whisper`/`WhisperModel` references.
  - `WhisperModel` import/instantiation in Core code is only in `transcription/asr_providers/faster_whisper_local.py` (tests excluded).

### Results

- Unit/regression tests: **28 passed, 0 failed**.
- Help/import checks: **3 passed, 0 failed**.
- Regressions: **not detected**.
- Task readiness: **ready for review**.

## Notes

- Existing CLI defaults remain compatible: provider `faster-whisper-local`, model `large-v3`, device `cuda`, compute type `float16`.
- Markdown/frontmatter layout, asset transcript naming, and manifest leading columns remain compatible by intent.
