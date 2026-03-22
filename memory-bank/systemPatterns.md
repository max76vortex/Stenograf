# System Patterns

## Учёт задач (весь workspace)

- Источник истины по списку задач с ID: **`memory-bank/task-registry.md`** (`WS-001` …).
- Правила, куда писать: **`memory-bank/task-tracking.md`** (реестр + `tasks.md` + `progress.md` + git + опционально `activity-journal.md`).

## Мультиагентная разработка

- В workspace контур MAS: каталог `multi-agent-system/` (промпты ролей в `multi-agent-system/agents/`, артефакты в `current-run/`).
- Работа идет по схеме оркестратор -> аналитик -> review ТЗ -> архитектор ->
  review архитектуры -> планировщик -> review плана -> разработчик -> review
  кода.
- Все артефакты активной задачи хранятся в
  `multi-agent-system/current-run/`.
- Глобальный статус процесса фиксируется в `multi-agent-system/status.md`.
- На варианте B после каждого крупного этапа требуется подтверждение
  пользователя, то есть система намеренно не делает полностью автономный
  autopilot.

