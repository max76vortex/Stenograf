# Task 02 Report: faster-whisper-local provider integration

## Что сделано

- Проверена интеграция Core через ASR abstraction:
  - `transcription/transcribe_to_obsidian.py` использует `get_provider(...)` и `AsrRequest`.
  - Прямых импортов `faster_whisper`/`WhisperModel` в Core-скрипте нет.
  - Регистрация провайдера `faster-whisper-local` доступна через `transcription/asr_providers/registry.py`.
- Добавлены тесты для `task_02` acceptance:
  - `transcription/tests/test_faster_whisper_local_provider.py` (новый файл):
    - TC-02.1: успешный `transcribe` возвращает `AsrResult` с текстом.
    - TC-02.2: отсутствующий input-файл вызывает `AsrError` с `category=input_not_found`.
  - `transcription/tests/test_naming_parity.py` (обновлен):
    - TC-02.3: `transcribe_to_obsidian.py --help` завершается с кодом `0`.

## Изменения по тестам

- **Добавлены:** 2 новых теста в `test_faster_whisper_local_provider.py`.
- **Обновлены:** добавлен 1 тест в `test_naming_parity.py`.

## Какие тесты запущены

- Команда:
  - `python -m unittest discover -s "transcription/tests" -p "test_*.py"`

## Результаты прогона

- Всего тестов: **15**
- Успешно: **15**
- Упало: **0**

## Регрессии

- Регрессий не выявлено.

## Готовность к ревью

- Задача **готова к ревью**.
