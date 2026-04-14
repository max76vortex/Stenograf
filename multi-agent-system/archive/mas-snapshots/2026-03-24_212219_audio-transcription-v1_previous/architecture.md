# Architecture

## Task Reference

- Source TZ: `multi-agent-system/current-run/technical_specification.md`
- Objective: реализовать легковесную точку входа для отображения статуса dry run, блокирующих вопросов и последних артефактов активного прогона.

## Architectural Decision Summary

- Формат поставки: CLI-команда на PowerShell (`multi-agent-system/tools/dryrun-status.ps1`) без новой инфраструктуры.
- Границы решения: чтение только файлов из `multi-agent-system/status.md` и `multi-agent-system/current-run/`.
- Режим отказоустойчивости: толерантный парсинг markdown + fallback-значения при неполных секциях.
- Критичное уточнение из TZ review: список артефактов строится только из `multi-agent-system/current-run/` (включая подкаталоги).

## Functional Components

### Status Reader

- Purpose: извлечь состояние процесса из `status.md`.
- Functions:
  - извлечение `Status`, `Current stage`, `Current iteration`;
  - извлечение `Next expected step` из секции `Orchestrator Step State`;
  - извлечение списка подтвержденных этапов из секции `Confirmed By User`.
- Dependencies: файловая система, markdown parser helpers.

### Open Questions Reader

- Purpose: определить наличие блокеров и вернуть их список.
- Functions:
  - чтение `current-run/open_questions.md`;
  - распознавание статуса "нет вопросов" и списка вопросов;
  - классификация наличия блокирующих вопросов (`true/false`).
- Dependencies: файловая система, markdown parser helpers.

### Artifacts Enumerator

- Purpose: показать последние созданные артефакты активного прогона.
- Functions:
  - рекурсивный обход `current-run/`;
  - исключение служебных файлов (`README.md` в каталогах);
  - сортировка по времени модификации (убывание);
  - возврат top-N (по умолчанию 10).
- Dependencies: файловая система.

### Output Formatter

- Purpose: вывести стабильный человекочитаемый отчет.
- Functions:
  - единый вывод блоков: `System Status`, `Open Questions`, `Latest Artifacts`;
  - понятные fallback-сообщения при отсутствии файлов/секций;
  - совместимость с терминалом без доп. модулей.
- Dependencies: PowerShell stdlib.

## System Components

### `multi-agent-system/tools/dryrun-status.ps1`

- Type: entry-point CLI script.
- Purpose: orchestration чтения, агрегации и вывода данных.
- Technology: PowerShell 5+/7+.
- Interfaces:
  - optional params: `-RunPath`, `-StatusPath`, `-Limit`;
  - stdout: форматированный текстовый отчет;
  - exit code: `0` для успешного чтения, `1` при критической ошибке.

### `multi-agent-system/tools/dryrun-status.internal.psm1`

- Type: internal module.
- Purpose: изолировать парсинг markdown и сбор артефактов.
- Technology: PowerShell module.
- Interfaces:
  - `Get-DryRunStatusModel`
  - `Get-DryRunOpenQuestionsModel`
  - `Get-DryRunLatestArtifacts`
  - `Format-DryRunReport`

## Data Model

### DryRunStatusModel

- Description: агрегированная модель состояния процесса.
- Fields:
  - `overallStatus` (string)
  - `currentStage` (string)
  - `currentIteration` (string)
  - `nextExpectedStep` (string)
  - `confirmedStages` (string[])
- Constraints: отсутствующие поля заменяются на `"UNKNOWN"` или `[]`.

### OpenQuestionsModel

- Description: модель блокирующих вопросов.
- Fields:
  - `hasBlockingQuestions` (bool)
  - `questions` (string[])
- Constraints: если файл отсутствует/пустой, возвращается `false` и пустой список.

### ArtifactItem

- Description: один артефакт активного прогона.
- Fields:
  - `path` (string, relative to `current-run/`)
  - `lastWriteTime` (datetime)
  - `category` (enum: `task|review|report|core|other`)
- Constraints: в выдачу не попадают служебные `README.md`.

## Interfaces

### CLI Interface

- Endpoint or protocol: локальный запуск PowerShell-скрипта.
- Input:
  - `-StatusPath` (default `multi-agent-system/status.md`)
  - `-RunPath` (default `multi-agent-system/current-run`)
  - `-Limit` (default `10`)
- Output: текстовый отчет по 3 обязательным блокам.
- Errors:
  - missing required file (`status.md`) -> ошибка с actionable message;
  - parse mismatch -> warning + fallback значения.

### Internal Parsing Contract

- Producer: `status.md`, `open_questions.md`, файлы `current-run/`.
- Consumer: `dryrun-status.internal.psm1`.
- Contract:
  - `status.md` содержит секции `System State`, `Confirmed By User`, `Orchestrator Step State`;
  - `open_questions.md` содержит секцию `Status` и/или маркированный список вопросов;
  - latest artifacts вычисляются по mtime, scope = `current-run/**`.

## Security

- Authentication: не требуется (локальная служебная команда).
- Authorization: права текущего локального пользователя к файлам workspace.
- Data protection: чтение локальных markdown без передачи наружу.

## Deployment And Migration

- Environments: локальная dev-среда в workspace.
- Config changes: не требуются.
- Migration steps:
  - добавить/обновить `dryrun-status.ps1` и внутренний модуль;
  - выполнить smoke-run с дефолтными путями;
  - проверить сценарий с отсутствием одного из опциональных файлов.

## Test Strategy (Smoke)

- Scenario 1: все файлы присутствуют -> вывод всех блоков и списка top-N артефактов.
- Scenario 2: `open_questions.md` без вопросов -> `hasBlockingQuestions = false`.
- Scenario 3: отсутствует часть секций в `status.md` -> fallback-поля без падения скрипта.
- Scenario 4: нет подкаталогов `reviews/reports/tasks` -> вывод "артефакты не найдены" в блоке.

## Open Questions

- None
