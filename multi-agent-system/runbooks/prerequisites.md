# Prerequisites

## Обязательное

Для полноценной работы схемы нужен Cursor CLI, доступный как одна из команд:

- `agent`
- `cursor-agent`

## Проверка

В PowerShell:

```powershell
Get-Command agent, cursor-agent -ErrorAction SilentlyContinue |
  Select-Object Name, CommandType, Source
```

Если команда ничего не вернула, CLI пока не установлен или не попал в `PATH`.

## Что считается готовностью

- хотя бы одна из команд запускается;
- оператор понимает, какую модель подставлять для каждой роли;
- Папка `multi-agent-system/` уже в проекте (внутри неё — `agents/` с промптами ролей).

## До установки CLI

Промпты, шаблоны и runbook’и уже готовы, но полноценный автономный запуск по
схеме статьи будет ограничен до появления рабочего Cursor CLI.
