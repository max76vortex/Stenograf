---
name: user.mb.activity-report
description: >-
  Builds an activity report for the N8N-projects workspace on demand by reading
  memory-bank/activity-journal.md (ISO timestamps, Manual/GitCommit/Scheduled sources),
  optional git log, and memory-bank/progress.md. Use when the user asks what was done today,
  за период, отчёт по работам, хронология, журнал активности, or to correlate tasks with time.
---

# Отчёт по активности workspace (по запросу)

Это **не** фоновый мониторинг: данные собираются **в момент запроса** из файлов и git — без постоянной нагрузки.

---

## Источники (по приоритету)

1. **`memory-bank/task-registry.md`** — таблица задач с ID **`WS-NNN`** и статусами (см. `task-tracking.md`).
2. **`memory-bank/activity-journal.md`** — строки с локальным ISO-временем и меткой `[Manual]` / `[GitCommit]` / `[Scheduled]`.
3. **`git log`** (если репозиторий инициализирован) — объективное время коммитов (ищи префиксы `WS-NNN:` в сообщениях).
4. **`memory-bank/progress.md`** — смысловые вехи; строки с **`[WS-NNN]`** сопоставляй с реестром.

Опционально пользователь запускает скрипт (быстрый снимок в консоль):

```powershell
pwsh -NoLogo -File "scripts/Get-ActivityReport.ps1" -SinceDays 7
```

---

## Как ответить пользователю

1. Прочитай **`memory-bank/activity-journal.md`** (хвост 50–100 строк или весь файл, если короткий).
2. При необходимости выполни **`git log --since=...`** (или предложи пользователю вывод `Get-ActivityReport.ps1`) за запрошенный период.
3. Сверь с **`memory-bank/progress.md`** для контекста «что за задачи», не дублируя всё дословно.
4. Сформируй ответ: **дата/период → краткий список действий**; укажи, что точное время коммитов — из git, ручные пометки — из журнала.

Если журнал пустой или его ещё не вели — честно скажи и опирайся на **git log** и **progress.md**.

---

## Как пополняется журнал

- Вручную: `pwsh -File scripts/append-activity-journal.ps1 -Message "..."` (см. `scripts/README.md`).
- После коммитов: при `git config core.hooksPath .githooks` — хук `.githooks/post-commit`.
- По расписанию: Task Scheduler + тот же скрипт с `-Source Scheduled`.

---

## Связанные пути

- `scripts/append-activity-journal.ps1`
- `scripts/Get-ActivityReport.ps1`
- `scripts/README.md`
- `memory-bank/activity-journal.md`
