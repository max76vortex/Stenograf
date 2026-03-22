# Task 03: CLI — один путь сборки отчёта, exit codes, согласование параметров

## Goal

- Устранить дефект в `dryrun-status.ps1` (двойной вызов `Build-StatusSurfaceReport`), стабилизировать интерфейс и коды выхода согласно `architecture.md` и smoke-поведению.

## Related Use Cases

- UC-01–03: единый предсказуемый запуск команды.

## Changes

### New Files

- (нет)

### Existing Files

#### `multi-agent-system/tools/dryrun-status.ps1`

- Change:
  - оставить **один** вызов сборки отчёта с полным набором параметров (override’ы передаются всегда когда заданы);
  - определить политику exit code: `0` после успешного вывода отчёта; `1` при критических сбоях (например отсутствует обязательный модуль, невозможно прочитать обязательный `status.md` — уточнить минимальный контракт и зафиксировать в комментарии скрипта);
  - опционально: добавить алиасы параметров `-Limit` → `-Top`, `-RunPath` → `-CurrentRunDirectoryOverride`, `-StatusPath` → `-StatusFilePathOverride` для соответствия архитектурной документации **без** удаления старых имён.

## Integration Notes

- Не ломать существующие вызовы из runbook и `task_04_tests.ps1` (обратная совместимость имён параметров).

## Test Cases

### End-To-End

1. Scenario: запуск с overrides как в `task_04_tests.ps1`.
   - Expected result: один проход логики; вывод идентичен ожиданиям тестов после фикса.

2. Scenario: отсутствует `dryrun-status.internal.psm1` (временно переименовать в фикстуре).
   - Expected result: ненулевой exit code и понятное сообщение.

### Unit Tests

- (по необходимости) минимальная проверка разбора параметров.

### Regression

- `multi-agent-system/tools/task_04_tests.ps1` — все сценарии зелёные.

## Acceptance Criteria

- [ ] Нет дублирующего вызова `Build-StatusSurfaceReport`
- [ ] Exit codes документированы и покрыты хотя бы одним сценарием
- [ ] Обратная совместимость параметров сохранена
- [ ] Tests passed

## Risks

| Риск | Уровень | Примечание |
| --- | --- | --- |
| Смена семантики exit code ломает CI | Средний | Согласовать с существующим task_04 |

## Estimate

- XS: 2–4 часа.
