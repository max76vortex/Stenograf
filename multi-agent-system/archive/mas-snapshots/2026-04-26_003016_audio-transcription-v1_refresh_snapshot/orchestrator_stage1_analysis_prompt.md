# Старт оркестратора — этап 1 (Analysis)

Скопируй блоки ниже в сессию с оркестратором (см. `runbooks/orchestrator-start-prompt.md`) или используй как инструкцию для первого шага после `start-orchestrator.ps1`.

## Постановка задачи

```text
Довести до практического использования конвейер транскрибации накопленных диктофонных записей (~30 ГБ mp3): локально, максимальное качество (Whisper large-v3 через faster-whisper), вывод в отдельный vault Obsidian «Audio Brain» в папку 00_inbox. Порядок в папке записей и однозначная связь mp3 ↔ .md. Постинг в Ghost вне scope этого прогона.
```

## Описание проекта

```text
Workspace: C:\Users\sa\N8N-projects. Уже есть: скрипт transcription/transcribe_to_obsidian.py (large-v3, --recursive, --manifest), check_coverage.py, README и SETUP, дизайн в memory-bank/creative/creative-transcription-workflow.md, шаблоны в vault Audio Brain. Железо: RTX 3060 6 ГБ, CUDA. Примеры путей: записи D:\1 ЗАПИСИ ГОЛОС\recordings\, выход D:\Obsidian\Audio Brain\00_inbox\.

Оркестратор: первый шаг — этап Analysis. Вызвать аналитика (agents/02_analyst_prompt.md), результат — current-run/technical_specification.md. Учесть существующий код и не изобретать заново; формализовать требования, риски и критерии приёмки для оставшейся реализации и эксплуатации (тестовый прогон на реальных папках, edge cases имён, документация).
```

## Ожидаемые действия на Analysis

1. Прочитать `current-run/task_brief.md`, `current-run/project_context.md`, `memory-bank/creative/creative-transcription-workflow.md`, `transcription/README.md`.
2. Подготовить `current-run/technical_specification.md`: цели, сценарии, функциональные и нефункциональные требования, критерии приёмки, явное исключение Ghost/постинга.
3. При блокерах — `current-run/open_questions.md`.
4. Обновить `multi-agent-system/status.md` (этап Analysis завершён / ожидает подтверждения ТЗ).

Следующий этап по e2e-flow: **Review ТЗ** (`agents/03_tz_reviewer_prompt.md` → `tz_review.md`).
