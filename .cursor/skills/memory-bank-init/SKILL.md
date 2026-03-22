---
name: memory-bank-init
description: >-
  Initializes or completes Memory Bank 2.0 in the workspace (memory-bank/ folder, tasks,
  progress, projectbrief, etc.) and adds portable task tracking: task-registry.md, task-tracking.md,
  workspace-task-tracking.mdc, optional activity journal scripts. Use when the user runs
  /инициализация, init memory bank, новый проект memory bank, подготовка workspace, or bootstrap
  task tracking alongside Memory Bank.
---

# Инициализация Memory Bank + учёт задач (WS-NNN)

Выполняй **по шагам**. Если `memory-bank/` уже есть — **дополни** только отсутствующее, не затирай пользовательский контент без явного согласия.

---

## Фаза A — Каркас Memory Bank 2.0

Создай папку **`memory-bank/`** в **корне workspace** и структуру:

```
memory-bank/
├── tasks.md
├── activeContext.md
├── progress.md
├── projectbrief.md
├── productContext.md
├── systemPatterns.md
├── techContext.md
├── style-guide.md
├── creative/README.md
├── reflection/README.md
└── archive/README.md
```

**Минимальное содержимое** (если файла не было):

| Файл | Минимум |
|------|---------|
| `tasks.md` | Заголовок `# Tasks`, блок **Current Task** (Status NOT_STARTED), ссылка на учёт: см. `task-registry.md` и `task-tracking.md` (после фазы B). |
| `activeContext.md` | `# Active Context` + 2–3 строки фокуса. |
| `progress.md` | `# Progress` + строка с датой инициализации. |
| `projectbrief.md` | `# Project Brief` + Name / Goal / Stack (заглушки из ответа пользователя или TODO). |
| `productContext.md`, `techContext.md`, `systemPatterns.md` | Заголовки и 1 абзац или пустые секции. |
| `style-guide.md` | Заголовок, при необходимости «TBD». |

Подкаталоги `creative/`, `reflection/`, `archive/` — с коротким `README.md` или пустые.

---

## Фаза B — Учёт задач (обязательно для этой методики)

Источник шаблонов: **`memory-bank/bootstrap/templates/`** в этом репозитории (если скилл вызван из N8N-projects) **или** пути, которые укажет пользователь.

1. Скопируй **`task-tracking.md`** → `memory-bank/task-tracking.md` (если файла нет — из шаблона; если есть — не перезаписывай без согласия).
2. Скопируй **`task-registry.empty.md`** → `memory-bank/task-registry.md` (если реестра ещё нет). Если реестр уже с данными — **не затирай**.
3. В начало **`tasks.md`** добавь блок (если ещё нет):

```markdown
**Учёт задач workspace:** каждая значимая задача — ID **`WS-NNN`** и строка в **`memory-bank/task-registry.md`**; правила — **`memory-bank/task-tracking.md`**. В `progress.md` при закрытии указывай `[WS-NNN]`.
```

4. В **`projectbrief.md`** добавь строку (если нет):

```markdown
- Task IDs: реестр **`memory-bank/task-registry.md`** (`WS-NNN`), правила — **`memory-bank/task-tracking.md`**.
```

5. В **`systemPatterns.md`** добавь раздел:

```markdown
## Учёт задач

- Реестр: **`memory-bank/task-registry.md`**
- Правила: **`memory-bank/task-tracking.md`**
```

---

## Фаза C — Правило Cursor в проекте

Создай **`.cursor/rules/workspace-task-tracking.mdc`**, скопировав содержимое из **`memory-bank/bootstrap/templates/workspace-task-tracking.mdc`** (или актуальный файл из эталонного репо).  
`alwaysApply: true` — чтобы агент не забывал реестр.

---

## Фаза D — Журнал активности (опционально)

Спроси пользователя: **нужны ли** скрипты `scripts/append-activity-journal.ps1`, `Get-ActivityReport.ps1` и журнал `memory-bank/activity-journal.md`.

Если **да**:

1. Создай в корне репо папку **`scripts/`** (если нет).
2. Скопируй файлы из **`memory-bank/bootstrap/reference-scripts/`** → **`scripts/`** (идентичные имена).
3. Опционально: скопируй **`memory-bank/bootstrap/reference-githooks/post-commit`** → **`.githooks/post-commit`**, затем пользователь выполнит `git config core.hooksPath .githooks`.
4. Упомни скилл **workspace-activity-report** — при необходимости скопируй `.cursor/skills/workspace-activity-report/` из эталонного репозитория.

---

## Фаза E — Глобальные правила Cursor (инструкция человеку)

Выдай пользователю **кратко**:

- Открой **`memory-bank/bootstrap/GLOBAL-CURSOR-SETUP.md`** (в N8N-projects) или перескажи: нужно вставить блок в **Cursor → Settings → Rules → User Rules**, чтобы во **всех** проектах с `memory-bank` агент помнил про `WS-NNN`.

Полный текст блока — в том файле.

---

## Фаза F — Закрытие инициализации

1. Добавь в **`memory-bank/progress.md`** строку с датой: «Инициализированы Memory Bank + учёт задач (task-registry, task-tracking, cursor rule)» и при необходимости **`[WS-NNN]`** если завели задачу в реестре.
2. Предложи пользователю следующий шаг: заполнить `projectbrief`, перенести **User Rules** из `GLOBAL-CURSOR-SETUP.md`, сделать первый коммит.

---

## Если шаблонов bootstrap нет в workspace

Пользователь может склонировать или скопировать папку **`memory-bank/bootstrap/`** из репозитория **N8N-projects** (или другого эталона). Без неё создавай **`task-tracking.md` и `task-registry.md` вручную** по смыслу фазы B.

---

## Связанные пути (эталон N8N-projects)

- `memory-bank/bootstrap/README.md`
- `memory-bank/bootstrap/GLOBAL-CURSOR-SETUP.md`
- `memory-bank/bootstrap/templates/`
- `memory-bank/bootstrap/reference-scripts/`
