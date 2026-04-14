# Task 01: Окружение и smoke-тест транскрибации

## Goal

Убедиться, что на машине поднимается Python-окружение с faster-whisper и что конвейер mp3 → `00_inbox` работает на 1–2 тестовых файлах.

## Related Use Cases

- UC-01 (установка), UC-02 (одна папка), UC-04 (check_coverage).

## Steps (исполнитель: пользователь + опционально `run-smoke-test.ps1`)

1. Открыть PowerShell, перейти в `C:\Users\sa\N8N-projects\transcription`.
2. `python -m venv .venv` (если ещё нет).
3. `.\.venv\Scripts\Activate.ps1`
4. `pip install -r requirements.txt`
5. `python transcribe_to_obsidian.py --help` — без ошибок импорта.
6. `python check_coverage.py --help` — без ошибок.
7. Создать тестовую папку с 1–2 короткими mp3 (или скопировать из архива).
8. Запустить:  
   `python transcribe_to_obsidian.py "<путь_к_тестовым_mp3>" "D:\Obsidian\Audio Brain\00_inbox"`  
   (путь к vault подставить свой, если другой).
9. Проверить в Obsidian появление заметок и поле `audio_file` во frontmatter.
10. `python check_coverage.py "<путь_к_тестовым_mp3>" "D:\Obsidian\Audio Brain\00_inbox"`

## Acceptance Criteria

- [x] Шаги 5–6 проходят (`run-smoke-test.ps1` + ручной `--help`).
- [x] После шага 8 в `00_inbox` есть `.md` с текстом транскрипта (автопрогон 2026-03-30: тестовый WAV в `transcription/test_smoke/` → `D:\Obsidian\Audio Brain\00_inbox`, для скорости `--model tiny --device cpu --ext .wav`; боевая схема: `large-v3` + `cuda` + `.mp3`).
- [x] `check_coverage.py` не показывает MISSING для тестовых файлов.

## Notes

- Первый полный прогон с загрузкой модели large-v3 может занять время и трафик; для `--help` модель не качается.
- Если CUDA не установлена, для smoke можно временно `--device cpu` (медленнее).

## Status

- [ ] Not started
- [ ] In progress
- [x] Done (smoke в vault подтверждён агентом; массовый прогон — `task_02.md`)
