# Review: Task Delta 01 — ASR Provider Abstraction

## 1. Общая оценка

Реализация в целом соответствует задаче D01: provider abstraction введен, прямые зависимости Core от `WhisperModel` убраны, регрессий по текущему CLI-потоку не обнаружено, тесты проходят.

## 2. Соответствие задаче

- Требование «Core не импортирует `faster_whisper` напрямую»: выполнено (`transcribe_to_obsidian.py` использует `AsrRequest` + registry/provider).
- Требование «`WhisperModel` только в provider-реализации»: выполнено для Core-кода; в `transcription/` совпадения только в `asr_providers/faster_whisper_local.py` и тестах.
- Требование по default-настройкам (`faster-whisper-local`, `large-v3`, `cuda`, `float16`): выполнено.
- Требование по совместимости формата выхода (Markdown/frontmatter/asset/manifest leading columns): выполнено по коду и тестам.
- Требование «unsupported provider id падает явно»: выполнено (allowlist через `choices` и `registry.get_provider` c `ValueError`).
- Требование «GUI/ingest/dispatcher остаются CLI-обертками»: выполнено (отдельного ASR-кода не добавлено).

## 3. Качество реализации

- Граница ответственности стала чище: ASR-детали вынесены в `transcription/asr_providers/`.
- Контракт `AsrRequest/AsrResult/AsrError` покрывает текущие operational поля и расширяем для следующих провайдеров.
- Регистратор провайдеров ограничивает контур (нет тихого fallback).
- Слой naming вынесен в `transcription/naming.py`, снижая риск рассинхронизации `transcribe_to_obsidian.py` и `check_coverage.py`.

## 4. Тестирование

Проверки выполнены:

- `python transcription/transcribe_to_obsidian.py --help` — OK.
- `python transcription/check_coverage.py --help` — OK.
- `python -c "import sys; sys.path.insert(0, 'transcription'); import transcribe_to_obsidian; print('import-ok')"` — OK.
- `python -m unittest discover -s transcription/tests -p "test_*.py"` — **28 passed, 0 failed**.
- Статический поиск `WhisperModel|from faster_whisper|import faster_whisper` (без `.venv*`) — только `transcription/asr_providers/faster_whisper_local.py` и тесты.

Регрессионные тесты на основной сценарий и смежные контракты присутствуют.

## 5. Документация

- `transcription/README.md` и `transcription/SETUP.md` актуализированы под v1.2-delta и provider abstraction.
- Добавлены/обновлены пояснения по benchmark gate и operational default.
- Smoke-скрипт дополнен запуском unit-тестов.

## 6. Критичные замечания

Критичных замечаний не выявлено.

## 7. Важные замечания

- Пакетный импорт `import transcription.transcribe_to_obsidian` из корня репозитория не работает из-за top-level импорта `from asr_providers ...`; текущий поддерживаемый путь (запуск как скрипт `python transcription/transcribe_to_obsidian.py`) при этом корректен.
- В выдаче `--help` есть локальные проблемы кодировки в Windows-консоли (текст отображается, но с mojibake в отдельных кириллических фрагментах); функционально не блокирует D01, но ухудшает UX.

## 8. Рекомендации

- Если нужен package-style импорт, перейти на package-safe импорты (`from transcription.asr_providers ...`) или поддержать dual-import стратегию.
- Для UX в Windows-консоли добавить короткую заметку в docs про рекомендуемую кодовую страницу/терминал.
- В следующих delta-задачах сохранить текущий принцип: любые новые провайдеры только через abstraction + benchmark gate.

## 9. Итоговое решение

**APPROVED_WITH_COMMENTS** — задача D01 принята, блокеров для продолжения нет.
