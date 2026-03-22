# Development Plan

## Task Reference

- TZ: `multi-agent-system/current-run/technical_specification.md`
- Architecture: `multi-agent-system/current-run/architecture.md`
- Task brief: `multi-agent-system/current-run/task_brief.md`
- Real E2E control task: `multi-agent-system/current-run/tasks/task_06.md` (meta-stage after delivery)

## Goal

Завершить служебную точку входа (CLI) для dry run: полный вывод статуса процесса по ТЗ, блокирующие вопросы, последние артефакты активного прогона — без тяжёлой инфраструктуры и без изменений контура n8n.

## Decision (из архитектуры)

- **Поставка:** PowerShell CLI `multi-agent-system/tools/dryrun-status.ps1` + модуль `dryrun-status.internal.psm1`.
- **Источники:** `multi-agent-system/status.md`, `multi-agent-system/current-run/open_questions.md`, рекурсивно `multi-agent-system/current-run/**/*.md`.

## Текущее состояние (инвентаризация)

| Компонент | Состояние |
| --- | --- |
| Чтение `## System State` (Variant, Status, stage, iteration, active task, last updated) | Реализовано в модуле |
| Чтение блокеров из `open_questions.md` + fallback `## Open Questions Summary` | Реализовано |
| Список последних `.md` по mtime под `current-run/` | Реализовано |
| **Next expected step**, **подтверждённые пользователем этапы** (ТЗ § FR1) | Не выводятся в отчёт; парсинг секций неполный |
| Исключение служебных `README.md` из артефактов (архитектура) | Не реализовано |
| Корректность путей при `-CurrentRunDirectoryOverride` (тесты task_04) | Требует проверки/исправления |
| `dryrun-status.ps1`: двойной вызов `Build-StatusSurfaceReport` | Дефект (лишний вызов без overrides) |
| Имена параметров в архитектуре (`-Limit`, `-RunPath`) vs скрипт (`-Top`, overrides) | Расхождение документации и кода |

## Целевое состояние (критерии приёмки ТЗ)

1. Одна команда из корня workspace даёт три блока: **System Status** (включая next step и подтверждённые этапы), **Blocking Questions**, **Latest Artifacts**.
2. Данные из markdown-файлов, не захардкожены.
3. Устойчивость к отсутствию опциональных секций/файлов.
4. Существующие workflow не ломаются.

## Execution Stages

### Stage 1 — Модель статуса и вывод

- Расширить модель/парсинг `status.md`: секции `## Orchestrator Step State` (минимум `Next expected step`), `## Confirmed By User` (список отмеченных этапов).
- Обновить форматирование отчёта в `dryrun-status.ps1`.

### Stage 2 — Артефакты

- Исключить `README.md` при обходе; исправить вычисление относительного пути при override каталога прогона.
- Опционально: поле категории (`tasks/`, `reviews/`, `reports/`, корень) для строки вывода.

### Stage 3 — CLI и надёжность

- Убрать дублирующий вызов сборки отчёта; зафиксировать exit code (0 при успешном выводе, 1 при фатальной ошибке импорта/чтения обязательных путей — по согласованию с тестами).
- Синхронизировать документацию параметров (алиасы `-Limit`/`-Top` или единое имя в runbook).

### Stage 4 — Тесты и документация

- Расширить `tools/task_04_tests.ps1` (или аналог) сценариями для новых полей и README exclusion.
- Обновить `runbooks/status-surface-runbook.md` и при необходимости `multi-agent-system/README.md`.

## Tasks

| ID | Кратко | Зависимости | Файл |
| --- | --- | --- | --- |
| Task 01 | Парсинг и вывод: next step + confirmed stages | — | `tasks/task_01.md` |
| Task 02 | Артефакты: README exclusion + fix override paths | — (можно параллельно с 01 после договорённости по API модуля) | `tasks/task_02.md` |
| Task 03 | CLI: убрать двойной Build, exit codes, параметры | 01–02 по желанию (логически после стабилизации модуля) | `tasks/task_03.md` |
| Task 04 | Автотесты smoke | 01–03 | `tasks/task_04.md` |
| Task 05 | Документация runbook/README | 01–04 | `tasks/task_05.md` |
| Task 06 | Реальный E2E dry run оркестратора | После закрытия 01–05; вне scope поставки CLI по ТЗ | `tasks/task_06.md` |

### Coordination Rule (Task 01/02 parallel)

- До старта параллельной работы согласовать публичный контракт `dryrun-status.internal.psm1`: имена экспортируемых функций и формат путей в сценариях `-CurrentRunDirectoryOverride`.
- Merge order: сначала изменения, не затрагивающие сигнатуры, затем объединение правок по общему API модуля.

## Use Case Coverage

| Use Case | Tasks |
| --- | --- |
| UC-1: Просмотр полного статуса процесса | 01, 03, 04, 05 |
| UC-2: Проверка блокеров | 04 (явный assert по FR2), 05 |
| UC-3: Список последних артефактов прогона | 02, 04, 05 |

## Риски (сводка)

| Риск | Вероятность | Влияние | Митигация |
| --- | --- | --- | --- |
| Разный markdown в `status.md` | Средняя | Среднее | Толерантный парсинг, UNKNOWN/fallback, тесты на частичные секции |
| Регресс путей при override | Средняя | Высокое | Явные тесты в task_04 |
| Дублирование логики вывода | Низкая | Низкое | Один путь сборки отчёта в task_03 |

## Definition of Done (весь план)

- [ ] Все task-файлы выполнены или отменены с причиной.
- [ ] `pwsh -File multi-agent-system/tools/dryrun-status.ps1` отражает ТЗ и проходит smoke-тесты.
- [ ] Runbook обновлён; нет расхождений с фактическим поведением без пометки.
