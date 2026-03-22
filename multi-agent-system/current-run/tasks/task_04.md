# Task 04: Расширенные smoke-тесты для dryrun-status

## Goal

- Покрыть сценарии из архитектуры (Test Strategy): полные данные, нет блокеров, частичный `status.md`, отсутствие подкаталогов артефактов; добавить проверки для Task 01–03.

## Related Use Cases

- Регрессия UC-01–03.

## Changes

### New Files

- Опционально: фикстуры markdown под `multi-agent-system/current-run/tmp_*` (как в существующем `task_04_tests.ps1`) — не коммитить временные каталоги, создавать в рантайме теста.

### Existing Files

#### `multi-agent-system/tools/task_04_tests.ps1`

- Change:
  - добавить assert’ы на новые строки вывода (next step, confirmed stages);
  - добавить явный assert по FR2: наличие/отсутствие блокеров из `open_questions.md` в ожидаемых сценариях;
  - сценарий с `README.md` в подкаталоге — не должен попадать в топ;
  - сценарий с `-CurrentRunDirectoryOverride` — проверка префикса путей;
  - при необходимости обновить эталонные подстроки после изменения формата отчёта.

## Integration Notes

- Запуск: `pwsh -File multi-agent-system/tools/task_04_tests.ps1` из корня workspace (как принято в проекте).
- Не требовать сети или внешних сервисов.

## Test Cases

### End-To-End

1. Scenario: «все файлы на месте» — см. architecture Test Strategy scenario 1.
2. Scenario: `open_questions.md` с маркером «no open questions» — scenario 2.
3. Scenario: урезанный `status.md` — scenario 3.
4. Scenario: нет вложенных каталогов с артефактами — scenario 4.
5. Scenario (new): подтверждённые этапы и next step присутствуют в stdout.

### Unit Tests

- Не обязательны, если покрыто интеграционным скриптом.

### Regression

- Полный прогон `task_04_tests.ps1` до зелёного состояния.

## Acceptance Criteria

- [ ] Все сценарии из архитектуры представлены или явно помечены как неприменимые
- [ ] Новые поля статуса проверяются
- [ ] README exclusion и override проверены
- [ ] Скрипт тестов завершается с ненулевым кодом при первом падении assert

## Risks

| Риск | Уровень | Примечание |
| --- | --- | --- |
| Хрупкие строковые assert’ы | Средний | Выносить ключевые фразы в константы внутри теста |

## Estimate

- S: 0.5 дня.
