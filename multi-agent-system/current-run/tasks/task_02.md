# Task 02: Реализация `faster-whisper-local` провайдера и интеграция в Core

## 1. Цель задачи

Реализовать локальный ASR-провайдер на базе `faster-whisper` и интегрировать его в основной конвейер транскрибации `transcribe_to_obsidian.py`. Обеспечить, чтобы это был единственный файл в Core, который напрямую импортирует `WhisperModel`.

## 2. Связь с use case

- **UC-01:** Установка окружения (сохранение зависимости `faster-whisper`).
- **UC-02:** Транскрибация папки месяца (вызов ASR-провайдера).
- **UC-03:** Рекурсивная транскрибация дерева (вызов ASR-провайдера).
- **UC-06:** Delta-контур Core/MAS Delivery и ASR R&D (интеграция провайдера через абстракцию).

## 3. Конкретные файлы изменений

- **Создаются:**
  - `transcription/asr_providers/faster_whisper_local.py`
- **Изменяются:**
  - `transcription/transcribe_to_obsidian.py`
  - `transcription/asr_providers/registry.py`

## 4. Описание добавляемых или изменяемых классов, методов, функций

- **В `transcription/asr_providers/faster_whisper_local.py`:**
  - `class FasterWhisperLocalProvider(AsrProvider)`: Реализация интерфейса `AsrProvider`.
  - `def transcribe(self, request: AsrRequest) -> AsrResult`:
    - Создает инстанс `WhisperModel` с параметрами из `request.runtime_options` (`model_size`, `device`, `compute_type`).
    - Вызывает метод транскрибации.
    - Маппит результаты `faster-whisper` в `AsrResult`.
    - Обрабатывает ошибки и выбрасывает `AsrError`.
- **В `transcription/asr_providers/registry.py`:**
  - Регистрация `FasterWhisperLocalProvider` под ключом `faster-whisper-local`.
- **В `transcription/transcribe_to_obsidian.py`:**
  - Удаление прямых импортов `faster_whisper` и `WhisperModel`.
  - Замена создания модели на `provider = get_provider(DEFAULT_ASR_PROVIDER_ID)`.
  - Формирование `AsrRequest` из аргументов CLI и вызов `provider.transcribe(request)`.

## 5. Тест-кейсы

- **TC-02.1:** Вызов `transcribe` с валидным `.mp3` возвращает `AsrResult` с текстом.
- **TC-02.2:** Вызов `transcribe` с несуществующим файлом выбрасывает `AsrError` с категорией `input_not_found`.
- **TC-02.3:** Запуск `transcribe_to_obsidian.py --help` проходит без ошибок.

## 6. Критерии приемки

- [ ] В `transcribe_to_obsidian.py` полностью отсутствуют импорты `faster_whisper` и `WhisperModel`.
- [ ] Единственное место, где инициализируется `WhisperModel`, — это `transcription/asr_providers/faster_whisper_local.py`.
- [ ] Существующие параметры CLI (`--model`, `--device`, `--compute-type`) корректно пробрасываются в `AsrRequest` и применяются провайдером.
- [ ] Выходной Markdown-файл и frontmatter формируются корректно на основе возвращенного `AsrResult`.
