# WS-025 ASR benchmark decision (RU)

## Scope and reproducibility

- Protocol: `memory-bank/creative/creative-asr-russian-benchmark-protocol.md`
- Dataset: 10-file golden set (`ru-gs-01`..`ru-gs-10`) with target split 3 low / 4 medium / 3 high noise.
- Candidates: `faster-whisper` (current baseline), `yandex-speechkit` (RU-oriented), `deepgram-nova-2` (alternative cloud STT), `nexara-transcriptions` (new cloud candidate).
- Additional candidate checked: `gigaam-v3-e2e_rnnt` (HF local smoke).
- Raw table: `transcription/asr-benchmark/results.csv`
- Current run type: **mixed**. `simulated` rows are still present for legacy cloud candidates; new measured Nexara smoke row has been added (`ru-gs-11`).

## Gate checks vs protocol

Thresholds:
- Primary: `A_pass >= 80%` and `post_edit <= 12 min / 10 min audio`
- Fallback: improves at least `50%` of files failed by primary on block A

Current measured aggregate (WS-026, Nexara):

| Engine | Runs (measured) | A_pass (pass/runs) | A_pass % | API status | Operational verdict |
|---|---:|---:|---:|---|---|
| nexara-transcriptions | 5 | 2/5 | 40% | 4x `200`, 1x `402` | Validation in progress (stay on candidate) |

Current measured Nexara runs (detail):

| File ID | Duration min | A_loops | A_empty | A_coherence | A_pass | API status | Notes |
|---|---:|---|---|---|---|---|---|
| ru-gs-11 | 10.1 | pass | pass | pass | pass | 200 | long noisy lecture-like sample |
| ru-gs-12 | 0.2 | pass | fail | fail | fail | 200 | very short output (10 chars) |
| ru-gs-13 | 0.3 | pass | pass | fail | fail | 200 | short fragment (58 chars) |
| ru-gs-14 | 162.2 | pass | pass | pass | pass | 200 | very long file, no pathological repeats by heuristic |
| ru-gs-15 | 0.0 | pass | fail | fail | fail | 402 | blocked by insufficient balance |

Legacy dry aggregate (historical simulated benchmark):

| Engine | A_pass (files/10) | A_pass % | Avg post_edit | Gate result | Scope |
|---|---:|---:|---:|---|---|
| faster-whisper | 4/10 | 40% | 16.1 | Fail | legacy baseline |
| yandex-speechkit | 9/10 | 90% | 10.4 | Pass as Primary | legacy simulated |
| deepgram-nova-2 | 9/10 | 90% | 11.3 | Pass as Fallback | legacy simulated |
| gigaam-v3-e2e_rnnt | 0/1 (smoke) | 0% | n/a | Not ready (environment/runtime blockers) | archived R&D |

## Decision

- **Working decision (2026-04-25):** stay on `nexara-transcriptions` as the current active candidate for WS-026 while continuing measured validation.
- **Operational mode:** single-engine path (`Nexara`) until we either (a) confirm stable pass on representative noisy set or (b) reject and switch to next candidate.
- **Baseline status:** keep `faster-whisper` only as local/offline contingency and comparison baseline.
- **GigaAM-v3 status:** **Rejected for primary/fallback in current project scope** (kept only as archived R&D branch).
- **Legacy dry-benchmark pair (`yandex-speechkit`/`deepgram-nova-2`):** retained as historical simulated comparison, not as current operational choice.

## Fallback triggers (explicit)

Route primary output to fallback when any trigger is true:

1. Repeated phrase loop: repeated block `>8 words` appears `>=2` times.
2. Suspiciously short transcript: `chars_per_min < 220` for non-silent recordings.
3. Coherence heuristic fail: sentence-fragment ratio suggests `<70%` coherent sentences.
4. Primary runtime/API failure: timeout, 5xx, quota/auth error.
5. Manual override: `needs_review=true` set by operator on quality spot-check.

## Operational note

Until live API run is completed, this decision is **provisional for review**. To finalize:

1. Replace `simulated` rows in `results.csv` with measured rows from real API calls.
2. Recompute aggregate metrics in this file.
3. Confirm the same primary/fallback pair still passes thresholds; otherwise rerun selection.

## Nexara measured smoke (2026-04-23)

- Endpoint: `POST https://api.nexara.ru/api/v1/audio/transcriptions`
- Auth: Bearer API key
- Measured run: `ru-gs-11` (`high` noise), `status=200`, `elapsed_sec=18.611`
- Artifacts:
  - `transcription/asr-benchmark/runs/ru-gs-11-nexara-20260423-205821.txt`
  - `transcription/asr-benchmark/runs/ru-gs-11-nexara-20260423-205821.json`
- Preliminary gate view for this single file: `A_pass=pass` (non-empty, coherent, no pathological looping detected).
- Extended noisy subset rerun (`ru-gs-12`, `ru-gs-13`) completed:
  - `ru-gs-12`: `A_pass=fail` (very short output, 10 chars),
  - `ru-gs-13`: `A_pass=fail` (short fragment, 58 chars, low coherence).
- Interim verdict: Nexara is operationally reachable and can work on some long noisy files (`ru-gs-11`), but currently **does not pass noisy mini-gate as reliable primary/fallback** for this project.
- Next required step: either (a) tune Nexara request params/prompting/preprocessing and rerun, or (b) move to next candidate in WS-026 with the same protocol.

## Additional base-file runs (2026-04-25)

- User requested two additional similar files from base.
- Runs executed:
  - `ru-gs-14` -> `D:\1 ЗАПИСИ ГОЛОС\recordings\2012-10\2012-10-16_001_DW_C0410.wav`
    - `status=200`, `duration=9733s` (~162.2 min), transcript size `119570` chars.
    - Heuristic anti-loop check (repeated long sentences) did not detect pathological repeats.
  - `ru-gs-15` -> `D:\1 ЗАПИСИ ГОЛОС\recordings\2012-10\2012-10-03_006_DW_C0409.wav`
    - `status=402`, response: `Недостаточно средств на аккаунте.`
- Operational blocker identified: account balance/quota currently prevents completing another full measured run.

## Worktree 2 rerun preflight (2026-04-26)

- Planned next measured file: `ru-gs-16` (`D:\1 ЗАПИСИ ГОЛОС\recordings\2012-10\2012-10-29_001_DW_A0414.wav`, long noisy).
- Run attempt stopped before API call because current session had no `NEXARA_API_KEY`:
  - error: `NEXARA_API_KEY environment variable is required`.
- Status impact:
  - no new measured quality datapoint added yet,
  - blocker is environment/billing readiness, not model-quality result.
- Exact rerun command pack is documented in:
  - `memory-bank/creative/ws-026-worktree2-handoff.md`

## GigaAM-v3 local findings (2026-04-21)

Runs executed (real, local):

1. `e2e_rnnt` short-file smoke:
   - completed with empty transcript (`transcript_chars=0`) in current environment.
2. `e2e_ctc` chunked run (`10s` segments, no longform API):
   - produced non-empty transcript (`5880` chars),
   - quality improved from empty output, but still showed repetitive loops on lecture-like fragments.
3. `e2e_ctc` chunked rerun (`6s` segments):
   - long lecture file: slightly cleaner than 10s mode but loops still present;
   - two short noisy assets: output remains too short/fragmented for production use.
4. GPU + dedupe rerun (`6s` segments + simple line dedupe):
   - environment switched to `torch==2.8.0+cu128` (`cuda_available=True`);
   - dedupe reduced exact duplicates only marginally (`segments_after_dedupe` changed `100 -> 99` on long file);
   - gate outcome for noisy files did not materially improve.
5. GPU + strong dedupe rerun (`6s` + fuzzy similarity):
   - applied adjacent fuzzy duplicate suppression (`similarity=0.88`) and repeat cap,
   - practical effect remained minimal on noisy set,
   - quality gate status unchanged.

Operational notes:

- Long-file `transcribe_longform` path requires `HF_TOKEN` for segmentation pipeline.
- Chunked mode allows running without `HF_TOKEN`, but repetition must still be quality-gated.
- GPU path is now active (`torch==2.8.0+cu128`), but quality issue persists (not just CPU performance problem).

Conclusion:

- GigaAM-v3 is **partially operational** via chunked mode without token.
- On current local setup, quality gate still fails on tested noisy assets (loops/low coherence/short outputs).
- **Decision fixed:** GigaAM-v3 is not accepted as operational primary/fallback for this project.
- Next action for WS-025: evaluate the next ASR candidate (non-Whisper path) with the same gate and update this file with measured results.
