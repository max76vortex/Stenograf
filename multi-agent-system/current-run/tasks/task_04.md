# Task 04: Написание тестов на паритет именования и smoke-тестов

## 1. Цель задачи

Покрыть тестами слой именования (Naming Layer) для доказательства паритета между `transcribe_to_obsidian.py` и `check_coverage.py`. Добавить smoke-тесты CLI, которые не скачивают модель `large-v3`, но проверяют работоспособность скриптов.

## 2. Связь с use case

- **UC-04:** Проверка покрытия транскрибации (гарантия совпадения имен).
- **UC-06:** Delta-контур Core/MAS Delivery и ASR R&D (стабильность интерфейсов).

## 3. Конкретные файлы изменений

- **Создаются:**
  - `transcription/tests/test_naming.py`
  - `transcription/tests/test_cli_smoke.py`
- **Изменяются:**
  - `transcription/run-smoke-test.ps1` (если необходимо)

## 4. Описание добавляемых или изменяемых классов, методов, функций

- **В `transcription/tests/test_naming.py`:**
  - `def test_slugify()`: Проверка очистки спецсимволов и пробелов.
  - `def test_get_expected_md_name_flat()`: Проверка имени для файла в корне `recordings/`.
  - `def test_get_expected_md_name_recursive()`: Проверка имени для файла во вложенной папке `recordings/YYYY-MM/`.
  - `def test_parity_transcribe_and_coverage()`: Имитация вызова из `transcribe_to_obsidian.py` и `check_coverage.py` для одного и того же пути, Assert на равенство результатов.
- **В `transcription/tests/test_cli_smoke.py`:**
  - `def test_transcribe_help()`: Вызов `subprocess.run(["python", "transcription/transcribe_to_obsidian.py", "--help"])` и Assert `returncode == 0`.
  - `def test_coverage_help()`: Вызов `subprocess.run(["python", "transcription/check_coverage.py", "--help"])` и Assert `returncode == 0`.
- **В `transcription/run-smoke-test.ps1`:**
  - Добавление вызова `pytest transcription/tests/` (или `python -m unittest`).

## 5. Тест-кейсы

- **TC-04.1:** Вызов `get_expected_md_name` для `D:\recordings\2023-10\2023-10-01_001.mp3` с корнем `D:\recordings` возвращает `2023-10_2023-10-01_001.md`.
- **TC-04.2:** Запуск smoke-тестов через `run-smoke-test.ps1` проходит успешно и не скачивает модель.
- **TC-04.3:** Тест паритета подтверждает, что обе утилиты используют одну логику.

## 6. Критерии приемки

- [ ] Написаны и проходят тесты на `slugify` и `get_expected_md_name`.
- [ ] Написан и проходит тест на паритет именования между `transcribe_to_obsidian.py` и `check_coverage.py`.
- [ ] Smoke-тесты CLI выполняются успешно без необходимости загрузки модели `large-v3`.
- [ ] Добавлены инструкции по запуску тестов (например, через `pytest`).
