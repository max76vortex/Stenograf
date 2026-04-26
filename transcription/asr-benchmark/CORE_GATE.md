# Core ASR Benchmark Gate

## Purpose

This document is the Core/MAS Delivery gate for accepting ASR provider changes from the ASR R&D worktree. Core v1.2 keeps `faster-whisper-local` as the production/default provider unless a fresh approved benchmark decision package explicitly approves another exact provider/profile.

## Current Core Default

- Provider id: `faster-whisper-local`
- Model/profile: `large-v3`
- Runtime default: local/offline execution (`device=cuda`, `compute_type=float16`, CPU fallback by explicit CLI option)
- Registry status: only `faster-whisper-local` is enabled by default in Core.

## Required Decision Package

Worktree 2 must hand off all of the following before Core changes a default provider, enables fallback routing, or treats an external/API provider as production:

- `transcription/asr-benchmark/decision.md`
- `transcription/asr-benchmark/results.csv`
- measured benchmark rows for the exact provider/profile being proposed
- raw run artifacts where available under `transcription/asr-benchmark/runs/`
- a verdict/status for the exact provider/profile
- known blockers: auth, quota/billing, runtime errors, missing env vars, data gaps
- rollback/default note: what Core should keep using if the proposed provider is rejected or becomes unavailable

Minimum `results.csv` gate fields:

- `file_id`, `duration_min`, `noise`, `engine`
- `A_loops`, `A_empty`, `A_coherence`, `A_pass`
- `post_edit_min_per_10`, `punctuation_1_5`, `terms_1_5`, `notes`

Minimum `decision.md` sections:

- scope/protocol and dataset reference
- candidate provider/profile
- measured aggregate pass/fail
- final or provisional recommendation
- freshness date for the current MAS delta
- blockers and operational risks
- artifact links for audit/reproduction

## Acceptable Gate Status

Core may change provider defaults only when the decision package says the exact provider/profile is approved. Acceptable wording includes:

- `approved`
- `accepted`
- `Pass as Primary`
- another explicit equivalent that clearly approves the exact provider/profile for Core production/default use

The decision must be fresh for the current MAS delta (`audio-transcription-v1` v1.2) or explicitly marked as still applicable to it.

## Non-Acceptable Status

Core must keep `faster-whisper-local` as default when the package is:

- missing
- stale
- simulated-only
- provisional
- validation in progress
- blocked by auth/quota/billing/runtime issues
- rejected
- ambiguous about exact provider/profile

Current examples:

- `yandex-speechkit` and `deepgram-nova-2` are legacy simulated/R&D context, not Core v1.2 defaults.
- Nexara is an active Worktree 2 candidate, but current measured validation is provisional/in progress and has blocker signals (`402`, missing `NEXARA_API_KEY` in latest preflight).
- GigaAM-v3 is rejected for operational primary/fallback in the current project scope.

## Worktree 2 -> Worktree 1 Handoff

Worktree 2 owns ASR R&D measurement and decision artifacts. Worktree 1 owns Core implementation and production defaults.

Handoff package from Worktree 2:

1. Updated `results.csv` with measured rows, not simulated placeholders, for the candidate provider/profile.
2. Updated `decision.md` with aggregate verdict, blocker status, and recommended Core action.
3. Raw run artifacts or clear links to them.
4. A rollback/default note that states whether Core should keep `faster-whisper-local`.
5. A concise handoff note in `memory-bank/creative/ws-026-worktree2-handoff.md` or successor document.

Worktree 1 consumption checklist:

1. Verify package freshness and exact provider/profile match.
2. Verify verdict is approved/accepted for Core production/default use.
3. Verify blockers are absent or explicitly non-blocking.
4. Keep secrets out of repo and manifests.
5. Implement any provider behind the provider abstraction and registry allowlist.
6. Keep `faster-whisper-local` as rollback/default unless the decision explicitly says otherwise.

## Core Action Matrix

| Decision package state | Core action |
|---|---|
| Missing/stale | Keep `faster-whisper-local`; no provider switch |
| Simulated-only | Keep `faster-whisper-local`; request measured rows |
| Provisional/in progress | Keep `faster-whisper-local`; wait for final decision |
| Blocked by auth/quota/runtime | Keep `faster-whisper-local`; request blocker resolution |
| Rejected | Keep `faster-whisper-local`; do not enable as default |
| Approved for exact provider/profile | Implement/enable only through provider abstraction and registry, with rollback note |

## Current Decision

As of the current run, no non-local provider is approved as Core v1.2 production/default. Core remains on `faster-whisper-local`.
