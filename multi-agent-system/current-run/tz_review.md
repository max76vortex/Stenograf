# TZ Review

## Summary

- **Overall status:** Approved with comments
- **Reviewed document:** `technical_specification.md` (v1.2-delta, detailed UC-01..UC-06 structure)
- **MAS Project ID:** `audio-transcription-v1`
- **Overall assessment:** ТЗ существенно улучшено по сравнению с предыдущими итерациями. Полностью отражает исходную постановку задачи из `task_brief.md` и `project_context.md`, включая delta-требования (продолжение текущего run без нового, разделение Worktree 1/Core vs Worktree 2/ASR R&D, обязательность ASR provider abstraction + benchmark decision gate). Use cases детализированы, критерии приемки в основном проверяемы, scope/non-scope чётко разделены. Учтена существующая кодовая база (`transcribe_to_obsidian.py`, `check_coverage.py`, прямой импорт faster-whisper). Блокирующих проблем нет.

ТЗ пригодно для перехода к архитектуре.

## BLOCKING

**Нет.**

## MAJOR

### 1. ASR Provider Abstraction Contract не формализован в ТЗ
- **Location:** `technical_specification.md:105-119` (UC-06), раздел 2 (Area of Changes)
- **Problem:** UC-06 правильно требует "отсутствие жесткой привязки к единственному ASR backend" и работу "только через согласованный интерфейс провайдера", но сам интерфейс (входы/выходы, `AsrRequest`/`AsrResult`, обработка ошибок, метаданные) не описан даже на минимальном уровне.
- **Why it matters:** Это центральный контракт delta-режима между Worktree 1 и Worktree 2. Без явного описания (хотя бы на уровне типов/обязательных полей) архитектура может реализовать "абстракцию", которая не будет достаточной для бесшовной замены провайдеров или для R&D-результатов.
- **Recommendation:** Не переписывать ТЗ, а в `architecture.md` (или как приложение к ТЗ) зафиксировать минимальный контракт провайдера. Это ожидаемо на следующем этапе и не блокирует текущее ТЗ.

### 2. Benchmark Decision Package упомянут, но структура и процесс gate не определены
- **Location:** `technical_specification.md:111-115` (UC-06 main/alternative scenarios + acceptance criteria)
- **Problem:** UC-06 говорит о "актуальном decision package" и "подтвержденном" решении из R&D, но не определяет, что именно должно входить в decision package, где он хранится (`transcription/asr-benchmark/decision.md`?), какие метрики/артефакты обязательны и кто/как утверждает gate.
- **Why it matters:** Это главный защитный механизм дельты. Без чёткого определения Core может принять непроверенные изменения из Worktree 2 или, наоборот, заблокироваться из-за неясного статуса decision.
- **Recommendation:** Оставить детали на уровень `architecture.md` / `benchmark decision` документа, но явно связать UC-06 acceptance criteria с конкретными артефактами (например, `decision.md` + `results.csv` + статус утверждения).

## MINOR

### 1. Покрытие ошибок и edge-кейсов можно усилить
- **Location:** `technical_specification.md` раздел 3 (Use Cases), особенно UC-02..UC-05
- **Problem:** Основные happy-path и несколько альтернатив (CPU fallback, overwrite, interrupt) описаны. Однако практически отсутствуют сценарии:
  - повреждённые/нечитаемые аудиофайлы;
  - OOM / GPU out of memory на больших файлах;
  - ошибки загрузки модели;
  - проблемы с правами доступа / disk full;
  - поведение при падении одного файла в батче.
- **Why it matters:** Для production-grade пайплайна на ~30 ГБ данных устойчивость к ошибкам критична. Текущий TZ фокусируется на happy path + idempotency.
- **Recommendation:** Не добавлять новые use cases в ТЗ (не переписывать), а учесть в `architecture.md` раздел Error Handling / Batch Resilience. Соответствует существующему решению "continue-on-error with final non-zero exit" из `plan.md`.

### 2. Синхронизация логики именования между скриптами
- **Location:** `technical_specification.md:88-89` (UC-04 acceptance criteria), `open_questions.md`
- **Problem:** UC-04 требует, чтобы правило "аудио → ожидаемый .md" было "синхронизировано" между `transcribe_to_obsidian.py` и `check_coverage.py`. Открытый вопрос о shared module/autotests остаётся.
- **Why it matters:** Расхождение в slug/naming logic — частый источник багов в таких пайплайнах.
- **Recommendation:** Это правильно вынесено в open questions. Решить на этапе планирования/реализации (shared `naming.py` модуль или тесты на parity).

### 3. Привязка к существующим артефактам могла быть explicit
- **Location:** Раздел 2 и UC-01..UC-04
- **Problem:** ТЗ правильно упоминает существующие файлы (`transcribe_to_obsidian.py`, `check_coverage.py`, `transcribe_gui.py`, `README.md`, `SETUP.md`), но не всегда явно говорит, что именно должно быть изменено/рефакторизовано (например, удаление прямого импорта `faster_whisper.WhisperModel`).
- **Why it matters:** Помогает избежать "рефакторинга ради рефакторинга" или пропуска ключевых мест.
- **Recommendation:** Улучшение качества, не критично. Архитектура уже отражает это (`asr_providers/` структура).

## Coverage of Original Requirements

**From Task Brief & Project Context:**
- [x] Локальный конвейер mp3 → Obsidian `00_inbox` с frontmatter + "Транскрипт" блоком
- [x] Предсказуемый порядок, именование, `audio_file` связь, idempotency (skip existing)
- [x] `faster-whisper large-v3`, CUDA/float16, CPU fallback
- [x] `check_coverage.py`, документация (`README.md`, `SETUP.md`, bat examples)
- [x] Non-scope: Ghost, n8n, content editing
- [x] Delta requirements (continue current run, Worktree 1 vs 2, provider abstraction, benchmark gate)

**Existing System Integration:**
- Учтена структура `recordings/YYYY-MM/`, vault `Audio Brain/00_inbox`
- Учтены существующие скрипты и необходимость рефакторинга под abstraction
- Учтены ограничения железа (RTX 3060 6GB, CUDA)

## Blocking Questions

Нет. Все открытые вопросы (см. `open_questions.md`) — уточняющего характера и не блокируют архитектуру.

## Final Decision

- [ ] Approved
- [x] **Approved with comments**
- [ ] Rework required
- [ ] Blocking

**JSON (для оркестратора):**

```json
{
  "review_file": "multi-agent-system/current-run/tz_review.md",
  "has_critical_issues": false
}
```

---

**Рекомендация:** Перейти к архитектуре. MAJOR замечания по контрактам (provider interface + decision package) будут естественным образом закрыты в `architecture.md` и `asr_providers/base.py`.
