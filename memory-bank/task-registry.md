# Реестр задач workspace (WS-NNN)

**Правила:** см. **`task-tracking.md`**. Статусы: `Open` | `Done` | `Cancelled`.

| ID | Title | Status | Created | Completed | Notes |
|----|-------|--------|---------|-----------|-------|
| WS-001 | Журнал активности, скрипты, скилл workspace-activity-report, git hook | Done | 2026-03-22 | 2026-03-22 | commit `84fdb22`, `progress.md` |
| WS-002 | Правила учёта задач: task-tracking.md + реестр | Done | 2026-03-22 | 2026-03-22 | `.cursor/rules/workspace-task-tracking.mdc` |
| WS-003 | Скилл memory-bank-init + bootstrap шаблоны + GLOBAL-CURSOR-SETUP; правка глобального memory-bank.mdc | Done | 2026-03-22 | 2026-03-22 | `memory-bank/bootstrap/`, `.cursor/skills/memory-bank-init`; зеркало инструкций WS-001–003 в Obsidian `20_system/Система мультиагентов/` |
| WS-004 | Подготовка дизайн-пакета для будущей реализации Supervisor/Sentinel | Done | 2026-03-14 | 2026-03-14 | `memory-bank/creative/creative-supervisor-sentinel.md`; scope, SLA, states, escalation, MVP/DoR |
| WS-005 | Подготовка дизайн-пакета для будущей реализации Delivery Observer / Project Documenter | Done | 2026-03-14 | 2026-03-14 | `memory-bank/creative/creative-delivery-observer-project-documenter.md`; inputs/outputs, quality policy, orchestration flow, MVP/DoR |
| WS-006 | MAS: исправление `mas-new-run.ps1` — проверка WhatIf (`$WhatIf` → `$WhatIfPreference`) | Done | 2026-03-24 | 2026-03-24 | `multi-agent-system/tools/mas-new-run.ps1`; dry-run `-WhatIf -Force` снова завершается с кодом 0 |
| WS-007 | MAS чистый старт + контекст прогона транскрибации: `audio-transcription-v1`, заполнены task_brief/project_context, `check_coverage.py` | Done | 2026-03-24 | 2026-03-24 | Snapshot `archive/mas-snapshots/2026-03-24_212219_audio-transcription-v1_previous/` |
| WS-008 | Предпочтение: документация в Obsidian через MCP без напоминания; заметки в vault; промпт этапа Analysis для оркестратора | Done | 2026-03-24 | 2026-03-24 | `memory-bank/user-preferences.md`; Obsidian `20_system/`; `current-run/orchestrator_stage1_analysis_prompt.md` |
| WS-009 | MAS audio-transcription-v1: TZ review, architecture (+review), plan (+review), ТЗ v1.1, статус → user acceptance | Done | 2026-03-24 | 2026-03-24 | `current-run/tz_review.md`, `architecture.md`, `plan.md`, reviews; Obsidian MAS-заметка обновлена |
| WS-010 | Транскрибация: исполняемый план (спринты A/B), task_01, task_02, `run-smoke-test.ps1` | Open | 2026-03-30 | | Массовый прогон архива (Sprint B). Roadmap и критерии готовности в `tasks.md`. |
| WS-011 | Windows: CUDA для faster-whisper — `nvidia-cublas-cu12` + PATH в скрипте | Done | 2026-03-30 | 2026-03-30 | `requirements.txt`, `transcribe_to_obsidian.py`, `SETUP.md` п. 2.3 |
| WS-012 | Пайплайн после транскрибации: фаза B (текст, категории), документация + vault | In Progress | 2026-03-30 | | Roadmap + критерии готовности в `tasks.md` (ревизия качества → инструкция в Obsidian → style examples → навигация). [WS-012] |
| WS-013 | ASR: предобработка ffmpeg + режим `--existing-asset` для повторной транскрипции из ассета | Done | 2026-04-01 | 2026-04-01 | `preprocess_for_asr.py`, `transcribe_to_obsidian.py`; 3 тестовых ассета — мало речи; winget FFmpeg упал (P:), использован ffmpeg из CHITUBOX |
| WS-014 | Windows: установка FFmpeg (Gyan.FFmpeg через winget, TEMP на C:) | Done | 2026-04-01 | 2026-04-01 | `ffmpeg` в PATH, `WinGet\Links\ffmpeg.exe` v8.1 |
| WS-015 | Phase B: прогон 11 asset-папок (`phase_b_processor`), публикация в `10_processed` | Done | 2026-04-01 | 2026-04-01 | Ollama `gemma3:1b` (RAM ~12.7 ГБ; qwen2.5 не влез / pull timeout); см. `parse_llm_json_response` в `phase_b_processor.py` |
| WS-016 | Диагностика LM Studio: окно запускается вне видимой области экрана | Done | 2026-04-13 | 2026-04-13 | Проверены процессы/логи; окно возвращено на основной экран через WinAPI (координаты 2157→120) |
| WS-017 | Phase B OpenAI: убрать `response_format: json_object` для LM Studio (только json_schema/text) | Done | 2026-04-13 | 2026-04-13 | `phase_b_processor.py`; полный `--recursive` на LM Studio дал `timed out` на [1/2] (900 с) — сервер/модель медленные; повторить с `--timeout-sec 1800+` при стабильном LM Studio |
| WS-018 | Интеграция записей с телефона через Google Drive в общий пайплайн обработки | Done | 2026-04-14 | 2026-04-14 | `transcription/ingest_phone_recordings.py`, README/SETUP; импорт с дедупликацией + опциональный запуск Phase A |
| WS-019 | Старт мультиагентного прогона: preflight и определение контекста нового/текущего run | Open | 2026-04-15 | | MAS: pending решение пользователя (продолжить текущий run или стартовать новый) |
| WS-020 | Реальный прогон phone-ingest (вариант из облака) в `recordings` | Done | 2026-04-15 | 2026-04-15 | `ingest_phone_recordings.py --source-dir \"D:\\1 ЗАПИСИ ГОЛОС\\1 Диктофон_\" --recordings-dir \"D:\\1 ЗАПИСИ ГОЛОС\\recordings\" --recursive --copy`; импортировано 1304, пропущено 0, manifest: `phone_ingest_manifest.csv` |
| WS-021 | Phase B по новому skill `phase-b-process` + сравнение с предыдущей версией | Done | 2026-04-15 | 2026-04-15 | Подтянут `.cursor/skills/phase-b-process/SKILL.md` из `origin/curs/cloud-asr-api-2f61`; переработан asset `2017-01-26...`: обновлены `02_clean__review.md`, `03_content__article.md`, `meta.json` (`llm_backend=cursor`, `needs_review=true`) |
| WS-022 | Закрепление единого Phase B (Kimi) + лимитный батчинг транскрибации | Done | 2026-04-15 | 2026-04-15 | Обновлены skill/rules/docs, `phase_b_processor.py` переведён в deprecated-mode, добавлены `transcription_limit_dispatcher.py` и `transcription/FREE_LIMITS.md` |
| WS-023 | Наведение порядка в `00_inbox` + категории `junk`/`unclear` | Done | 2026-04-16 | 2026-04-16 | В `00_inbox` оставлен только `README.md`, 16 обработанных заметок перемещены в `_archive_processed/2026-04-16`; проблемные ранние ассеты переложены в `junk/unclear` и синхронизированы в `10_processed` |
| WS-024 | Финальная чистка по правилам: `00_inbox` как очередь, `10_processed` как результат | Done | 2026-04-16 | 2026-04-16 | Удалены обработанные `.md` из `00_inbox` (оставлен `README.md`), пересобрана публикация из asset `phase=B` в `10_processed/<category>`, удалён лишний backup-артефакт `compare-before-*` |

<!-- Новая задача: скопируй строку шаблона ниже, присвой следующий WS-NNN. -->

<!--
| WS-NNN | Краткое название | Open | YYYY-MM-DD | | |
-->
