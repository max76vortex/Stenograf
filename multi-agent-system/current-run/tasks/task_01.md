# Task 01: Расширенный статус из status.md (next step + confirmed stages)

## Goal

- Закрыть **FR1** ТЗ: в отчёт CLI попадают глобальный статус, стадия, итерация, **следующий ожидаемый шаг** и **список подтверждённых пользователем этапов**, читаемые из `multi-agent-system/status.md`.

## Related Use Cases

- UC-01: Просмотр полного статуса процесса dry run.

## Changes

### New Files

- (нет обязательных новых файлов; при выделении парсеров — опционально мелкие хелперы в том же `.psm1`)

### Existing Files

#### `multi-agent-system/tools/dryrun-status.internal.psm1`

- Change: расширить модель (например поля `NextExpectedStep`, `ConfirmedStages` / строковый массив) и функции парсинга:
  - из секции `## Orchestrator Step State` извлечь строку с `Next expected step` (или эквивалент по фактическому формату `status.md`);
  - из секции `## Confirmed By User` собрать отмеченные пункты (`- [x] ...`).
- New or updated symbols: `Get-SystemStateFromStatusFile` / новые хелперы секций; при необходимости обновить класс `SystemState`.
- Expected behavior: при отсутствии секций или ключей — диагностика + значения `UNKNOWN` / пустой список без падения.

#### `multi-agent-system/tools/dryrun-status.ps1`

- Change: вывести новые поля в блоке `--- System State ---` (или отдельным подблоком в том же разделе отчёта).
- Expected behavior: оператор видит next step и список подтверждений без чтения сырого markdown.

## Integration Notes

- Не менять формат `status.md` вручную ради задачи — только читать существующую структуру.
- Сохранить совместимость с текущими полями `System State`.

## Test Cases

### End-To-End

1. Scenario: полный `status.md` как в репозитории.
   - Input: запуск `dryrun-status.ps1` с путями по умолчанию.
   - Expected result: в выводе присутствуют непустые next step и список подтверждённых этапов (согласно файлу).

2. Scenario: временный `status.md` без `## Orchestrator Step State`.
   - Input: `-StatusFilePathOverride` на фикстуру.
   - Expected result: скрипт завершается успешно; next step помечен как UNKNOWN или аналог; есть диагностика.

### Unit Tests

1. Scenario: парсинг `## Confirmed By User` с `[x]` и `[ ]`.
   - Target: функции парсинга в модуле (через dot-source или импорт в тестовом скрипте).
   - Expected result: только отмеченные `[x]` попадают в список.

### Regression

- Existing tests to run: `multi-agent-system/tools/task_04_tests.ps1` (после обновления под новый вывод — см. Task 04).

## Acceptance Criteria

- [ ] Implementation complete
- [ ] Next expected step и confirmed stages читаются из markdown, не захардкожены
- [ ] Tests passed (ручной smoke + существующий тестовый скрипт после правок)
- [ ] Documentation updated (Task 05 или ссылка на последующее обновление runbook)

## Risks

| Риск | Уровень | Примечание |
| --- | --- | --- |
| Секции переименованы в будущем | Низкий | Диагностика + UNKNOWN |

## Estimate

- S: 0.5–1 день.
