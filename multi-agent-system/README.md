# Multi-Agent System

Рабочая зона локальной мультиагентной системы варианта B.

Система рассчитана на поэтапную работу с подтверждением каждого крупного шага:

1. Аналитик
2. Ревьюер ТЗ
3. Архитектор
4. Ревьюер архитектуры
5. Планировщик
6. Ревьюер плана
7. Разработчик
8. Ревьюер кода

Оркестратор связывает эти роли и ведет `status.md`.

## Структура

```text
multi-agent-system/
├── README.md
├── status.md
├── run-agent.ps1
├── start-orchestrator.ps1
├── agents/                    # промпты ролей (оркестратор 01, роли 02–09)
├── current-run/
│   ├── README.md
│   ├── task_brief.md
│   ├── project_context.md
│   ├── open_questions.md
│   ├── technical_specification.md
│   ├── tz_review.md
│   ├── architecture.md
│   ├── architecture_review.md
│   ├── plan.md
│   ├── plan_review.md
│   ├── tasks/
│   ├── reviews/
│   └── reports/
├── templates/
│   ├── README.md
│   ├── technical_specification.template.md
│   ├── tz_review.template.md
│   ├── architecture.template.md
│   ├── architecture_review.template.md
│   ├── plan.template.md
│   ├── plan_review.template.md
│   ├── task.template.md
│   ├── test_report.template.md
│   └── open_questions.template.md
├── archive/
│   └── README.md
├── runbooks/
│   ├── operator-guide.md
│   ├── how-to-run-project-through-multi-agent-system.md
│   ├── mas-archive-policy.md
│   └── acceptance-checklists.md
└── examples/
    ├── README.md
    └── sample-task-brief.md
```

## Быстрый запуск

1. Подготовьте постановку задачи.
2. Ознакомьтесь с `multi-agent-system/agents/01_orchestrator.md`.
3. Откройте `runbooks/operator-guide.md`.
4. Обновите `current-run/` под новую задачу.
5. Запустите оркестратор с постановкой и контекстом проекта.

Для быстрого просмотра статуса активного прогона используйте:

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/dryrun-status.ps1" -Top 10
```

Перед запуском оркестратора (проверка `pwsh`, Cursor CLI, обязательных файлов):

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/orchestrator-preflight.ps1"
```

### Чистый старт для нового прогона (новый `MAS Project ID`)

После архивации завершённого прогона или чтобы сбросить `current-run/` и `status.md` под новую задачу:

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/mas-new-run.ps1" -MasProjectId "your-new-slug"
```

Скрипт по умолчанию делает снимок `current-run/` в `archive/mas-snapshots/`, затем очищает артефакты и пишет заготовки. Подробности: скилл **mas-clean-start** (`.cursor/skills/mas-clean-start/SKILL.md`). Просмотр без изменений: добавьте `-WhatIf -Force`.

Подробности по интерпретации отчета: `multi-agent-system/runbooks/status-surface-runbook.md`.

Запуск оркестратора (из корня workspace; по умолчанию читаются `current-run/task_brief.md` и `current-run/project_context.md`):

```powershell
.\multi-agent-system\start-orchestrator.ps1 -Model "auto"
```

Другие файлы постановки/контекста — параметры `-TaskFile` и `-ProjectContextFile`. Пример в `examples/sample-task-brief.md` — только шаблон для копирования в `current-run/task_brief.md`.

## Команды запуска

В зависимости от версии Cursor CLI используйте:

```powershell
agent -f --model <model> -p "<prompt>"
```

или

```powershell
cursor-agent -f --model <model> -p "<prompt>"
```

Если первая команда не найдена, проверьте вторую, и наоборот.

Также можно использовать PowerShell-обертку:

```powershell
.\multi-agent-system\run-agent.ps1 -PromptFile .\multi-agent-system\agents\02_analyst_prompt.md -Model <model> -ContextFile <context-file>
```

## Важные правила

- Каждый агент пишет только свои артефакты.
- Все блокирующие вопросы складываются в `current-run/open_questions.md`.
- После каждого этапа пользователь подтверждает результат перед переходом
  к следующему смысловому этапу.
