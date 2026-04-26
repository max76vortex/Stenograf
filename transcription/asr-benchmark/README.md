# ASR Benchmark Gate Contract (Core v1.2-delta)

Этот документ фиксирует минимальный контракт между потоками:

- **Worktree 2 (ASR R&D)** — измеряет кандидатов и готовит decision package.
- **Worktree 1 (Core Delivery)** — принимает/не принимает смену default provider только по утвержденному decision package.

Детальные правила Core gate остаются в `CORE_GATE.md`. Этот файл задает короткий operational минимум для практической передачи результата.

## Поток принятия решения

1. Worktree 2 запускает benchmark на релевантном датасете и сохраняет измерения.
2. Worktree 2 обновляет:
   - `transcription/asr-benchmark/results.csv`
   - `transcription/asr-benchmark/decision.md`
3. Worktree 2 передает пакет в Worktree 1 вместе с артефактами запусков (`runs/` при наличии).
4. Worktree 1 проверяет свежесть и однозначность вердикта.
5. Default provider в Core меняется только если `decision.md` явно утверждает точный provider/profile.

Если `decision.md` отсутствует, устарел, имеет provisional/in-progress статус или не утверждает точный provider/profile, Core сохраняет default `faster-whisper-local`.

## Обязательные поля `results.csv`

Каждая строка benchmark (минимум) должна содержать:

- `file_id`
- `duration_min`
- `noise`
- `engine`
- `A_loops`
- `A_empty`
- `A_coherence`
- `A_pass`

Дополнительные метрики допускаются, но поля выше обязательны для gate-проверки.

## Минимальные требования к `decision.md`

`decision.md` должен явно содержать:

- кандидат (`provider/profile`), к которому относится решение;
- агрегированный итог benchmark (pass/fail);
- итоговый вердикт (`approved`/`accepted` или эквивалент для точного provider/profile);
- список блокеров и operational рисков (если есть);
- указание rollback/default поведения (что делать при отказе кандидата).

## Правило интеграции в Core

Worktree 1 не переключает production/default путь на основании промежуточных заметок или локальных предположений. Единственный источник решения — актуальный и однозначный `decision.md`, подтвержденный `results.csv`.
