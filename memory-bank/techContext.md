# Tech Context

## Транскрибация аудио → Obsidian

- **Инструмент:** faster-whisper (Python), модель **large-v3** для максимального качества.
- **Железо:** GPU 6+ ГБ VRAM (RTX 3060), CUDA Toolkit, compute_type float16.
- **Скрипт:** `transcription/transcribe_to_obsidian.py` — папка .mp3 → папка .md с frontmatter под шаблон транскрипта vault (00_inbox).
- **Зависимости:** `transcription/requirements.txt` (faster-whisper).
- **Документация:** `transcription/README.md`, **установка на ПК:** `transcription/SETUP.md`.

### Где что на компьютере

- **Проект/скрипт:** `C:\Users\sa\N8N-projects\transcription\` (venv: `.venv`).
- **Записи mp3:** по желанию, например `D:\recordings\` с подпапками `YYYY-MM`.
- **Vault Audio Brain:** `D:\Obsidian\Audio Brain\`; выход транскриптов: `00_inbox\`.
- **Связь:** задаётся только в команде запуска (входная папка → скрипт → выходная папка 00_inbox). Подробно — в SETUP.md.

## Мультиагентная система

- **Промпты ролей:** `multi-agent-system/agents/` (в workspace: `N8N-projects/multi-agent-system/agents/`).
- **Рабочая зона системы:** `C:\Users\sa\N8N-projects\multi-agent-system\`.
- **Статус процесса:** `multi-agent-system/status.md`.
- **Активный прогон задачи:** `multi-agent-system/current-run/`.
- **Шаблоны артефактов:** `multi-agent-system/templates/`.
- **Runbook'и оператора:** `multi-agent-system/runbooks/`.
- **CLI-запуск:** ожидается Cursor CLI как `agent` или `cursor-agent`; на момент сборки комплекта команды в `PATH` не обнаружены, значит нужен отдельный install/setup шаг перед первым автономным прогоном.

