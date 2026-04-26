# Task 04 Report: naming parity tests and CLI smoke tests

## Измененный код

- Добавлен `transcription/tests/test_naming.py`:
  - `test_slugify`
  - `test_get_expected_md_name_flat`
  - `test_get_expected_md_name_recursive`
  - `test_parity_transcribe_and_coverage`
- Добавлен `transcription/tests/test_cli_smoke.py`:
  - `test_transcribe_help`
  - `test_coverage_help`
- Обновлен `transcription/run-smoke-test.ps1`:
  - после `--help` проверок добавлен запуск `python -m unittest discover -s tests -p "test_*.py"`.
- Обновлен `transcription/README.md`:
  - добавлена инструкция запуска тестов через `unittest`.

## Какие тесты добавлены или обновлены

- **Добавлены:**
  - `transcription/tests/test_naming.py`
  - `transcription/tests/test_cli_smoke.py`
- **Обновлены:**
  - `transcription/run-smoke-test.ps1` (включен запуск тестов)
  - `transcription/README.md` (инструкция запуска тестов)

## Какие тесты были запущены

- `python -m unittest discover -s "transcription/tests" -p "test_*.py"`
- `pwsh -File .\transcription\run-smoke-test.ps1`

## Результаты тестов

- Всего прошло: **22**
- Упало: **0**

## Регрессии

- Регрессии не выявлены.

## Готовность к ревью

- Задача **готова к ревью**.
