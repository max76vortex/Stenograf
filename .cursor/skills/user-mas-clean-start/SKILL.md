---
name: user.mas.clean-start
description: >-
  Prepares a clean MAS (Multi-Agent System, Variant B) workspace for a new project: backs up
  multi-agent-system/current-run to archive/mas-snapshots, resets status.md from template, writes
  stub task_brief.md and project_context.md with a new MAS Project ID, clears open_questions and
  removes prior stage artifacts (tasks/reviews/reports). Use when the user starts a new MAS run,
  asks for a clean current-run, reset after COMPLETE archive, «чистый старт MAS», «новый прогон»,
  or before filling task_brief for a new slug.
---

# Чистый старт MAS (новый прогон)

Цель — **безопасно** освободить `multi-agent-system/current-run/` и **`status.md`** под **новую** задачу с новым **`MAS Project ID`**, не теряя прошлый прогон (резервная копия по умолчанию).

Исполняй процедуру **после** того, как завершённый прогон **заархивирован** по `runbooks/mas-archive-policy.md` (или пользователь явно согласен не опираться на старые артефакты).

---

## 1. Собери у пользователя

1. **`MAS Project ID`** — уникальный slug (`kebab-case`, латиница и цифры), например `ghost-sync-v1`. Без этого скрипт не запустить.
2. Опционально: **короткая метка** для поля Active task в `status.md` (если отличается от slug) — параметр `-ActiveTaskLabel`.
3. **Подтверждение**, что старый прогон можно снять с «активных» (или уже в архиве).

---

## 2. Автоматическая подготовка (основной путь)

Из **корня workspace** (`N8N-projects`):

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/mas-new-run.ps1" -MasProjectId "<slug>"
```

- Скрипт задаст вопрос подтверждения (если не `-- -Force`).
- По умолчанию копирует весь `current-run/` в **`multi-agent-system/archive/mas-snapshots/<timestamp>_<slug>_previous/`**.
- Удаляет артефакты прошлого прогона (ТЗ, архитектура, план, `tasks/*.md`, `reviews/*.md`, `reports/*.md` — **README в подпапках сохраняются**).
- Перезаписывает: **`status.md`** (из шаблона), **`task_brief.md`**, **`project_context.md`** (с `**MAS Project ID:** \`<slug>\``), **`open_questions.md`**.

Просмотр без изменений:

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/mas-new-run.ps1" -MasProjectId "<slug>" -WhatIf -Force
```

Без бэкапа (только если пользователь осознанно принимает риск):

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/mas-new-run.ps1" -MasProjectId "<slug>" -NoBackup -Force
```

---

## 3. Что сделать после скрипта

1. Пользователь **дорабатывает** `task_brief.md` и `project_context.md` (убрать TODO, уточнить стек и ограничения).
2. `pwsh -File multi-agent-system/tools/orchestrator-preflight.ps1`
3. `.\multi-agent-system\start-orchestrator.ps1 -Model "auto"`

Дальше — как в скилле **`start-multi-agent-run`** (фазы B–D).

---

## 4. Если терминал недоступен

Вручную повтори логику скрипта по:

- `multi-agent-system/templates/status.initial.template.md` — шаблон `status.md`;
- `multi-agent-system/current-run/README.md` — правила смены прогона;
- резервная копия: скопируй всю папку `current-run/` в `archive/mas-snapshots/` с понятным именем.

Не удаляй файлы без явного согласия пользователя.

---

## Связанные файлы

- Скрипт: `multi-agent-system/tools/mas-new-run.ps1`
- Шаблон статуса: `multi-agent-system/templates/status.initial.template.md`
- Снимки: `multi-agent-system/archive/mas-snapshots/README.md`
- Архивация завершённых прогонов: `multi-agent-system/runbooks/mas-archive-policy.md`
