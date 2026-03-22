# Как запускать проект через мультиагентную систему

Этот документ фиксирует операционный ритуал: как вести проект **через** оркестратор и pipeline (Variant B), а не «как обычно» в свободном чате.

## Команда Cursor (интерактивный сценарий)

В чате Cursor введите **`/start-multi-agent-run`** — подставится сценарий из `.cursor/commands/start-multi-agent-run.md`: сначала **preflight** (CLI, обязательные файлы), затем проверка run (п.2), вопросы и заполнение входов (п.1), ожидание подтверждения, затем запуск `start-orchestrator.ps1` (п.3).

## Preflight перед оркестратором (опционально, из терминала)

Из корня workspace:

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/orchestrator-preflight.ps1"
```

При ошибках см. `multi-agent-system/runbooks/prerequisites.md`.

## 1. Подготовить входы перед стартом

Нужны два файла:

- `multi-agent-system/current-run/task_brief.md` — что сделать (цели, scope, ограничения, что не делать).
- `multi-agent-system/current-run/project_context.md` — контекст проекта (стек, текущее состояние, важные файлы/папки, ограничения по инфраструктуре).

**Идентификатор проекта MAS (обязательно для архива после завершения):** в начале `project_context.md` зафиксируйте уникальный slug, по которому проект будет отделяться в архиве (латиница, дефисы), например:

```markdown
**MAS Project ID:** `my-unique-project-slug`
```

**MAS** здесь и далее — сокращение от **M**ulti-**A**gent **S**ystem (`multi-agent-system/`).

Система работает от этих входов, а не «из головы».

## 2. Проверить, что run готов

- `multi-agent-system/status.md` — если там прошлый run, он должен быть закрыт (`COMPLETE`) или осознанно продолжается.
- `multi-agent-system/current-run/` — не должно быть мусора от другой задачи (или это осознанно сохранено).

Правило из `current-run/README.md`: при старте новой задачи очистить или заархивировать результаты прошлого прогона.

## 3. Запускать через оркестратор

Запуск из **корня workspace** (после preflight и заполнения `task_brief.md` / `project_context.md`).

**Рекомендуемый вариант:** по умолчанию оркестратор берёт постановку из `multi-agent-system/current-run/task_brief.md` и контекст из `multi-agent-system/current-run/project_context.md` (если файл есть). Явно указывать пути не обязательно.

```powershell
.\multi-agent-system\start-orchestrator.ps1 -Model "auto"
```

**Явные пути** (если нужны другие файлы):

```powershell
.\multi-agent-system\start-orchestrator.ps1 `
  -TaskFile "multi-agent-system/current-run/task_brief.md" `
  -ProjectContextFile "multi-agent-system/current-run/project_context.md" `
  -Model "auto"
```

Параметр `-Model` подставьте по своей политике (см. `runbooks/prerequisites.md`).

**Важно:** `examples/sample-task-brief.md` — только пример для копирования; рабочий запуск всегда опирается на **`current-run/task_brief.md`**.

Предпосылки по CLI: см. `multi-agent-system/runbooks/prerequisites.md`.

## 4. Работать в режиме checkpoint-подтверждений (ключевое отличие)

После каждого **крупного** этапа процесс останавливается и ждёт подтверждения. Без подтверждения следующий этап не начинается.

Типичная цепочка:

1. Analysis  
2. TZ review  
3. Architecture  
4. Architecture review  
5. Planning  
6. Plan review  
7. Development  
8. Code review  
9. Final summary  

Определение Variant B: см. `multi-agent-system/agents/00_agent_development.md` (подтверждение после каждого этапа).

## 5. На каждом шаге смотреть три вещи

- `multi-agent-system/status.md` — главный источник истины по процессу.
- Новый артефакт этапа в `multi-agent-system/current-run/` (reviews, reports, ТЗ, план и т.д.).
- `multi-agent-system/current-run/open_questions.md` — блокеры и уточнения.

## 6. Если блокер или ошибка

- Фиксировать в `open_questions.md`.
- Отвечать на вопросы пользователем.
- Продолжать **с того же этапа**, не перескакивать стадии вручную.

Правила переходов: `multi-agent-system/runbooks/stage-transition-rules.md`.

## 7. Завершение — венец всего цикла (обязательная архивация)

> *Конец — всему делу венец.* Финал прогона в MAS — это не только `Final summary` в `current-run/`, а **обязательное** закрытие с передачей знаний дальше.

### 7.1 Подтверждение и статус

- После этапа `Final summary` — подтвердить его пользователем.
- Убедиться, что в `multi-agent-system/status.md` прогон переведён в **`COMPLETE`**.

### 7.2 Обязательная архивация (не опционально)

Каждый завершённый прогон **должен** быть заархивирован по политике:

- подробная инструкция и чеклист: **`multi-agent-system/runbooks/mas-archive-policy.md`**;
- корень архива в репозитории: **`multi-agent-system/archive/`** (см. `archive/README.md`).

**Что обязано быть по смыслу:**

1. **Подробный отчёт о всей проделанной работе** — не только краткий summary, а исчерпывающее описание: цели, результат, ключевые решения, артефакты, ссылки на файлы, ограничения и риски.
2. **Материалы для читателя**, который **впервые** видит проект: что это за проект, зачем он был, как устроен, что читать в каком порядке, как воспроизвести/проверить.
3. **Имя проекта в архиве** — используйте **`MAS Project ID`** из `project_context.md`; по нему разделяются каталоги `archive/mas-projects/<mas_project_id>/...` и записи в Obsidian.

Рекомендуемые имена файлов отчёта в архиве прогона: `mas_handover_report.md`, `reader_guide.md` (или один объединённый документ с тем же содержанием) — см. `mas-archive-policy.md`.

### 7.3 Копия в Obsidian (обязательно)

Параллельно с папкой в workspace создайте **зеркальную** документацию в vault:

- по правилам **этой** базы (см. `.cursor/rules/obsidian-content-boundaries.mdc`) — в **`20_system/Система мультиагентов/`** (не `Base/`, не `ИТ проекты/`, не `00_inbox`/`10_processed`);
- пример пути: **`20_system/Система мультиагентов/Архив прогонов/<mas_project_id>/`** или одна заметка с русским именем файла в том же разделе;
- новая заметка — **с шаблона** из **`20_system/templates/`** в vault Audio Brain (список шаблонов → чтение → заполнение → запись; корневой `Templates/` в этом vault нет);
- тот же идентификатор проекта, ссылка на путь в `N8N-projects`, дата закрытия, суть handover и reader guide.

Так читатель сможет найти проект **и в репозитории, и в Obsidian**, не теряя контекста.

### 7.4 Очистка `current-run/`

Очистку или смену активного прогона выполняйте **только после** копирования в архив (по правилам `current-run/README.md`).

---

## Чем это отличается от «обычного» запуска

| Обычный режим | Через систему |
|---------------|----------------|
| Сразу кодим в чате | Сначала ТЗ → архитектура → план → разработка |
| Один большой контекст | Узкие роли и отдельные промпты в `multi-agent-system/agents/` |
| Нет обязательных артефактов | На каждом этапе есть выходной файл |
| Нет явных quality gates | Есть review-этапы |
| Сложно восстановить ход работы | Есть `status.md` и дерево `current-run/` |
| Финал = «сделали и забыли» | Финал = **обязательная** архивация + Obsidian + отчёты для следующего читателя |

---

## Быстрый чеклист на каждый новый проект

- [ ] Если предыдущий прогон закрыт и нужен **чистый** `current-run/` + новый slug: выполнить `multi-agent-system/tools/mas-new-run.ps1 -MasProjectId "<slug>"` (скилл **mas-clean-start**) или вручную по `current-run/README.md`
- [ ] Заполнить `current-run/task_brief.md`
- [ ] Заполнить `current-run/project_context.md` и строчку **`MAS Project ID`** (slug для архива)
- [ ] Убедиться, что предыдущий run закрыт или осознанно сброшен
- [ ] При необходимости: `multi-agent-system/tools/orchestrator-preflight.ps1`
- [ ] Запустить `.\multi-agent-system\start-orchestrator.ps1 -Model "auto"` (по умолчанию — `current-run/task_brief.md` и `project_context.md`)
- [ ] Подтверждать этапы по checkpoint
- [ ] Следить за `status.md`, артефактами и `open_questions.md`
- [ ] Закрыть `Final summary`, статус `COMPLETE`
- [ ] Выполнить **обязательную** архивацию по `runbooks/mas-archive-policy.md` (workspace + **копия в Obsidian**)

---

## Сводка (копипаст для Obsidian)

### Контекст

- Система запускается через оркестратор и stage-by-stage pipeline.
- Главные входы: `task_brief.md` и `project_context.md`.
- Главный источник состояния: `multi-agent-system/status.md`.

### Что делать

1. Подготовить `multi-agent-system/current-run/task_brief.md`.
2. Подготовить `multi-agent-system/current-run/project_context.md` с **`MAS Project ID`** для будущего архива.
3. Проверить, что предыдущий run завершён или осознанно продолжается.
4. Запустить `.\multi-agent-system\start-orchestrator.ps1 -Model "auto"` (см. п.3; по умолчанию читается `current-run/task_brief.md`) или сначала `orchestrator-preflight.ps1`.
5. Идти по этапам с подтверждением после каждого checkpoint.
6. При блокерах работать через `open_questions.md`, не перескакивая стадии.
7. После `Final summary`: `COMPLETE`, затем **обязательная** архивация по `mas-archive-policy.md` (workspace + **Obsidian**).

### Ключевые правила

- Не переходить к следующему крупному этапу без подтверждения.
- Для рабочих прогонов не обходить оркестратор без причины.
- На каждом шаге проверять: `status.md` + новый артефакт этапа + `open_questions.md`.
- **Завершённый прогон без архивации и без копии в Obsidian — неполное закрытие цикла MAS.**

### Что проверить

- В конце run в `status.md` должен быть `COMPLETE` (или явное продолжение).
- В `current-run/` должны быть артефакты пройденных этапов.
- Выполнены: финальный отчёт, **обязательная** архивация в `multi-agent-system/archive/mas-projects/<mas_project_id>/`, подробные `mas_handover_report` / `reader_guide`.
- В **Obsidian** в **`20_system/Система мультиагентов/`** есть зеркальная заметка/папка с тем же `mas_project_id` (создано по шаблону из **`20_system/templates/`**).
