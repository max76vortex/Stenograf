# Task 01: Создание абстракции ASR-провайдера и слоя именования

## 1. Цель задачи

Выделить общую логику формирования имен выходных файлов (Naming Layer) для обеспечения паритета между скриптами транскрибации и проверки покрытия. Создать базовые интерфейсы ASR-провайдера (ASR Provider Abstraction), чтобы отвязать основной конвейер (Core Delivery) от прямой зависимости от библиотеки `faster_whisper`.

## 2. Связь с use case

- **UC-02:** Транскрибация папки месяца (единое именование `.md` файлов).
- **UC-03:** Рекурсивная транскрибация дерева (предотвращение коллизий имен).
- **UC-04:** Проверка покрытия транскрибации (использование общего слоя именования).
- **UC-06:** Delta-контур Core/MAS Delivery и ASR R&D (введение абстракции провайдера).

## 3. Конкретные файлы изменений

- **Создаются:**
  - `transcription/naming.py`
  - `transcription/asr_providers/__init__.py`
  - `transcription/asr_providers/base.py`
  - `transcription/asr_providers/registry.py`
- **Изменяются:**
  - `transcription/transcribe_to_obsidian.py`
  - `transcription/check_coverage.py`

## 4. Описание добавляемых или изменяемых классов, методов, функций

- **В `transcription/naming.py`:**
  - `def get_expected_md_name(audio_path: str, root_dir: str) -> str`: Возвращает ожидаемое имя `.md` файла для заданного аудио (с учетом рекурсивного пути для предотвращения коллизий).
  - `def slugify(text: str) -> str`: Общая функция очистки имен (перенос из `transcribe_to_obsidian.py`).
- **В `transcription/asr_providers/base.py`:**
  - `class AsrRequest`: Dataclass/Pydantic-модель с полями `audio_path`, `language`, `provider_id`, `model`, `runtime_options`.
  - `class AsrResult`: Dataclass/Pydantic-модель с полями `text`, `segments`, `language_detected`, `duration_sec`, `provider_id`, `quality_flags`.
  - `class AsrError(Exception)`: Базовый класс ошибок провайдера.
  - `class AsrProvider(Protocol)`: Интерфейс с методом `def transcribe(self, request: AsrRequest) -> AsrResult`.
- **В `transcription/asr_providers/registry.py`:**
  - `DEFAULT_ASR_PROVIDER_ID = "faster-whisper-local"`
  - `def get_provider(provider_id: str) -> AsrProvider`: Фабрика для получения инстанса провайдера.
- **В `transcribe_to_obsidian.py` и `check_coverage.py`:**
  - Замена дублирующейся логики именования вызовами из `naming.py`.

## 5. Тест-кейсы

- **TC-01.1:** Передача `audio_path` из вложенной папки в `get_expected_md_name` возвращает имя, включающее префикс папки.
- **TC-01.2:** Вызов `get_provider("unknown_id")` выбрасывает исключение `ValueError`.
- **TC-01.3:** Импорт `AsrRequest` и `AsrResult` проходит без ошибок.

## 6. Критерии приемки

- [ ] В `transcribe_to_obsidian.py` и `check_coverage.py` больше нет дублирования функций `slugify` и логики формирования имен.
- [ ] Пакет `asr_providers` содержит базовые классы и типы, не зависящие от конкретных библиотек (например, `faster_whisper`).
- [ ] Реестр провайдеров (`registry.py`) корректно инициализирован и содержит константу `DEFAULT_ASR_PROVIDER_ID`.
