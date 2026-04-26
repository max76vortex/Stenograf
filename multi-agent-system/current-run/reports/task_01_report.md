# Task 01 Report: naming layer + ASR provider abstraction baseline

## Измененный код

- `transcription/naming.py`
  - Добавлены требуемые API:
    - `slugify(text: str) -> str`
    - `get_expected_md_name(audio_path: Path, root_dir: Path, recursive: bool) -> str`
  - Оставлены алиасы совместимости (`slug`, `expected_md_name`) без изменения поведения.
- `transcription/asr_providers/registry.py`
  - Добавлен требуемый метод `get_provider(...) -> AsrProvider`.
  - Для неизвестного `provider_id` теперь выбрасывается `ValueError` (по TC-01.2).
  - Сохранен совместимый враппер `get_asr_provider(...)`, делегирующий в `get_provider(...)`.
- `transcription/asr_providers/__init__.py`
  - Экспортирован `get_provider`.
- `transcription/transcribe_to_obsidian.py`
  - Убраны обращения к старым именам в логике Task 01:
    - `slug` -> `slugify`
    - `expected_md_name` -> `get_expected_md_name`
    - `get_asr_provider` -> `get_provider`
  - Добавлен обработчик `ValueError` при неверном `provider_id` на этапе резолва провайдера.
- `transcription/check_coverage.py`
  - Переведено на `get_expected_md_name` из `naming.py`.

## Тесты (добавлены/обновлены)

- Обновлены `transcription/tests/test_naming_parity.py`:
  - проверка `get_expected_md_name` для nested path (TC-01.1);
  - проверка `get_provider("unknown_id")` -> `ValueError` (TC-01.2);
  - проверка импорта/использования `AsrRequest` и `AsrResult` (TC-01.3);
  - обновлены проверки паритета вызовов под новые имена API.
- Обновлены `transcription/tests/test_transcribe_failures.py`:
  - адаптация monkeypatch на `get_provider` после переключения Core-скрипта.

## Какие тесты запущены

- `python -m unittest tests.test_naming_parity tests.test_transcribe_failures`
- `python transcribe_to_obsidian.py --help`
- `python check_coverage.py --help`

## Результаты тестов

- Всего прошло: **12**
- Упало: **0**
- Регрессии: **не выявлены** в рамках запущенного набора.

## Готовность к ревью

Задача **готова к ревью**.
