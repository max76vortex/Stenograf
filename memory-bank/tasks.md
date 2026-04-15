# Tasks

**Учёт задач workspace:** каждая значимая задача — ID **`WS-NNN`** и строка в **`memory-bank/task-registry.md`**; правила — **`memory-bank/task-tracking.md`**. В `progress.md` при закрытии указывай `[WS-NNN]`.

## Current Task
- Status: BUILD (Phase B Kimi + лимитный батчинг Phase A)
- Complexity: 3
- Description: Зафиксировать **единственный** путь Phase B через skill `phase-b-process` (Kimi), убрать legacy-альтернативы из рабочих инструкций и внедрить батч-диспетчер под бесплатные лимиты распознавания.

---

## Сквозной процесс (кратко)

1. **A — Транскрибация:** `recordings/` → скрипт → `00_inbox/*.md` (`creative-transcription-workflow.md`).
2. **B — Подготовка + классификация:** `00_inbox` → правка → `10_processed/ideas|articles|projects` + шаблоны (`creative-post-transcription-pipeline.md`).
3. **C — Развитие материала:** идея → черновик статьи; проект — по шаблону; по мере надобности.
4. **D — Публикация (Ghost):** `creative-content-pipeline-and-ghost.md`, инструкция в vault `20_system/`.

---

## Phase 1 — Транскрибация

### Plan / Checklist
- [x] Спроектировать структуру Obsidian-vault и шаблоны (транскрипт, идеи, статья, проект).
- [x] Выбрать инструмент транскрибации (faster-whisper large-v3, скрипт transcription/).
- [x] Спроектировать порядок и рабочий процесс: папка записей (recordings/YYYY-MM/), именование mp3 (creative-transcription-workflow.md).
- [x] Реализовать в скрипте: `--recursive`, `--manifest`; `check_coverage.py`; README/SETUP.

### Исполнение (машина пользователя)
- [x] Спринт A (task_01): smoke, CUDA/cuBLAS (WS-011).
- [ ] Спринт B (task_02): массовый прогон архива по `multi-agent-system/current-run/plan.md`.

---

## Phase 1.5 — Подготовка текста и разнесение по категориям (после транскрибации)

**Цель:** зафиксировать и при необходимости дополнить **документацию**, чтобы этап B был воспроизводимым; структура vault (`00_inbox` → `10_processed`) использовалась осознанно.

### План реализации (шаги)

| # | Шаг | Артефакт / владелец | Статус |
|---|-----|---------------------|--------|
| 1 | Согласовать сквозную схему A→D | `creative-post-transcription-pipeline.md` | Done (креатив) |
| 1.1 | Зафиксировать asset-модель: перенос исходника, исходное имя, суффиксы, `asset_path`, `meta.json`, правила даты | `creative-post-transcription-pipeline.md` (§1.1, §2.4, §2.6) | Done |
| 1.2 | Реализационный чеклист по доработке `transcribe_to_obsidian.py` для asset-flow в Phase A | `creative-post-transcription-pipeline.md` (§5) | Done |
| 1.3 | Реализовать MVP-скрипт Phase B (LLM-first): clean + classify + meta + publish | `transcription/phase_b_processor.py` | Done |
| 1.4 | Реализовать asset-flow в `transcribe_to_obsidian.py` (asset dirs, move/copy source, transcript+meta, inbox publish) | `transcription/transcribe_to_obsidian.py` | Done |
| 1.5 | Добавить quality-first контур стиля для LLM (style profile + editing checklist + style examples, интеграция в Phase B скрипт) | `transcription/style/*`, `phase_b_processor.py`, `README.md` | Done |
| 1.6 | Исправить обнаружение asset-папок в Phase B: рекурсивный режим от корня `audio-work` | `transcription/phase_b_processor.py` (`--recursive`) | Done |
| 2 | Инструкция «Фаза B» для ежедневной работы: **LLM/скрипт-проход B1–B7** (auto + human checkpoint), куда класть файл, связь с шаблонами | Заметка в vault `20_system/` (новая или раздел в существующей) | Pending |
| 3 | Краткий README или указатель в `10_processed/` (если ведётся в vault — путь в инструкции) | vault | Pending |
| 4 | Ссылка из репозитория: `memory-bank/productContext.md` (1 абзац про фазу B) | репо | Done |
| 5 | Опционально: одна строка в `transcription/README.md` — «после транскрибации см. …» | репо | Done |
| 6 | Прогон приёмки: 1–2 заметки пройти B1–B7 по инструкции (LLM-first) | пользователь | **Сейчас:** все 11 ассетов прогнаны Phase B (см. `10_processed`, WS-015); осталось **ваша ревизия** качества и при необходимости правки/перегон с другой моделью |

### Что ещё не зафиксировано в vault (на конец дня)

- [ ] Инструкция в Obsidian для ежедневной работы Phase B (`20_system/`), чтобы путь B1-B7 был виден прямо в vault.
- [ ] Указатель/README в `10_processed/` (папки ideas/articles/projects и правила переноса из `00_inbox`).
- [ ] Примеры авторского стиля в `transcription/style/examples/` (минимум 5-10 файлов) для реального quality-first режима.

### План на завтра (логичный порядок)

1. Прогнать 1-2 реальных asset-папки через `phase_b_processor.py` с `qwen2.5:32b`.
2. Проверить результат в Obsidian (`10_processed/*`) и точечно поправить style profile/checklist.
3. Из лучших обработанных материалов сформировать эталоны и добавить 5-10 файлов в `transcription/style/examples/`.
4. Записать в Obsidian рабочую инструкцию Phase B (B1-B7, критерии `needs_review`, правило очистки `00_inbox` после переноса в `10_processed`).
5. Закрыть шаги 2/3/6 в этой таблице при успешной приёмке.

### Компоненты, требующие креатива (уже закрыто в черновике)

- Правила классификации ideas / articles / projects — §2.2 в `creative-post-transcription-pipeline.md` (можно уточнять по ходу).
- Нужна ли отдельная заметка-глоссарий в vault — решается при шаге 2.

### Направление

- Креатив для фазы B: **`memory-bank/creative/creative-post-transcription-pipeline.md`** (обновлять при смене правил).
- Реализация: шаги таблицы выше; код в репозитории **не обязателен** для MVP (всё в Obsidian + Memory Bank).

---

## Phase 2 — Постинг (Ghost)

- [ ] Выбрать реализацию интеграции Obsidian ↔ Ghost (скрипт/сервис/n8n).
- [ ] Поток Obsidian → Ghost и обратно, валидация — по `creative-content-pipeline-and-ghost.md` и инструкции в vault.

---

## Supporting Tooling — Multi-Agent System

- [x] См. исторические чеклисты в архивных строках `tasks.md` при необходимости.

## Backlog / Future Projects

- [ ] LLM-ассист для резюме/тегов после транскрибации (опционально, см. creative-post-transcription §2.5).
- [ ] WS-004 / WS-005 — см. прежние backlog-строки при актуализации.
