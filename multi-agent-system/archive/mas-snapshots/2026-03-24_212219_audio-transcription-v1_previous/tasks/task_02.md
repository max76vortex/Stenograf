# Task 02: Артефакты — исключения README и корректные пути при override

## Goal

- Соответствие архитектуре и ТЗ: список «последних артефактов» строится по `current-run/**`, **без** служебных `README.md`, с корректными относительными путями при `-CurrentRunDirectoryOverride`.

## Related Use Cases

- UC-03: Список последних артефактов активного прогона.

## Changes

### New Files

- (нет)

### Existing Files

#### `multi-agent-system/tools/dryrun-status.internal.psm1`

- Change: в `Get-RunArtifactsFromCurrentRun` (или эквиваленте):
  - пропускать файлы с именем `README.md` (в любом подкаталоге);
  - при заданном `$CurrentRunDirectoryOverride` использовать его как корень обхода **и** как базу для относительного пути в поле вывода (исправить смещение, если override не совпадает с дефолтным `.../current-run`).
- Optional: добавить в модель `ArtifactEntry` поле `Category` (`task` | `review` | `report` | `core` | `other`) по префиксу пути для строки отчёта.
- Expected behavior: top-N по mtime (убывание), tie-break по пути; при пустом наборе — явное сообщение в отчёте.

#### `multi-agent-system/tools/dryrun-status.ps1`

- Change: при наличии категорий — вывести в строке артефакта (минимально, без ломания текста).

## Integration Notes

- Не индексировать вне `current-run` для этой фичи.
- Сохранить производительность на типичном дереве (без внешних БД).

## Test Cases

### End-To-End

1. Scenario: в тестовом каталоге есть `sub/README.md` и обычные `.md`.
   - Input: `-CurrentRunDirectoryOverride` на каталог фикстуры, `-Top 5`.
   - Expected result: `README.md` не в списке; остальные отсортированы по времени.

2. Scenario: override указывает на копию `current-run` с другим абсолютным путём.
   - Expected result: относительные пути в выводе согласованы с документированным форматом (`multi-agent-system/current-run/...` или согласованный префикс — зафиксировать в Task 03/05).

### Unit Tests

1. Scenario: имя файла `Readme.md` vs `README.md` на Windows.
   - Target: правило исключения (рекомендуется сравнение без учёта регистра для basename).

### Regression

- Existing tests to run: `multi-agent-system/tools/task_04_tests.ps1`.

## Acceptance Criteria

- [ ] README исключены из списка артефактов
- [ ] Override каталога не ломает относительные пути
- [ ] Tests passed
- [ ] Documentation updated (Task 05)

## Risks

| Риск | Уровень | Примечание |
| --- | --- | --- |
| Различие регистра имён на Windows | Средний | Явное правило сравнения basename |

## Estimate

- S: 0.5 дня.
