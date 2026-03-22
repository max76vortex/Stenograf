# Orchestrator Start Prompt

Используй процесс из `multi-agent-system/agents/01_orchestrator.md`.

Постановка задачи:

```text
<вставить задачу пользователя>
```

Описание проекта:

```text
<вставить краткое описание проекта, ограничения и ссылки на ключевые файлы>
```

Правила выполнения:

1. Все артефакты активной задачи сохраняй в `multi-agent-system/current-run/`.
2. Глобальный прогресс процесса веди в `multi-agent-system/status.md`.
3. После каждого крупного этапа останавливайся и готовь краткий отчет на мое
   подтверждение.
4. При блокирующих вопросах обновляй
   `multi-agent-system/current-run/open_questions.md` и останавливай процесс.
5. Для ролей используй файлы из `multi-agent-system/agents/`.
6. При необходимости запускай субагентов через Cursor CLI:

```powershell
agent -f --model <model> -p "<prompt>"
```

или:

```powershell
cursor-agent -f --model <model> -p "<prompt>"
```

7. Соблюдай лимиты review-итераций, указанные в `multi-agent-system/agents/01_orchestrator.md`.
