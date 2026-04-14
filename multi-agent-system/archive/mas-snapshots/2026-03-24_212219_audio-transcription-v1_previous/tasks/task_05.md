# Task 05: Документация — runbook, README, согласованность с планом

## Goal

- Обновить операторскую документацию после реализации Tasks 01–04: как читать новые поля статуса, правила артефактов, параметры CLI и exit codes.

## Related Use Cases

- Все UC; сопровождение dry run оператором.

## Changes

### New Files

- (нет обязательных)

### Existing Files

#### `multi-agent-system/runbooks/status-surface-runbook.md`

- Change: описать блоки отчёта с учётом **Next expected step** и **Confirmed stages**; уточнить исключение `README.md` из Last Artifacts; зафиксировать параметры (`-Top` / `-Limit`, override’ы), exit codes.

#### `multi-agent-system/README.md`

- Change: краткая ссылка на команду статуса и runbook (если раздел уже есть — дополнить).

## Integration Notes

- Не дублировать полный текст ТЗ — только операционные инструкции.
- Язык: согласовать с существующими runbook (RU/EN — как в `status-surface-runbook.md`).

## Test Cases

### End-To-End

1. Scenario: новый оператор следует только runbook и запускает команду.
   - Expected result: успешный просмотр статуса без чтения исходников.

### Unit Tests

- Не применимо.

### Regression

- Проверка вручную: команда из runbook копипастой работает.

## Acceptance Criteria

- [ ] Runbook отражает фактическое поведение CLI
- [ ] Параметры и коды выхода согласованы с `dryrun-status.ps1`
- [ ] README обновлён при необходимости

## Risks

| Риск | Уровень | Примечание |
| --- | --- | --- |
| Устаревание при следующем рефакторинге | Низкий | Ссылка на версию/дату внизу runbook |

## Estimate

- XS: 1–2 часа.
