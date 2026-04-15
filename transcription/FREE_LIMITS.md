# Бесплатные лимиты и профиль батчей

## Что используем в проекте

- **Phase B (редактура текста):** skill `.cursor/skills/phase-b-process/SKILL.md`, модель `kimi-k2.5` в Cursor.
- **Phase A (распознавание аудио):** батч-диспетчер `transcription_limit_dispatcher.py`.

## Важный факт про Kimi API

У Kimi API нет вечного free-tier в классическом виде: для API нужен депозит (минимум $1), дальше лимиты зависят от tier/recharge.

Источник: `https://platform.kimi.ai/docs/pricing/limits`

## Бесплатный профиль для транскрибации (по умолчанию)

В `transcription_limit_dispatcher.py` по умолчанию задан профиль **Groq Whisper Free**:

- `requests_per_window = 20`
- `window_seconds = 60`
- `requests_per_day = 2000`
- `audio_seconds_per_window = 7200`
- `audio_seconds_per_day = 28800`
- `max_file_mb = 25`

Источник: `https://console.groq.com/docs/rate-limits`

## Как работает автоочередь

- Скрипт берёт pending-файлы из `recordings/` (то, чего нет в manifest).
- Формирует партию в пределах текущего окна и дневного лимита.
- После исчерпания лимита засыпает до reset.
- В режиме `--watch` сразу продолжает, когда открывается следующее окно лимита.

## Базовый запуск

```powershell
python transcription_limit_dispatcher.py `
  --input-dir "D:\1 ЗАПИСИ ГОЛОС\recordings" `
  --output-dir "D:\Obsidian\Audio Brain\00_inbox" `
  --manifest "D:\1 ЗАПИСИ ГОЛОС\recordings\manifest.csv" `
  --asset-root "D:\1 ЗАПИСИ ГОЛОС\audio-work" `
  --recursive `
  --watch
```
