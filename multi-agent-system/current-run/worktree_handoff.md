# Worktree Handoff: ASR Benchmark Gate

## Purpose

This is the current-run Core-readable handoff contract for `audio-transcription-v1` v1.2-delta. It explains what Worktree 2 can hand off, what Worktree 1 can consume, and when Core may change the ASR production/default provider.

The detailed gate remains `transcription/asr-benchmark/CORE_GATE.md`.

## Current Core Default

Core production/default ASR remains `faster-whisper-local` (`large-v3`) until a fresh approved decision package explicitly approves another exact provider/profile.

No current benchmark artifact approves Nexara, Yandex SpeechKit, Deepgram, or GigaAM as Core default.

## Required Decision Package

Before Worktree 1 changes the Core default provider, enables provider-specific fallback routing, or treats an external/API provider as production, the handoff package must include:

- `transcription/asr-benchmark/decision.md`.
- `transcription/asr-benchmark/results.csv`.
- Measured, not simulated-only, rows for the exact provider/profile being proposed.
- A clear verdict/status for the exact provider/profile.
- Freshness/applicability to `audio-transcription-v1` v1.2-delta.
- Quality and operational metrics sufficient for review.
- Known blockers such as auth, quota/billing, runtime, missing env vars, or data gaps.
- Rollback/default note stating what Core should use if the provider is rejected or unavailable.

## Insufficient States

The following states are not enough to switch Core default away from `faster-whisper-local`:

- missing or stale package;
- simulated-only evidence;
- provisional status;
- validation in progress;
- blocked by auth, quota/billing, runtime, environment, or missing measured data;
- rejected;
- ambiguous recommendation that does not approve the exact provider/profile.

## Current Package Interpretation

- Nexara (`nexara-transcriptions`) is active Worktree 2 R&D/provisional validation and is not approved as Core default. Current blockers include incomplete measured validation, prior `402` balance/quota failure, and missing `NEXARA_API_KEY` in the latest preflight.
- `yandex-speechkit` and `deepgram-nova-2` are historical simulated comparison rows, not current Core operational defaults.
- GigaAM-v3 is rejected for current primary/fallback scope.
- Core therefore keeps `faster-whisper-local` as production/default provider.

## Worktree 2 -> Worktree 1 Contract

Worktree 2 owns ASR R&D artifacts: benchmark runs, `results.csv`, `decision.md`, recommendations, rerun commands, and blocker notes.

Worktree 1 owns Core changes: provider abstraction, registry/default selection, CLI integration, fallback behavior, docs that affect Core operation, and any production/default enablement.

Direct R&D edits to Core delivery scripts are outside the handoff unless Worktree 1 explicitly reviews and accepts them. Any accepted provider integration must go through the provider abstraction and registry allowlist.

