# Operator Guide

## Цель

Этот runbook описывает, как запускать мультиагентную систему варианта B в
ручном, но структурированном режиме.

## Подготовка

1. Описать постановку задачи.
2. Собрать краткое описание проекта или ссылки на нужные файлы.
3. Проверить, что папка `multi-agent-system/current-run/` готова под новую задачу.
4. Выбрать модель для оркестратора и субагентов.
5. Проверить наличие Cursor CLI по инструкции из `prerequisites.md`.

## Рекомендуемый порядок работы

1. Открыть `multi-agent-system/agents/01_orchestrator.md`.
2. Передать оркестратору:
   - постановку задачи;
   - описание проекта;
   - указание использовать артефакты из `multi-agent-system/current-run/`.
3. Оркестратор запускает или имитирует запуск следующей роли через Cursor CLI.
4. После завершения этапа оператор подтверждает результат.
5. Только потом процесс идет к следующему этапу.

Запуск через обёртку из **корня workspace** (по умолчанию: `multi-agent-system/current-run/task_brief.md` и при наличии — `project_context.md`):

```powershell
.\multi-agent-system\start-orchestrator.ps1 -Model "<model>"
```

Иные пути к файлам:

```powershell
.\multi-agent-system\start-orchestrator.ps1 `
  -TaskFile "multi-agent-system/current-run/task_brief.md" `
  -ProjectContextFile "multi-agent-system/current-run/project_context.md" `
  -Model "<model>"
```

## Шаблон стартового промпта

```text
Используй процесс из `multi-agent-system/agents/01_orchestrator.md`.

Постановка задачи:
<вставить постановку>

Описание проекта:
<вставить краткое описание или ссылки на файлы>

Все артефакты активной задачи сохраняй в `multi-agent-system/current-run/`.
После каждого этапа обновляй `multi-agent-system/status.md` и останавливайся на
моё подтверждение перед переходом к следующему крупному этапу.

Промпты ролей бери из папки `multi-agent-system/agents/`.
Если для запуска доступен Cursor CLI, используй `agent` или `cursor-agent`.
```

## Шаблон CLI-команды

```powershell
agent -f --model <model> -p "<содержимое_prompt_файла> <контекст>"
```

Альтернатива:

```powershell
cursor-agent -f --model <model> -p "<содержимое_prompt_файла> <контекст>"
```

Обертка для произвольной роли:

```powershell
.\multi-agent-system\run-agent.ps1 -PromptFile .\multi-agent-system\agents\02_analyst_prompt.md -Model <model> -ContextFile <context-file>
```

## Когда останавливать процесс

- Есть блокирующие вопросы.
- После завершения крупного этапа нужен пользовательский акцепт.
- Превышен лимит review-итераций.
- Агент не создал обязательный артефакт.
