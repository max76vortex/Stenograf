# Project Context

**MAS Project ID:** `audio-transcription-v1`

## Workspace

- Name: N8N-projects (локальный репозиторий Cursor)
- Repository root: `C:\Users\sa\N8N-projects`

## Описание проекта

Пользователь накопил большой объём аудиозаписей с диктофона (идеи, проекты, размышления). Нужен **устойчивый локальный пайплайн**: mp3 → текст → заметки в отдельном vault Obsidian (**Audio Brain**), без смешивания с остальными делами. Качество транскрибации — максимально доступное на домашнем ПК (faster-whisper **large-v3**, GPU). Постинг в блог/Ghost вынесен в **отдельную фазу** после появления готовых к публикации материалов.

## Стек и ограничения

- **Транскрибация:** Python 3.10+, `faster-whisper`, модель `large-v3`, `compute_type=float16`, `device=cuda` (или `cpu`).
- **Obsidian:** vault `D:\Obsidian\Audio Brain\`; транскрипты пишутся в `00_inbox\`; шаблоны в `20_system/templates\`; инструкция по синку с Ghost — на будущее, не в scope текущего прогона.
- **Связь с репозиторием:** код и документация в `transcription/`; Memory Bank в `memory-bank/` (tasks, creative, techContext, progress).

## Структура репозитория (важное от корня)

| Путь | Назначение |
|------|------------|
| `transcription/transcribe_to_obsidian.py` | Основной скрипт: папка mp3 → папка .md |
| `transcription/check_coverage.py` | Проверка: какие mp3 ещё без ожидаемого .md |
| `transcription/requirements.txt` | Зависимость faster-whisper |
| `transcription/README.md` | Порядок имён, примеры команд |
| `transcription/SETUP.md` | Полная установка на ПК (драйвер, CUDA, Python, venv) |
| `transcription/transcribe_month.bat` | Пример bat с путями (подправить под себя) |
| `memory-bank/tasks.md` | План: Phase 1 транскрибация, Phase 2 постинг |
| `memory-bank/creative/creative-transcription-workflow.md` | Дизайн порядка в папке записей и в 00_inbox |
| `memory-bank/creative/creative-content-pipeline-and-ghost.md` | Ghost/Obsidian (фаза 2, справочно) |
| `memory-bank/techContext.md` | Краткий техконтекст транскрибации |
| `multi-agent-system/` | MAS: статус, current-run, агенты, runbooks |

## Папки на компьютере пользователя (примеры)

- Записи: `D:\1 ЗАПИСИ ГОЛОС\recordings\` с подпапками `YYYY-MM\`, имена mp3: `YYYY-MM-DD_NNN[_метка].mp3`.
- Vault: `D:\Obsidian\Audio Brain\`, выход транскриптов: `00_inbox\`.

## Ссылки

- Промпты ролей: `multi-agent-system/agents/`
- Глобальный статус: `multi-agent-system/status.md`
- Артефакты прогона: `multi-agent-system/current-run/`
- Снимок предыдущего прогона MAS: `multi-agent-system/archive/mas-snapshots/2026-03-24_212219_audio-transcription-v1_previous/`

## Правило slug для будущих прогонов MAS

Для новых чистых стартов **`MasProjectId`** выбирается по смыслу задачи (kebab-case), например `audio-transcription-v1`, `ghost-sync-v2`; не использовать произвольные бессмысленные строки.

## Delta execution mode (2026-04-26)

- Оркестрация выполняется поверх текущего run `audio-transcription-v1` (без `mas-new-run`).
- Потоки разделены:
  - **Core/MAS Delivery (Worktree 1):** основной delivery в этом контуре.
  - **ASR R&D (Worktree 2):** отдельный параллельный контур с benchmark-валидацией ASR.
- Контракт между потоками:
  - Worktree 2 поставляет измеренные результаты и decision package.
  - Worktree 1 принимает изменения ASR только через зафиксированный интерфейс и обновлённый benchmark decision.
