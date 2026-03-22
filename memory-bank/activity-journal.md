# Activity journal

Краткий лог для отчётов по запросу (агент/человек). Формат: локальное ISO-время, источник, текст.

- Ручная запись: `pwsh -File scripts/append-activity-journal.ps1 -Message "..."`
- После коммитов: `git config core.hooksPath .githooks` и хук `post-commit` (см. `scripts/README.md`)
- Отчёт: скилл **workspace-activity-report** или `pwsh -File scripts/Get-ActivityReport.ps1`

## Entries

- `2026-03-22T21:47:44.940+03:00` [Manual] Инициализация журнала: скрипты append/Get, skill workspace-activity-report, .githooks/post-commit
- `2026-03-22T21:56:26.860+03:00` [Manual] WS-002: единая схема учёта задач (task-tracking, registry, cursor rule)
- `2026-03-22T22:18:09.342+03:00` [Manual] WS-003: memory-bank-init skill, bootstrap/, global memory-bank.mdc extension
