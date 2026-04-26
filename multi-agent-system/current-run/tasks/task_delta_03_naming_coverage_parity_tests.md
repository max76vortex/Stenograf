# Task Delta 03: Naming and Coverage Parity Tests

## Goal

Align naming between transcription and coverage so `transcribe_to_obsidian.py` and `check_coverage.py` always agree on expected `.md` names for normal and recursive modes. Add focused tests that do not download or initialize the ASR model.

## Inputs

- `current-run/plan.md`, D03 row.
- `current-run/technical_specification.md`, UC-03 and UC-04.
- `current-run/architecture.md`, Coverage and GUI / Compatibility guards.
- Existing code:
  - `transcription/transcribe_to_obsidian.py`
  - `transcription/check_coverage.py`
  - `transcription/tests/`

## Planned Changes

- Add a shared naming helper, preferred path: `transcription/naming.py`.
- Move or mirror the canonical `slug()` behavior into the helper without changing output names.
- Use the helper in both:
  - `transcription/transcribe_to_obsidian.py`
  - `transcription/check_coverage.py`
- Add focused stdlib tests for:
  - normal mode expected `.md` name;
  - recursive mode expected `.md` name from relative path;
  - slug truncation/sanitization parity;
  - `check_coverage.py` and transcription helper agreement.

## Acceptance Criteria

- [x] `transcribe_to_obsidian.py` and `check_coverage.py` use the same implementation for slug/expected `.md` naming.
- [x] Existing normal output names from audio stem remain unchanged.
- [x] Existing recursive output names from relative path remain unchanged.
- [x] `python transcription/check_coverage.py --help` still succeeds.
- [x] Focused parity tests pass without downloading or initializing ASR models.
- [x] No ASR provider default switch, external provider implementation, Ghost/CMS/n8n behavior, or Phase B behavior is introduced.

## Tests / Report Path

Report results in:

- `multi-agent-system/current-run/reports/task_delta_03_naming_coverage_parity_tests_report.md`

Expected checks:

- `python -m unittest transcription.tests.test_naming_parity`
- `python transcription/transcribe_to_obsidian.py --help`
- `python transcription/check_coverage.py --help`

## Non-Scope Guards

- Do not change date extraction, asset directory naming, or manifest semantics except where directly needed for naming parity.
- Do not implement cloud/API provider routing or provider default changes.

## Status

- [x] Planned
- [x] In progress
- [x] Done
