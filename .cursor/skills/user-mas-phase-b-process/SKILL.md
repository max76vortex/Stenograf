---
name: user.mas.phase-b-process
description: >-
  Обрабатывает транскрипты Phase A через Kimi в Cursor (без локальных Ollama/LM Studio):
  чистит текст, классифицирует (idea/article/project/junk/unclear), записывает 02_clean, 03_content,
  обновляет meta.json. Используй когда пользователь просит обработать транскрипты,
  запустить Phase B, «обработай записи», «почисти транскрипты», «разбери inbox».
---

# Phase B: обработка транскриптов через Kimi в Cursor

Этот скилл обрабатывает транскрипты из asset-папок (результат Phase A) силами
встроенной модели Cursor с профилем Kimi — без локальных Ollama/LM Studio и без внешних ключей.

---

## Контекст

- **Phase A** (`transcribe_to_obsidian.py`) создаёт asset-папки с `01_transcript__inbox.md` и `meta.json`.
- **Phase B** (этот скилл) берёт сырой транскрипт и создаёт очищенный текст + классификацию.
- Справочные файлы стиля: `transcription/style/style_profile.md`, `transcription/style/editing_checklist.md`.
- Примеры стиля (если есть): `transcription/style/examples/*.md` (кроме TEMPLATE.md и README.md).
- **Модель по умолчанию:** Kimi (`kimi-k2.5`). Это единственный поддерживаемый вариант Phase B в этом проекте.

## Scope (защита от случайного запуска в другом проекте)

Перед запуском обязательно проверь:
1. Workspace root = `C:\Users\sa\N8N-projects`.
2. Есть путь `.cursor/skills/user-mas-phase-b-process/SKILL.md`.
3. Есть папка `transcription/` и файл `transcription/style/style_profile.md`.

Если любой пункт не выполнен — остановись и сообщи, что скилл привязан только к проекту `N8N-projects`.

## Входные данные

Пользователь указывает **одно из**:
- Конкретную asset-папку (например `D:\audio-work\2024-03\2024-03-15_001_...`)
- Корневую папку (`--recursive` по всем asset-папкам с `01_transcript__inbox.md`)
- Или говорит «обработай все» — тогда ищи asset-папки в `transcription/demo_audio_work/` или по указанному пути.

## Алгоритм (выполняй по шагам)

### Шаг 1: Найти asset-папки

Asset-папка — это каталог, содержащий `01_transcript__inbox.md`.

Найди все такие папки. Для каждой проверь:
- Если `03_content__*.md` уже существует и пользователь **не** просил перезаписать → **пропусти**.
- Если транскрипт (текст после `## Транскрипт`) короче **30 символов** → **пропусти** (мусор/пустая запись).
- Если папка похожа на backup/снимок (`compare-before-*`, `_archive*`, `backup*`) → **пропусти**.

### Шаг 2: Прочитать стилевые файлы

Прочитай:
1. `transcription/style/style_profile.md`
2. `transcription/style/editing_checklist.md`
3. Файлы `.md` из `transcription/style/examples/` (кроме TEMPLATE.md и README.md), если есть — до 5 штук.

### Шаг 3: Для каждой asset-папки

Прочитай `01_transcript__inbox.md`. Извлеки:
- **frontmatter** (YAML между `---`)
- **транскрипт** (текст после `## Транскрипт`)

Затем обработай транскрипт, выполнив следующую задачу:

---

**ЗАДАЧА ОБРАБОТКИ ТРАНСКРИПТА**

Ты — редактор русскоязычных транскриптов диктофонных записей.
Работай в стиле из style_profile.md, соблюдай editing_checklist.md.

Из сырого ASR-транскрипта сделай:

1. **clean_text** — очищенный текст:
   - Исправь ASR-ошибки, пунктуацию, согласование
   - Убери повторы, слова-паразиты («ну», «значит», «вот», «типа», «как бы»)
   - Разбей на абзацы (один абзац = одна мысль)
   - Сохрани ВСЕ факты и мысли автора, ничего не придумывай

2. **title** — заголовок (3–8 слов), отражающий ключевую мысль

3. **summary** — резюме (2–5 буллетов с маркером `-`), практическая суть

4. **category** — одна из пяти:
   - `idea` — короткая мысль, зарисовка, заметка
   - `article` — есть структура/тезисы, задел под публикацию
   - `project` — задача/план с шагами, контекстом
   - `junk` — явный хлам/технический шум (автоответчик, случайная запись, пустой звонок)
   - `unclear` — фрагмент или низкое качество, когда категорию определить нельзя

5. **tags** — 2–5 тематических тегов (на русском, через запятую)

6. **needs_review** — `true` если текст неоднозначен или ASR сильно искажён

---

### Шаг 4: Записать результаты

Для каждой обработанной asset-папки создай **три файла**:

#### 4a. `02_clean__review.md`

```markdown
---
type: "{category или note для idea}"
status: "review"
category: "{category}"
audio_file: "{из frontmatter оригинала}"
asset_path: "{абсолютный путь к asset-папке}"
source_transcript: "01_transcript__inbox.md"
tags: "{tags через запятую}"
updated_at: "{ISO datetime}"
phase: "B2"
stage: "clean"
---

## Заголовок
{title}

## Краткое резюме
{summary}

## Текст

{clean_text}
```

#### 4b. `03_content__{category}.md`

Тот же формат, но `phase: "B5"` и `stage: "classified"`.

#### 4c. Обновить `meta.json`

Прочитай существующий `meta.json`, обнови/добавь:

```json
{
  "phase": "B",
  "category": "{category}",
  "needs_review": true/false,
  "review_reason": "{причина или пустая строка}",
  "llm_model": "kimi-k2.5",
  "llm_backend": "cursor",
  "style_profile": "custom",
  "updated_at": "{ISO datetime}",
  "versions": [ ...существующие..., {
    "timestamp": "{ISO datetime}",
    "files": ["02_clean__review.md", "03_content__{category}.md"],
    "category": "{category}"
  }]
}
```

### Шаг 5: Отчёт

После обработки всех папок выведи таблицу:

| Asset | Category | Title | needs_review |
|-------|----------|-------|--------------|
| ... | idea/article/project | ... | true/false |

И итог: `Done. ok=N, skip=N`.

### Шаг 6: Публикация из `00_inbox` в `10_processed`

После обработки каждой записи обязательно выполни раскладку:

- `idea` → `10_processed/ideas`
- `article` → `10_processed/articles`
- `project` → `10_processed/projects`
- `junk` → `10_processed/junk`
- `unclear` → `10_processed/unclear`

Правило публикации:
- файл из `00_inbox` с этой записью должен быть перенесён/разложен в соответствующую папку `10_processed`;
- не отправляй в архив автоматически;
- любые массовые чистки `00_inbox` — только по прямой команде пользователя.

## Важные правила

- **Не придумывай факты.** Если в транскрипте нет информации — не добавляй.
- **Не менее 30 символов** транскрипта для обработки.
- **Сохраняй `audio_file`** из оригинального frontmatter.
- Для `type` в frontmatter: `idea/junk/unclear` → `note`, `article` → `article`, `project` → `project`.
- ISO datetime формат: `YYYY-MM-DDTHH:MM:SS`.
