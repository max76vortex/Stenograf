# WS-025 — Agent Handoff Instruction (ASR benchmark gate)

## Назначение

Этот документ — готовое техническое задание для отдельного агента, который должен выполнить `WS-025` максимально качественно и верифицируемо.

## Контекст задачи

- Массовый прогон `WS-010` временно остановлен из-за нестабильного качества ASR.
- Нужно выбрать **primary + fallback** движки для русской речи через quality-gated benchmark.
- Канонический протокол: `memory-bank/creative/creative-asr-russian-benchmark-protocol.md`.

## Что агент должен сделать (обязательный scope)

1. Подготовить benchmark-папку:
   - `transcription/asr-benchmark/`
   - `transcription/asr-benchmark/results.csv`
   - `transcription/asr-benchmark/decision.md`
2. Собрать `golden set` минимум из 10 файлов (3 low-noise, 4 medium, 3 hard).
3. Прогнать минимум 3 кандидата:
   - baseline `faster-whisper` (текущий pipeline),
   - RU-ориентированный вариант,
   - второй облачный/альтернативный STT.
4. Заполнить `results.csv` по метрикам из протокола.
5. Зафиксировать решение в `decision.md`:
   - primary engine,
   - fallback engine,
   - trigger правила перехода на fallback.
6. Обновить `transcription/README.md` кратким блоком:
   - какой now-canonical путь Phase A,
   - когда включать fallback.

## Строгие ограничения (чтобы не поломать проект)

- Не менять текущий рабочий pipeline необратимо.
- Не удалять существующие артефакты в `audio-work`, `00_inbox`, `10_processed`.
- Любые новые внешние зависимости/сервисы — только с явной пометкой в `decision.md`.
- Не закрывать `WS-010`, пока gate не пройден документально.

## Формат `results.csv` (обязательные колонки)

`file_id,duration_min,noise,engine,A_loops,A_empty,A_coherence,A_pass,post_edit_min_per_10,punctuation_1_5,terms_1_5,notes`

## Критерий готовности (Definition of Done)

Задача считается выполненной только если:

1. Есть `results.csv` с данными по >=10 файлам и >=3 движкам.
2. Есть `decision.md` с чётким выбором primary/fallback и аргументацией.
3. В `decision.md` явно проверены пороги из протокола (`must-pass` + эксплуатационные).
4. В `README.md` отражён выбранный operational flow.
5. Данные воспроизводимы (понятно, как повторить тест).

## Формат финального отчёта агента (в чат)

Агент должен вернуть:

1. Список созданных/изменённых файлов.
2. Краткую сводку результатов по каждому кандидату.
3. Финальное решение: primary/fallback + trigger.
4. Риски и что осталось проверить.
5. Явный статус: `WS-025 READY FOR REVIEW`.

## Готовый текст-поручение агенту (можно вставить как есть)

```text
Выполни задачу WS-025 (ASR benchmark gate для русской речи) по протоколу:
memory-bank/creative/creative-asr-russian-benchmark-protocol.md

Обязательные артефакты:
1) transcription/asr-benchmark/results.csv
2) transcription/asr-benchmark/decision.md
3) update transcription/README.md (краткий operational flow)

Условия:
- минимум 10 файлов в golden set и минимум 3 ASR-кандидата;
- заполнить метрики quality gate;
- выбрать primary + fallback и правила переключения;
- ничего не удалять из текущих рабочих артефактов.

Верни финальный отчёт в формате:
- files changed
- benchmark summary
- decision (primary/fallback/trigger)
- residual risks
- статус: WS-025 READY FOR REVIEW
```
