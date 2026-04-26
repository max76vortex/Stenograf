# Task Delta 02 Review: Core Integration, Batch Errors, and Docs Compatibility

## 1. Общая оценка

Реализация в целом соответствует задаче и acceptance criteria: интеграция ASR provider boundary в Core сделана, дефолт `faster-whisper-local` сохранен, batch-failure поведение реализовано и подтверждено тестами. Вердикт: **approved_with_comments**.

## 2. Соответствие задаче

- `AsrRequest` формируется на каждый файл после skip/output-решений.
- Для генерации Markdown используется `AsrResult.text`.
- `AsrError` обрабатывается пофайлово с видимым `[FAILED]` сообщением (file/provider/model/category).
- При ошибке по файлу успешные артефакты (`out_path`, `01_transcript__inbox.md`, inbox copy) не создаются.
- Batch продолжает обработку и завершает процесс кодом `1`, если были ошибки.
- Манифест расширен ASR-полями с сохранением legacy leading columns.
- В asset/existing-asset режиме `meta.json` обновляется статусом `failed`, полями ошибки и `versions[]`-записью без transcript-файла.
- Документация (`README.md`, `SETUP.md`) переведена на совместимый v1.2 messaging: default — локальный `faster-whisper-local`, внешние/API providers только через новый approved decision.

## 3. Качество реализации

- Логика обработки ошибок и записи артефактов реализована аккуратно: запись transcript и move source происходят в корректной последовательности.
- В asset-mode перенос source отложен до успешного ASR, что улучшает retryability и соответствует заявленному поведению.
- Изменения не нарушают CLI-совместимость: новых обязательных флагов нет, default provider остается прежним.
- Публичный контракт provider boundary (`AsrRequest`/`AsrResult`/`AsrError`) используется последовательно.

## 4. Тестирование

- Проверено: `python -m unittest transcription.tests.test_transcribe_failures` — **5 tests passed**.
- Покрыты ключевые сценарии:
  - mixed batch (success/fail/success) с итоговым exit `1`;
  - all skipped -> exit `0`;
  - asset-mode fail -> `meta.json` updated, transcript не создается;
  - existing-asset fail -> `meta.json` updated, transcript не создается;
  - retry same command после transient fail в asset-mode.
- Smoke проверки CLI:
  - `python transcription\transcribe_to_obsidian.py --help` — pass;
  - `python transcription\check_coverage.py --help` — pass.

## 5. Документация

- `README.md` и `SETUP.md` актуализированы по default/provider-policy и batch-failure semantics.
- Legacy cloud wording (`yandex-speechkit` + `deepgram-nova-2`) корректно ограничен историческим/R&D контекстом.
- Явно зафиксировано требование fresh approved decision package для внешних/API providers перед default enablement.

## 6. Критичные замечания

Критичных замечаний нет.

## 7. Важные замечания

- Для **уже существующих** legacy manifest-файлов со старым заголовком скрипт дописывает расширенные строки, но сам header не мигрирует. В результате `asr_status/asr_error_*` могут быть не видны в header-based парсерах, хотя данные в строках присутствуют.

## 8. Рекомендации

- Добавить отдельный тест на append в **существующий legacy manifest** (4/7-column header), чтобы явно зафиксировать ожидаемое совместимое поведение.
- В operational docs коротко описать, как безопасно мигрировать старый manifest header, если нужен доступ к новым ASR-полям в BI/CSV-пайплайнах.

## 9. Итоговое решение

**approved_with_comments**. Task Delta 02 можно считать выполненной и готовой к переходу на следующий шаг, при сохранении текущего benchmark gate (без включения external/API providers в default до нового approved decision).
