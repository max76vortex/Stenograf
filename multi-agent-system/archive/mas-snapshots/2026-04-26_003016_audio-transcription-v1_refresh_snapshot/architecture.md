# Architecture

## Task Reference

- **Source TZ:** `multi-agent-system/current-run/technical_specification.md` (v1.1)
- **Objective:** Локальный конвейер mp3 → Markdown в Obsidian `00_inbox` с предсказуемыми именами и идемпотентностью.

## Overview

Однопользовательская система на Windows: CLI- или GUI-запуск Python-скрипта, библиотека faster-whisper (CTranslate2), файловый вывод в каталог vault. Без сервера, без БД, без внешних API для распознавания.

```text
[Папка mp3] → transcribe_to_obsidian.py → [WhisperModel large-v3] → [.md в 00_inbox]
                     ↑
              check_coverage.py (сравнение имён)
              transcribe_gui.py (subprocess → тот же CLI)
```

## Functional Components

### transcribe_to_obsidian.py

- **Purpose:** Основной конвейер: обход mp3, транскрибация, сборка frontmatter + «Транскрипт».
- **Functions:** `slug`, `date_from_path`, `build_md`, цикл по файлам, опции CLI.
- **Related use cases:** UC-02–05, UC-07.
- **Dependencies:** faster-whisper, torch/ctranslate2 (транзитивно), локальные пути.

### check_coverage.py

- **Purpose:** Отчёт «какие mp3 ещё без ожидаемого .md».
- **Functions:** Та же логика имён, что и у основного скрипта (дублирование `slug` — известный техдолг).
- **Related use cases:** UC-04.
- **Dependencies:** только stdlib.

### transcribe_gui.py

- **Purpose:** Обёртка tkinter: выбор каталогов, флаги, лог stdout/stderr.
- **Related use cases:** UC-06.
- **Dependencies:** stdlib, subprocess вызов `transcribe_to_obsidian.py`.

### Документация

- **README.md**, **SETUP.md**, **transcribe_month.bat** — установка и примеры.

## Data Model

### Файл транскрипта (.md)

- **Description:** Заметка Obsidian в `00_inbox`.
- **Fields (frontmatter):** `type: transcript`, `source: audio`, `audio_file`, `date`, `status: inbox`, `tags`, `links`.
- **Body:** секции «Заголовок», «Краткое резюме», «Транскрипт».
- **Relations:** `audio_file` = basename исходного mp3; при `--recursive` имя .md кодирует относительный путь для уникальности.

### Исходный mp3

- **Constraints:** рекомендуемый шаблон имени `YYYY-MM-DD_NNN[_метка].mp3`; путь задаёт пользователь.

## Interfaces

### Internal (процесс)

- **CLI:** `python transcribe_to_obsidian.py <input_dir> <output_dir> [options]`
- **GUI:** `python transcribe_gui.py` → `subprocess` с тем же интерпрейсом.

### External

- Нет HTTP API. Выход — только файловая система.

## Security

- Локальная обработка; секреты не требуются. Vault и пути на диске пользователя.

## Deployment And Migration

- **Environment:** venv в `transcription/.venv`; CUDA опционально.
- **Migration:** не применимо; обновление скрипта = замена файлов в репозитории.

## Open Questions

- Вынести `slug` / ожидаемое имя `.md` в общий модуль для синхронизации с `check_coverage.py` (опционально).
- Поддержка wav/m4a (опционально).
