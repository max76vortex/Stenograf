# Task 05 Report: документация и Benchmark Gate контракт

## Измененный код и документация

- Обновлен `transcription/README.md`:
  - зафиксирован Core v1.2-delta default provider `faster-whisper-local`;
  - cloud/API провайдеры (`yandex-speechkit`, `deepgram-nova-2`, `nexara`) явно помечены как R&D/экспериментальные до Benchmark Gate;
  - раздел ошибок переоформлен в `continue-on-error` с явными кодами возврата (`0/1/2`);
  - в ASR benchmark gate добавлена ссылка на новый `transcription/asr-benchmark/README.md`.
- Обновлен `transcription/SETUP.md`:
  - уточнен статус Core v1.2-delta;
  - явно зафиксировано, что модель `large-v3` скачивается при первом запуске и требует место под кэш.
- Создан `transcription/asr-benchmark/README.md`:
  - описан контракт Worktree 2 -> Worktree 1;
  - зафиксированы требования к `decision.md` и обязательные поля `results.csv`;
  - описано правило, что смена default provider допустима только по утвержденному `decision.md`.

## Какие тесты добавлены или обновлены

- **Добавлены:**
  - `transcription/tests/test_docs_benchmark_gate.py`
    - проверка default provider и experimental-статуса облачных кандидатов;
    - проверка раздела `continue-on-error` и кодов возврата;
    - проверка требований `SETUP.md` по `large-v3`;
    - проверка контракта Benchmark Gate в `transcription/asr-benchmark/README.md`.
- **Обновлены:**
  - нет (существующие тесты не менялись).

## Какие тесты были запущены

- `python -m unittest discover -s "transcription/tests" -p "test_*.py"`

## Результаты тестов

- Всего прошло: **26**
- Упало: **0**

## Регрессии

- Регрессии не выявлены.

## Готовность к ревью

- Задача **готова к ревью**.
