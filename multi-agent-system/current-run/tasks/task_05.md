# Task 05: Обновление документации и фиксация контракта Benchmark Gate

## 1. Цель задачи

Актуализировать эксплуатационную документацию (`README.md`, `SETUP.md`), чтобы отразить текущее состояние Core Delivery (v1.2-delta) с провайдером по умолчанию `faster-whisper-local`. Описать контракт Benchmark Gate для приема новых ASR-движков из Worktree 2.

## 2. Связь с use case

- **UC-01:** Установка окружения (актуальные инструкции).
- **UC-06:** Delta-контур Core/MAS Delivery и ASR R&D (фиксация контракта).

## 3. Конкретные файлы изменений

- **Изменяются:**
  - `transcription/README.md`
  - `transcription/SETUP.md`
- **Создаются:**
  - `transcription/asr-benchmark/README.md` (если отсутствует)

## 4. Описание добавляемых или изменяемых классов, методов, функций

- **В `transcription/README.md`:**
  - Обновить описание архитектуры: указать, что `faster-whisper-local` является провайдером по умолчанию.
  - Удалить или пометить как "экспериментальные" упоминания облачных провайдеров (Yandex, Deepgram, Nexara), которые еще не прошли Benchmark Gate.
  - Добавить раздел "Обработка ошибок", описывающий поведение continue-on-error и коды возврата.
- **В `transcription/SETUP.md`:**
  - Убедиться, что инструкции по установке `faster-whisper` и CUDA актуальны.
  - Добавить примечание о том, что модель `large-v3` скачивается при первом запуске.
- **В `transcription/asr-benchmark/README.md`:**
  - Описать процесс Benchmark Gate:
    - Worktree 2 (ASR R&D) проводит тестирование.
    - Формирует `decision.md` и `results.csv`.
    - Worktree 1 (Core Delivery) принимает решение о смене провайдера по умолчанию только на основании утвержденного `decision.md`.
  - Указать обязательные поля для `results.csv` (`file_id`, `duration_min`, `noise`, `engine`, `A_loops`, `A_empty`, `A_coherence`, `A_pass`).

## 5. Тест-кейсы

- **TC-05.1:** Пользователь может успешно установить окружение по `SETUP.md` на чистой машине Windows.
- **TC-05.2:** В `README.md` нет упоминаний облачных провайдеров как "production/default".
- **TC-05.3:** Контракт Benchmark Gate четко определяет критерии приема новых провайдеров.

## 6. Критерии приемки

- [ ] `README.md` и `SETUP.md` обновлены и соответствуют архитектуре v1.2-delta.
- [ ] Описано поведение continue-on-error при пакетной обработке.
- [ ] Описан контракт Benchmark Gate и требования к `decision.md` и `results.csv`.
- [ ] Упоминания облачных провайдеров (Yandex, Deepgram, Nexara) помечены как экспериментальные или удалены из основного пути выполнения.
