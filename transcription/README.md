# Транскрибация аудио → Obsidian

Ключевая система распознавания в текущем operational-контуре: **`speech2text-transcriptions`**.

Core v1.2-delta сохраняет ASR provider abstraction и локальный `faster-whisper-local` как contingency/baseline.

История сравнения альтернативных ASR-кандидатов вынесена в архив:

- `transcription/asr-benchmark/archive/ASR_EVALUATION_ARCHIVE_2026-04.md`

**Полная установка на компьютере (что ставить, куда класть, как запускать):** см. **[SETUP.md](SETUP.md)**.

### Быстрая проверка окружения (Windows)

Из папки `transcription`:

```powershell
pwsh -File .\run-smoke-test.ps1
```

Создаёт `.venv` при необходимости, ставит зависимости, вызывает `--help` у основного скрипта и `check_coverage.py` (модель Whisper при этом не качается).

### Запуск тестов

Из папки `transcription`:

```powershell
python -m unittest discover -s .\tests -p "test_*.py"
```

### Окно вместо терминала (опционально)

После установки зависимостей можно запустить простой GUI (tkinter, без доп. пакетов):

```bash
python transcribe_gui.py
```

Выбор папок «Обзор…», флаги рекурсии и перезаписи, опционально манифест, **пауза между файлами** (секунды) — чтобы снизить непрерывную нагрузку на GPU. Под капотом вызывается тот же `transcribe_to_obsidian.py`.

## Записи с телефона через Google Drive

Для сценария "диктофон на телефоне -> Google Drive -> этот проект" добавлен скрипт:

```bash
python ingest_phone_recordings.py --help
```

Что делает:
- читает экспорт Google Drive (локальная папка после синка/скачивания);
- находит новые аудио (`.m4a`, `.mp3`, `.wav`, `.ogg`, `.aac`, `.flac`);
- раскладывает в `recordings/YYYY-MM/`;
- приводит имя к формату `YYYY-MM-DD_NNN_phone[-slug].ext`;
- сохраняет манифест, чтобы не импортировать один и тот же файл повторно.

Пример импорта:

```bash
python ingest_phone_recordings.py \
  "D:\GoogleDrive\PhoneRecorder" \
  "D:\1 ЗАПИСИ ГОЛОС\recordings" \
  --manifest "D:\1 ЗАПИСИ ГОЛОС\recordings\phone_ingest_manifest.json"
```

Сразу импорт + транскрибация (Phase A asset-flow):

```bash
python ingest_phone_recordings.py \
  "D:\GoogleDrive\PhoneRecorder" \
  "D:\1 ЗАПИСИ ГОЛОС\recordings" \
  --manifest "D:\1 ЗАПИСИ ГОЛОС\recordings\phone_ingest_manifest.json" \
  --run-transcribe \
  --transcribe-output "D:\Obsidian\Audio Brain\00_inbox" \
  --transcribe-asset-root "D:\1 ЗАПИСИ ГОЛОС\audio-work" \
  --transcribe-recursive \
  --transcribe-manifest "D:\1 ЗАПИСИ ГОЛОС\recordings\manifest.csv"
```

Таким образом телефонные записи автоматически попадают в ту же структуру, что и "компьютерные", и дальше проходят обработку по существующим правилам проекта.

## Требования

- Python 3.10+
- GPU NVIDIA с 6+ ГБ VRAM (RTX 3060 подходит; large-v3 в fp16 ~4.5 ГБ)
- CUDA и cuDNN (для `device=cuda`)

## Установка

```bash
cd transcription
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

При первом запуске модель `large-v3` скачается автоматически (несколько ГБ).

---

## Порядок: папка записей и имена файлов

Чтобы ничего не перепутать и сохранить хронологию:

### Структура папки с записями

Рекомендуется **разбивка по месяцам**:

```
recordings/
  2024-01/
  2024-02/
  ...
  2025-03/
```

В каждой папке — все mp3 за этот месяц. Так удобно гонять скрипт по одной папке или по всему дереву с `--recursive`.

### Именование mp3

**Шаблон:** `YYYY-MM-DD_NNN[ _метка].mp3`

- `YYYY-MM-DD` — дата записи (обязательно).
- `NNN` — номер в этот день: 001, 002, … (обязательно).
- `_метка` — опционально (латиница/цифры/дефис).

**Примеры:** `2024-03-15_001.mp3`, `2024-03-15_002_idei-produkt.mp3`.

Так сохраняется порядок по имени, нет коллизий в один день, дата однозначно попадает во frontmatter. Старые файлы без такого имени: можно переименовать вручную (хотя бы дату и номер) или оставить — скрипт возьмёт дату из даты изменения файла.

---

## Использование

```bash
# Одна папка (например месяц)
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox"

# Вся папка записей рекурсивно (все подпапки 2024-01, 2024-02, …)
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings" "D:\Obsidian\Audio Brain\00_inbox" --recursive

# С логом обработанных (манифест)
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --manifest "D:\1 ЗАПИСИ ГОЛОС\recordings\manifest.csv"

# Перезапись уже существующих .md
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --overwrite

# Язык авто
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --language auto

# Новый режим Phase A (asset-flow):
# - переносит исходник в asset-папку
# - создаёт 01_transcript__inbox.md + meta.json
# - публикует копию transcript в 00_inbox
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings" "D:\Obsidian\Audio Brain\00_inbox" --recursive --asset-root "D:\1 ЗАПИСИ ГОЛОС\audio-work"
```

**Параметры:**

- `input_dir` — каталог с `.mp3` (или корень при `--recursive`).
- `output_dir` — каталог для `.md` (например `D:\Obsidian\Audio Brain\00_inbox`).
- `--recursive` — обходить все подпапки; имена .md включают путь (напр. `2024-01_2024-01-15_001.md`), чтобы не было коллизий.
- `--manifest FILE` — дописывать в CSV лог: timestamp, путь к mp3, имя .md, дата из frontmatter; новые манифесты также содержат `asr_provider`, `asr_model`, `asr_status`, `asr_error_category`, `asr_error_message`, `error_category`, `elapsed_sec`.
- `--sleep-between-seconds SEC` — пауза после каждого **успешно** обработанного файла (0 по умолчанию); помогает разгрузить GPU/диск при длинных ночных прогонах.
- `--model`, `--device`, `--compute-type`, `--language` — как раньше.
- `--overwrite` — перезаписывать существующие .md.
- `--asset-root DIR` — включает asset-режим: создаёт asset-папки (`YYYY-MM-DD_NNN_slug__src-YYYYMMDD`), пишет `01_transcript__inbox.md` и `meta.json`.
- `--move-source` / `--copy-source` — в asset-режиме переместить (default) или копировать исходник в asset-папку. Default-перенос выполняется только после успешного ASR, чтобы failed-файл остался в исходной очереди для повторного запуска той же команды.
- `--no-publish-inbox` — в asset-режиме не писать копию transcript в `output_dir`.

Имя выходного `.md`: из имени mp3 (slug). При `--recursive` — из относительного пути (папка_имя), чтобы файлы из разных месяцев не перезаписывали друг друга.

### Обработка ошибок в batch-прогоне (continue-on-error)

Если ASR падает на одном файле, скрипт:

- печатает `[FAILED]` с provider/model/category;
- не создаёт успешный transcript для этого файла;
- продолжает следующие файлы;
- пишет `asr_status=failed` в manifest, а в asset-режиме также в `meta.json`;
- завершает весь batch с кодом `1`, если была хотя бы одна ошибка.

Для уже существующих legacy-манифестов со старым header (4/7 колонок) скрипт сохраняет header как есть и дописывает расширенные строки в append-only режиме. Если downstream-парсер читает только header-колонки, создайте новый manifest через `--manifest` или вручную обновите header до расширенного формата.

Пустой результат распознавания сохраняет прежнюю совместимость: создаётся transcript с `(нет речи)` и `quality_flags: ["empty_output"]` в asset `meta.json`.

Коды возврата:

- `0` — batch завершён без ASR ошибок (включая кейс, когда все файлы были пропущены как уже обработанные);
- `1` — в batch была хотя бы одна ASR ошибка;
- `2` — ошибка аргументов CLI (поведение `argparse`).

## Проверка покрытия (какие mp3 ещё без .md)

После транскрибации или при подготовке батча:

```bash
python check_coverage.py "D:\1 ЗАПИСИ ГОЛОС\recordings" "D:\Obsidian\Audio Brain\00_inbox" --recursive
```

Флаги `--recursive` и `--ext` должны совпадать с тем, как вызывали `transcribe_to_obsidian.py`. Скрипт выводит список mp3, для которых нет ожидаемого имени `.md` в inbox.

## Формат вывода

Каждый `.md` соответствует шаблону транскрипта vault: `type: transcript`, `audio_file`, `date`, `status: inbox`, блок «Транскрипт» с текстом. Связь с записью — по полю `audio_file` (имя mp3). Заголовок и «Краткое резюме» можно заполнить в Obsidian после просмотра.

---

## ASR benchmark gate (WS-025)

Текущий quality-gated benchmark для RU-речи зафиксирован в:

- `transcription/asr-benchmark/README.md` — краткий контракт Benchmark Gate для Worktree 1/2
- `transcription/asr-benchmark/CORE_GATE.md` — Core gate: когда можно менять ASR provider/default
- `multi-agent-system/current-run/worktree_handoff.md` — handoff-контракт Worktree 2 -> Worktree 1 для текущего MAS run
- `transcription/asr-benchmark/results.csv`
- `transcription/asr-benchmark/decision.md`

Канонический operational flow для Core v1.2:

1. Active ASR API path: `speech2text-transcriptions` (принятый operational decision).
2. Локальный `faster-whisper-local` используется как fallback/contingency baseline.
3. Исторические альтернативы (`nexara`, `gigaam-v3`, legacy simulated cloud) не являются текущим operational default.
4. Любой новый provider включается только после свежего approved decision package.

Если decision package отсутствует, устарел, содержит simulated-only/provisional/blocked строки или не утверждает конкретный provider/profile, Core продолжает использовать `faster-whisper-local`.

Дополнительно для локального RU-R&D:

- `transcription/asr-benchmark/GIGAAM-RUNBOOK.md`
- `transcription/asr-benchmark/run_gigaam_smoke.py`
- `transcription/asr-benchmark/run_gigaam_chunked.py`

Примечание по GigaAM-v3:

- без `HF_TOKEN` длинные файлы можно прогонять через chunking (например 10s сегменты),
- но результат всё равно обязан пройти тот же quality gate (loops/coherence/post-edit),
- текущий smoke показывает, что модель перспективная, но ещё требует донастройки окружения/режима.

---

## Фаза B (основной и единственный путь в проекте)

Phase B выполняется только через skill:

- `.cursor/skills/user-mas-phase-b-process/SKILL.md`
- модель: **Kimi** (`kimi-k2.5`)
- backend в `meta.json`: `llm_backend: cursor`

Что делает skill:
- читает `01_transcript__inbox.md` в asset-папке;
- создаёт `02_clean__review.md`;
- создаёт `03_content__idea.md` / `03_content__article.md` / `03_content__project.md` / `03_content__junk.md` / `03_content__unclear.md`;
- обновляет `meta.json` с новой версией и полями `llm_model`/`llm_backend`.

Категории по новой схеме:
- `idea` — рабочая идея/заметка;
- `article` — заготовка статьи;
- `project` — проектная задача/план;
- `junk` — явный хлам или технический шум (автоответчик, пустой звонок);
- `unclear` — запись низкого качества или слишком фрагментарная, требует ручной ревизии.

Важно:
- старые варианты через Ollama/LM Studio больше не используются в этом проекте;
- `phase_b_processor.py` оставлен только для архива и совместимости, но не является рабочим путём.
- после классификации запись из `00_inbox` раскладывается в `10_processed/<category>` по правилам skill.

## Батчинг под бесплатные лимиты транскрибации (R&D/эксперимент)

Для планового распознавания по квотам используй:

```powershell
python transcription_limit_dispatcher.py --help
```

Подробно про лимиты и откуда цифры: **[FREE_LIMITS.md](FREE_LIMITS.md)**.

Этот раздел не меняет Core v1.2 default: основной production-путь остаётся локальным
`faster-whisper-local`. Любой внешний/API provider или quota-profile можно включать
в Core default только после свежего approved decision package для точного
provider/profile.

Скрипт:
- берёт очередь из `recordings/`;
- формирует партии по лимитам (по умолчанию профиль Groq Free Whisper);
- после исчерпания окна ждёт reset и запускает следующий батч автоматически (`--watch`).

Пример непрерывного режима:

```powershell
python transcription_limit_dispatcher.py `
  --input-dir "D:\1 ЗАПИСИ ГОЛОС\recordings" `
  --output-dir "D:\Obsidian\Audio Brain\00_inbox" `
  --manifest "D:\1 ЗАПИСИ ГОЛОС\recordings\manifest.csv" `
  --asset-root "D:\1 ЗАПИСИ ГОЛОС\audio-work" `
  --recursive `
  --watch
```
