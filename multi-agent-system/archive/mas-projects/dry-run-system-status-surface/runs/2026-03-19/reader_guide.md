## Гид для читателя: прогон dry-run-system-status-surface

### Что это за проект в двух фразах

Это **не отдельный продукт**, а проверка и развитие **мультиагентной обвязки** в репозитории `N8N-projects`: оркестратор, роли в `multi-agent-system/agents/`, артефакты в `multi-agent-system/current-run/`, плюс CLI для просмотра статуса dry run из терминала.

### С чего начать чтение

1. **`multi-agent-system/status.md`** — снимок состояния процесса (сейчас `COMPLETE`).
2. **`multi-agent-system/runbooks/how-to-run-project-through-multi-agent-system.md`** — как запускать следующий проект через MAS.
3. **`multi-agent-system/runbooks/mas-archive-policy.md`** — как обязательно архивировать завершённые прогоны.
4. **`multi-agent-system/agents/00_agent_development.md`** и **`multi-agent-system/agents/01_orchestrator.md`** — роли и порядок этапов.

### Как воспроизвести проверку статуса (CLI)

Из корня workspace:

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/dryrun-status.ps1" -Top 10
```

Preflight перед оркестратором:

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/orchestrator-preflight.ps1"
```

Запуск оркестратора (после заполнения `current-run/task_brief.md`):

```powershell
.\multi-agent-system\start-orchestrator.ps1 -Model "auto"
```

### Где лежит архив этого прогона

- **Workspace:** `multi-agent-system/archive/mas-projects/dry-run-system-status-surface/runs/2026-03-19/`
- **Obsidian (Audio Brain):** `20_system/Система мультиагентов/Архив прогонов/dry-run-system-status-surface/` — зеркальная заметка с передачей.

### Что проверить при аудите

- [ ] В `project_context.md` указан **`MAS Project ID`** для каждого нового прогона.
- [ ] После `COMPLETE` создан каталог в `archive/mas-projects/<id>/runs/<дата>/`.
- [ ] В Obsidian есть заметка в `20_system/Система мультиагентов/` (по шаблону из `20_system/templates/` — в vault Audio Brain шаблоны там, не в корневой `Templates/`).
