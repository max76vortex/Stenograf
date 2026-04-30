# Архив ASR-оценки (2026-04)

Статус: архивный материал R&D по выбору ASR до фиксации рабочего решения.

## Что тестировали

- `faster-whisper` (локальный baseline)
- `gigaam-v3` (локальный кандидат)
- `nexara-transcriptions` (API-кандидат)
- `speech2text-transcriptions` (API-кандидат)
- исторические simulated-сравнения для `yandex-speechkit` и `deepgram-nova-2`

## Где лежат результаты

- Сводная таблица: `transcription/asr-benchmark/results.csv`
- История run-артефактов: `transcription/asr-benchmark/runs/`
- Рабочий итоговый вердикт: `transcription/asr-benchmark/decision.md`

## Финальный итог

- По решению пользователя в operational-контуре проекта зафиксирован `speech2text-transcriptions` как основной ASR.
- Материалы по альтернативным кандидатам сохранены как архив для дальнейшего сравнения, но не являются текущим default-путём.
