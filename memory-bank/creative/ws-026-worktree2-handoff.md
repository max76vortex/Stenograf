# WS-026 Worktree 2 Handoff (ASR R&D)

## Контекст

- Поток: **Worktree 2 (ASR R&D)**.
- Задача: `WS-026` (Nexara measured validation).
- Режим: только benchmark/ASR-документация, без изменений Core/MAS delivery.
- Дата обновления: `2026-04-26`.

## Что запущено

1. Проверены артефакты:
   - `transcription/asr-benchmark/results.csv`
   - `transcription/asr-benchmark/decision.md`
   - `transcription/asr-benchmark/runs/*nexara*`
2. Подготовлен следующий measured run на длинном noisy файле:
   - target file: `D:\1 ЗАПИСИ ГОЛОС\recordings\2012-10\2012-10-29_001_DW_A0414.wav`
   - planned `file_id`: `ru-gs-16`
3. Выполнена попытка реального запуска `run_nexara_smoke.py`.

## Measured outcomes

- Новый measured-транскрипт **не получен** (run не стартовал до HTTP-запроса).
- Технический результат попытки:
  - `run_nexara_smoke.py` завершился с ошибкой:
    - `NEXARA_API_KEY environment variable is required`
- Это не simulated-результат и не оценка качества модели; это preflight blocker среды выполнения.

## Blocker status

- **Blocker A (env):** отсутствует `NEXARA_API_KEY` в текущей сессии/окружении Worktree 2.
- **Blocker B (billing risk):** ранее зафиксирован `HTTP 402 insufficient balance` (см. `ru-gs-15`), поэтому даже после восстановления ключа нужен контроль баланса перед повтором.

## Core handoff gate

- Core/MAS Delivery принимает ASR-изменения только через gate: `transcription/asr-benchmark/CORE_GATE.md`.
- До свежего approved decision package для точного provider/profile Core default остаётся `faster-whisper-local`.
- Текущий Nexara handoff является R&D/provisional и не разрешает переключение Core default.

## Exact next commands (rerun pack)

### 1) Проверка ключа в текущей PowerShell-сессии

```powershell
if ([string]::IsNullOrWhiteSpace($env:NEXARA_API_KEY)) { "EMPTY" } else { "SET" }
```

### 2) Установить ключ (текущая сессия)

```powershell
$env:NEXARA_API_KEY = "<YOUR_NEXARA_API_KEY>"
```

### 3) Re-run measured (длинный noisy)

```powershell
python "transcription/asr-benchmark/run_nexara_smoke.py" `
  --audio "D:\1 ЗАПИСИ ГОЛОС\recordings\2012-10\2012-10-29_001_DW_A0414.wav" `
  --file-id "ru-gs-16" `
  --noise "high"
```

### 4) Быстрый пост-check run-артефактов

```powershell
Get-ChildItem "transcription/asr-benchmark/runs" -Filter "ru-gs-16-nexara-*.json" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 FullName,LastWriteTime
```

### 5) Если снова `402`, зафиксировать blocker без потери истории

```powershell
Get-ChildItem "transcription/asr-benchmark/runs" -Filter "ru-gs-16-nexara-*.json" |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 -ExpandProperty FullName |
  ForEach-Object { rg "\"http_status\"|\"detail\"" $_ }
```

## Что обновить после успешного rerun

1. Добавить measured строку в `transcription/asr-benchmark/results.csv` (без удаления истории).
2. Обновить `transcription/asr-benchmark/decision.md`:
   - measured summary,
   - pass/fail impact на Nexara verdict.
3. В `memory-bank/progress.md` добавить запись с `[WS-026]`.
