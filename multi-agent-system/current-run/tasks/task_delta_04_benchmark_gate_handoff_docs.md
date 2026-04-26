# Task Delta 04: Benchmark Gate and Handoff Documentation

## Goal

Document the Core-readable benchmark gate and Worktree 1/2 handoff contract so future ASR provider/profile changes cannot become Core defaults without a fresh approved decision package.

## Inputs

- `current-run/plan.md`, D04 row.
- `current-run/architecture.md`, Benchmark Gate Consumption and Worktree Handoff Interface.
- `transcription/asr-benchmark/decision.md`.
- `transcription/asr-benchmark/results.csv`.
- `memory-bank/creative/ws-026-worktree2-handoff.md`.

## Planned Changes

- Add or update a Core-facing benchmark gate document under `transcription/asr-benchmark/`.
- Document required files, required fields/statuses, freshness rules, rejection/provisional handling, and Core actions.
- Document Worktree 2 -> Worktree 1 handoff package expectations.
- Link the gate document from `transcription/README.md`.
- Do not enable external/API providers or change the Core default provider.

## Acceptance Criteria

- [x] Core gate doc states the current default remains `faster-whisper-local`.
- [x] Gate doc states external/API providers require fresh approved decision for exact provider/profile before default enablement.
- [x] Gate doc defines minimum decision package: `decision.md`, `results.csv`, measured rows, verdict/status, blockers, rollback/default note.
- [x] Gate doc explains how to treat provisional, simulated-only, blocked, rejected, stale, or missing decision packages.
- [x] Worktree 2 handoff expectations are explicit and compatible with `memory-bank/creative/ws-026-worktree2-handoff.md`.
- [x] README links to the gate doc.
- [x] No code behavior or provider default changes are introduced.

## Tests / Report Path

Report results in:

- `multi-agent-system/current-run/reports/task_delta_04_benchmark_gate_handoff_docs_report.md`

Expected checks:

- Docs review: README links to the gate doc.
- Static review: provider registry still supports only `faster-whisper-local`.
- Optional smoke: `python transcription/transcribe_to_obsidian.py --help`.

## Non-Scope Guards

- Do not implement Nexara/Yandex/Deepgram/GigaAM providers.
- Do not switch default provider.
- Do not add Ghost/CMS/n8n publishing behavior.

## Status

- [x] Planned
- [x] In progress
- [x] Done
