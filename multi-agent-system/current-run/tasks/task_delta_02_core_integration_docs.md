# Task Delta 02: Core Integration, Batch Errors, and Docs Compatibility

## Goal

Integrate the ASR provider boundary into the main Core pipeline while keeping `faster-whisper-local` as the v1.2 default. Make batch failure behavior explicit and update user-facing docs so legacy cloud-provider wording is no longer presented as the Core production/default path.

## Inputs

- Output of `task_delta_01_provider_abstraction.md`.
- `current-run/architecture.md`, sections Main Flow, Provider Selection and Config, Manifest, Security and Constraints.
- `current-run/architecture_review.md`, major docs compatibility comment and minor batch error behavior comment.
- Existing docs/code:
  - `transcription/transcribe_to_obsidian.py`
  - `transcription/README.md`
  - `transcription/SETUP.md`
  - `transcription/asr-benchmark/decision.md`
  - `transcription/asr-benchmark/results.csv`

## Planned Changes

- In `transcribe_to_obsidian.py`:
  - Build `AsrRequest` for each audio file after skip/output-name decisions.
  - Consume `AsrResult.text` for Markdown generation.
  - Catch `AsrError` per file.
  - Keep existing behavior for successful/skipped files.
- Choose and implement batch error behavior:
  - continue processing remaining files after one ASR failure;
  - print visible `[FAILED]` message with file, provider id, model, and error category;
  - write no successful transcript artifact for the failed file;
  - preserve existing successful outputs;
  - exit `1` after the loop if one or more files failed.
- Extend manifest behavior compatibly:
  - preserve existing leading columns;
  - append provider/status/error fields for new manifests where needed;
  - failure rows use `asr_status=failed` and include `asr_error_category`/`asr_error_message`.
- Extend asset meta behavior where asset context exists:
  - record `asr_status=failed`;
  - record provider/model/error fields;
  - add a `versions[]` entry for failed Phase A attempt without `01_transcript__inbox.md`.
- Update `README.md`:
  - state Core v1.2 default is `faster-whisper-local`;
  - mark `yandex-speechkit` primary + `deepgram-nova-2` fallback as legacy simulated/R&D context, not production/default;
  - mark Nexara/GigaAM as R&D/provisional/rejected according to current decision package;
  - document selected batch failure behavior.
- Update `SETUP.md` only where useful for operational clarity:
  - install/run instructions should still describe local faster-whisper path;
  - mention non-zero exit on partial batch failures if this affects user workflow.

## Acceptance Criteria

- [x] Existing successful CLI commands still work with no new required flags.
- [x] Default provider remains `faster-whisper-local` unless a future fresh approved decision explicitly changes it.
- [x] A failed ASR call for one file does not create `out_path`, `01_transcript__inbox.md`, or inbox copy for that failed file.
- [x] Batch continues after a failed file and returns exit code `1` at the end if any file failed.
- [x] Manifest failure status is visible and legacy leading columns are preserved.
- [x] Asset `meta.json` records failure status when an asset/existing-asset context exists.
- [x] README/SETUP no longer imply `yandex-speechkit` + `deepgram-nova-2` is the v1.2 Core production/default flow.
- [x] Docs explicitly say external/API providers require a fresh approved decision for the exact provider/profile before default enablement.

## Tests / Report Path

Report results in:

- `multi-agent-system/current-run/reports/task_delta_02_core_integration_docs_report.md`

Expected checks:

- fake provider succeeds for one file and fails for another; successful file writes `.md`, failed file does not.
- manifest includes success and failure rows with compatible leading columns.
- asset-mode failure updates `meta.json` without writing a successful transcript.
- process exits `1` when any file failed and `0` when all files are successful/skipped.
- docs review confirms the old cloud-provider operational flow is either removed or clearly scoped as historical/R&D.

## Non-Scope Guards

- Do not implement cloud/API provider routing.
- Do not switch default provider based on current provisional benchmark artifacts.
- Do not add Ghost/CMS/n8n posting or make Phase B/manual editing mandatory.

## Status

- [x] Planned
- [x] In progress
- [x] Done
- [x] Reviewed: approved_with_comments

## Status

- [x] Planned
- [x] In progress
- [x] Done
