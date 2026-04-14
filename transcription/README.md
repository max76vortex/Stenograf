# Транскрибация аудио → Obsidian

Пайплайн на **faster-whisper** с моделью **large-v3** для максимального качества. Результат — `.md` с frontmatter под vault Audio Brain (папка `00_inbox`).

**Полная установка на компьютере (что ставить, куда класть, как запускать):** см. **[SETUP.md](SETUP.md)**.

### Быстрая проверка окружения (Windows)

Из папки `transcription`:

```powershell
pwsh -File .\run-smoke-test.ps1
```

Создаёт `.venv` при необходимости, ставит зависимости, вызывает `--help` у основного скрипта и `check_coverage.py` (модель Whisper при этом не качается).

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
- `--manifest FILE` — дописывать в CSV лог: timestamp, путь к mp3, имя .md, дата из frontmatter.
- `--sleep-between-seconds SEC` — пауза после каждого **успешно** обработанного файла (0 по умолчанию); помогает разгрузить GPU/диск при длинных ночных прогонах.
- `--model`, `--device`, `--compute-type`, `--language` — как раньше.
- `--overwrite` — перезаписывать существующие .md.
- `--asset-root DIR` — включает asset-режим: создаёт asset-папки (`YYYY-MM-DD_NNN_slug__src-YYYYMMDD`), пишет `01_transcript__inbox.md` и `meta.json`.
- `--move-source` / `--copy-source` — в asset-режиме переместить (default) или копировать исходник в asset-папку.
- `--no-publish-inbox` — в asset-режиме не писать копию transcript в `output_dir`.

Имя выходного `.md`: из имени mp3 (slug). При `--recursive` — из относительного пути (папка_имя), чтобы файлы из разных месяцев не перезаписывали друг друга.

## Проверка покрытия (какие mp3 ещё без .md)

После транскрибации или при подготовке батча:

```bash
python check_coverage.py "D:\1 ЗАПИСИ ГОЛОС\recordings" "D:\Obsidian\Audio Brain\00_inbox" --recursive
```

Флаги `--recursive` и `--ext` должны совпадать с тем, как вызывали `transcribe_to_obsidian.py`. Скрипт выводит список mp3, для которых нет ожидаемого имени `.md` в inbox.

## Формат вывода

Каждый `.md` соответствует шаблону транскрипта vault: `type: transcript`, `audio_file`, `date`, `status: inbox`, блок «Транскрипт» с текстом. Связь с записью — по полю `audio_file` (имя mp3). Заголовок и «Краткое резюме» можно заполнить в Obsidian после просмотра.

---

## Фаза B (MVP): LLM-first обработка и классификация asset-папок

Скрипт: `phase_b_processor.py`

Что делает:
- читает `01_transcript__inbox.md` в asset-папке;
- создаёт `02_clean__review.md`;
- создаёт `03_content__idea.md` / `03_content__article.md` / `03_content__project.md`;
- обновляет `meta.json`;
- опционально публикует результат в `10_processed/*` vault.

Пример:

```powershell
python phase_b_processor.py "D:\1 ЗАПИСИ ГОЛОС\audio-work" --recursive --vault-dir "D:\Obsidian\Audio Brain" --model "qwen2.5:32b"
```

По умолчанию **`options.num_gpu` не задаётся** — Ollama сам выбирает слои на GPU. Явное большое значение (раньше 999) у части моделей ломало загрузку. Нужен только CPU: **`--cpu-only`**; своё число слоёв: **`--ollama-num-gpu N`**.

**GPU / VRAM / LM Studio:** см. **[GPU-Ollama-LMStudio.md](GPU-Ollama-LMStudio.md)** (`curl /api/ps` и поле `size_vram`, альтернатива **`--backend openai`** для LM Studio на порту 1234).

Рекомендуемая quality-first конфигурация:
- модель: `qwen2.5:32b`
- стиль: `transcription/style/style_profile.md`
- редакторский чеклист: `transcription/style/editing_checklist.md`
- примеры твоего голоса: `transcription/style/examples/*.md`
- хранилище моделей (Ollama/LM Studio): `D:\LLM_models` (как локальный стандарт папки)

Кастомные пути к style/checklist:

```powershell
python phase_b_processor.py "D:\1 ЗАПИСИ ГОЛОС\audio-work" `
  --recursive `
  --vault-dir "D:\Obsidian\Audio Brain" `
  --model "qwen2.5:32b" `
  --style-profile "D:\my-style\style_profile.md" `
  --editing-checklist "D:\my-style\editing_checklist.md" `
  --style-examples-dir "D:\my-style\examples"
```

Если LLM временно недоступна:

```powershell
python phase_b_processor.py "D:\1 ЗАПИСИ ГОЛОС\audio-work" --recursive --vault-dir "D:\Obsidian\Audio Brain" --allow-heuristic-fallback
```
