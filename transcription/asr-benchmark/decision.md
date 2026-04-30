# WS-025 ASR benchmark decision (RU)

## Final decision

- В operational-контуре проекта зафиксирован `speech2text-transcriptions` как основной ASR.
- Решение принято по итогам measured validation Worktree 2 и утверждено пользователем.

## Scope

- Protocol: `memory-bank/creative/creative-asr-russian-benchmark-protocol.md`
- Raw table: `transcription/asr-benchmark/results.csv`
- Historical runs: `transcription/asr-benchmark/runs/`

## Operational status

- `speech2text-transcriptions` — active default for ASR API path.
- `faster-whisper-local` сохраняется как локальный contingency/baseline в Core.
- Альтернативные кандидаты (`nexara`, `gigaam-v3`, legacy simulated cloud rows) переведены в архивный R&D-контур.

## Archive

Детальная история сравнения и промежуточные вердикты сохранены в:

- `transcription/asr-benchmark/archive/ASR_EVALUATION_ARCHIVE_2026-04.md`
