# Project Context For Dry Run

**MAS Project ID:** `dry-run-system-status-surface`

## Workspace

- Name: `N8N-projects`
- Current primary purpose: конфигурация и сопутствующие скрипты для `n8n`
- Additional subsystem: локальный контур мультиагентной разработки варианта B

## Existing Structure

Key directories:

- `multi-agent-system/agents/` — роли мультиагентной системы
- `multi-agent-system/` — артефакты, шаблоны, runbook'и
- `memory-bank/` — долговременный контекст проекта
- `transcription/` — отдельный рабочий поток транскрибации
- `nginx/` — конфиги reverse proxy

## Existing Constraints

- Нельзя ломать рабочий контур `n8n`.
- Нельзя требовать тяжелую новую инфраструктуру ради dry run.
- Dry run должен по возможности жить внутри `multi-agent-system/`.
- На текущий момент Cursor CLI (`agent` / `cursor-agent`) не найден в `PATH`.

## Existing Multi-Agent Files

- Global status: `multi-agent-system/status.md`
- Active artifacts: `multi-agent-system/current-run/`
- Operator guidance: `multi-agent-system/runbooks/`

## Dry Run Intent

Проверить, что система умеет:

- принимать постановку задачи;
- формировать ТЗ;
- проводить ревью ТЗ;
- строить архитектуру и план;
- останавливаться на подтверждение пользователя после каждого крупного этапа.
