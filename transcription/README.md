# Транскрибация аудио → Obsidian

Пайплайн на **faster-whisper** с моделью **large-v3** для максимального качества. Результат — `.md` с frontmatter под vault Audio Brain (папка `00_inbox`).

**Полная установка на компьютере (что ставить, куда класть, как запускать):** см. **[SETUP.md](SETUP.md)**.

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
python transcribe_to_obsidian.py "D:\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox"

# Вся папка записей рекурсивно (все подпапки 2024-01, 2024-02, …)
python transcribe_to_obsidian.py "D:\recordings" "D:\Obsidian\Audio Brain\00_inbox" --recursive

# С логом обработанных (манифест)
python transcribe_to_obsidian.py "D:\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --manifest D:\recordings\manifest.csv

# Перезапись уже существующих .md
python transcribe_to_obsidian.py "D:\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --overwrite

# Язык авто
python transcribe_to_obsidian.py "D:\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --language auto
```

**Параметры:**

- `input_dir` — каталог с `.mp3` (или корень при `--recursive`).
- `output_dir` — каталог для `.md` (например `D:\Obsidian\Audio Brain\00_inbox`).
- `--recursive` — обходить все подпапки; имена .md включают путь (напр. `2024-01_2024-01-15_001.md`), чтобы не было коллизий.
- `--manifest FILE` — дописывать в CSV лог: timestamp, путь к mp3, имя .md, дата из frontmatter.
- `--model`, `--device`, `--compute-type`, `--language` — как раньше.
- `--overwrite` — перезаписывать существующие .md.

Имя выходного `.md`: из имени mp3 (slug). При `--recursive` — из относительного пути (папка_имя), чтобы файлы из разных месяцев не перезаписывали друг друга.

## Формат вывода

Каждый `.md` соответствует шаблону транскрипта vault: `type: transcript`, `audio_file`, `date`, `status: inbox`, блок «Транскрипт» с текстом. Связь с записью — по полю `audio_file` (имя mp3). Заголовок и «Краткое резюме» можно заполнить в Obsidian после просмотра.
