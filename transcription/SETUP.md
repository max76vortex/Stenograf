# Установка и настройка транскрибации на компьютере

Пошагово: что установить, где что лежит, как связать папку записей, скрипт и vault Obsidian.

---

## 1. Что где лежит (схема)

| Назначение | Путь (пример) |
|------------|----------------|
| **Проект (скрипт транскрибации)** | `C:\Users\sa\N8N-projects\transcription\` |
| **Папка с записями mp3** | `D:\1 ЗАПИСИ ГОЛОС\recordings\` с подпапками `2024-01`, `2024-02`, … |
| **Vault Obsidian (Audio Brain)** | `D:\Obsidian\Audio Brain\` |
| **Куда пишутся .md транскриптов** | `D:\Obsidian\Audio Brain\00_inbox\` |
| **Виртуальное окружение Python** | `C:\Users\sa\N8N-projects\transcription\.venv\` |
| **Манифест (лог обработанных)** | по желанию, например `D:\1 ЗАПИСИ ГОЛОС\recordings\manifest.csv` |

Связь «одно с другим»: ты один раз задаёшь пути в команде запуска: папка с mp3 → вход скрипта, `00_inbox` → выход. Скрипт ничего не «подключает» в настройках — только читает из одной папки и пишет в другую.

---

## 2. Что нужно установить

### 2.1. Windows

Обычная рабочая Windows 10/11. Ниже команды для PowerShell или cmd.

### 2.2. Драйвер видеокарты NVIDIA

- Уже должен стоять, если видеокарта используется.
- Проверка: открой «Диспетчер устройств» → «Видеоадаптеры» → NVIDIA RTX 3060 без жёлтого значка.
- Обновить при необходимости: [nvidia.com/drivers](https://www.nvidia.com/drivers) — выбрать RTX 3060, скачать и установить.

### 2.3. CUDA / GPU на Windows (без полного CUDA Toolkit)

faster-whisper на GPU (через **ctranslate2**) ищет библиотеку **cuBLAS** (`cublas64_12.dll`). Полный **CUDA Toolkit** в `Program Files` не обязателен, если:

1. Установлен актуальный **драйвер NVIDIA** (см. п. 2.2).
2. В venv выполнен `pip install -r requirements.txt` — для Windows подтягивается пакет **`nvidia-cublas-cu12`** (cuBLAS для CUDA 12 в `site-packages`).
3. Скрипт **`transcribe_to_obsidian.py`** сам добавляет `…\site-packages\nvidia\cublas\bin` в `PATH` перед загрузкой модели, чтобы DLL находились без ручной настройки.

Если при `--device cuda` всё же ошибка про отсутствующий `cublas64_12.dll` — проверь, что пакет установлен:  
`pip show nvidia-cublas-cu12`.

**Опционально:** полный [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) (11 или 12) — если нужен `nvcc` для других задач; путь к `…\CUDA\v12.x\bin` тогда можно добавить в PATH системы.

Если хочешь только CPU (без GPU): CUDA не нужен; при запуске укажи `--device cpu` (будет медленнее).

### 2.4. Python 3.10 или новее

- Скачать: [python.org/downloads](https://www.python.org/downloads/) — установить, **галочка «Add Python to PATH»** обязательна.
- Проверка (новый терминал):  
  `python --version`  
  Должно быть 3.10 или выше.

### 2.5. Ничего больше ставить не нужно

Модель large-v3 скрипт скачает сам при первом запуске (несколько ГБ). Логика «скачать/подключить» встроена в библиотеку faster-whisper.

---

## 3. Папка с записями

### 3.1. Создать структуру

На диске, где хранятся записи (например `D:\`):

1. Создать папку, например: `D:\1 ЗАПИСИ ГОЛОС\recordings\`.
2. Внутри — подпапки по месяцам: `2024-01`, `2024-02`, …, `2025-03` и т.д. (имена вида `YYYY-MM`).

Итог:

```
D:\1 ЗАПИСИ ГОЛОС\recordings\
  2024-01\
  2024-02\
  2024-03\
  ...
```

В каждую папку класть mp3 за соответствующий месяц.

### 3.2. Имена файлов

Рекомендуемый формат: **`YYYY-MM-DD_NNN[ _метка].mp3`**

- Дата: `2024-03-15`
- Номер в день: `001`, `002`, …
- По желанию: `_краткая-метка` (латиница/цифры/дефис).

Примеры:  
`2024-03-15_001.mp3`, `2024-03-15_002_idei-produkt.mp3`.

Если старые файлы уже с другими именами — можно оставить; скрипт возьмёт дату из даты изменения файла. Для предсказуемого порядка лучше со временем переименовать по шаблону.

---

## 4. Obsidian и vault Audio Brain

- Vault уже должен быть: `D:\Obsidian\Audio Brain\`.
- В нём уже есть папка `00_inbox\` (мы её создавали ранее).  
Именно в неё скрипт будет писать .md файлы.  
Проверь, что путь существует: `D:\Obsidian\Audio Brain\00_inbox\`.

---

## 5. Установка окружения транскрибации (один раз)

Все команды — в PowerShell или cmd, из папки проекта.

1. Перейти в папку скрипта:

   ```powershell
   cd C:\Users\sa\N8N-projects\transcription
   ```

2. Создать виртуальное окружение:

   ```powershell
   python -m venv .venv
   ```

3. Активировать его:

   ```powershell
   .venv\Scripts\activate
   ```

   В начале строки должно появиться `(.venv)`.

4. Установить зависимость:

   ```powershell
   pip install -r requirements.txt
   ```

   Установится faster-whisper (и при необходимости зависимости для CUDA). При первом запуске скрипта дополнительно скачается модель large-v3 — это нормально.

---

## 6. Как запускать (связать папки одной командой)

После активации `.venv` скрипт вызывается так:  
**первый аргумент** — папка с mp3, **второй** — папка для .md (00_inbox).

### Вариант 1: одна папка месяца

```powershell
cd C:\Users\sa\N8N-projects\transcription
.venv\Scripts\activate
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox"
```

Обработаются только файлы из `D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03\`, результаты появятся в `D:\Obsidian\Audio Brain\00_inbox\`.

### Вариант 2: все месяцы (рекурсивно)

```powershell
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings" "D:\Obsidian\Audio Brain\00_inbox" --recursive
```

Скрипт обойдёт все подпапки (`2024-01`, `2024-02`, …) и запишет .md в тот же `00_inbox`. Имена .md будут содержать префикс папки (например `2024-01_2024-01-15_001.md`), чтобы не было пересечений.

### Вариант 3: с логом (манифест)

```powershell
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --manifest "D:\1 ЗАПИСИ ГОЛОС\recordings\manifest.csv"
```

В `D:\1 ЗАПИСИ ГОЛОС\recordings\manifest.csv` будет дописываться лог: когда какой файл обработан, какое имя .md, какая дата во frontmatter.

### Вариант 4: без GPU (только CPU)

Если CUDA не ставил или хочешь запустить без видеокарты:

```powershell
python transcribe_to_obsidian.py "D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03" "D:\Obsidian\Audio Brain\00_inbox" --device cpu
```

Будет заметно медленнее, но без видеокарты и драйверов.

---

## 7. Удобный запуск (без ввода длинных путей)

Можно один раз прописать свои пути в bat-файл или скрипт и потом только его запускать.

**Пример `transcribe_month.bat`** в папке `transcription\`:

```batch
@echo off
set RECORDINGS=D:\1 ЗАПИСИ ГОЛОС\recordings
set INBOX=D:\Obsidian\Audio Brain\00_inbox
call .venv\Scripts\activate.bat
python transcribe_to_obsidian.py "%RECORDINGS%\2024-03" "%INBOX%" --manifest "%RECORDINGS%\manifest.csv"
pause
```

Пути `RECORDINGS` и `INBOX` поменяй под себя; при необходимости замени `2024-03` на другой месяц или используй отдельный bat для рекурсивного запуска по всему `%RECORDINGS%` с `--recursive`.

---

## 8. Проверка, что всё связано правильно

1. В папке записей лежат mp3 (например в `D:\1 ЗАПИСИ ГОЛОС\recordings\2024-03\`).
2. Запускаешь команду из п. 6 (с своими путями).
3. В `D:\Obsidian\Audio Brain\00_inbox\` появляются .md с именами, похожими на имена mp3.
4. В Obsidian открываешь vault Audio Brain → папка 00_inbox — там новые заметки с полем `audio_file` и блоком «Транскрипт».

Если .md не появляются: проверь, что второй аргумент команды — именно папка `00_inbox` (слеш в конце не обязателен), и что прав на запись в неё есть.

---

## 9. Краткий чеклист

- [ ] Установлены: драйвер NVIDIA, CUDA Toolkit (если используешь GPU), Python 3.10+.
- [ ] Создана папка записей (например `D:\1 ЗАПИСИ ГОЛОС\recordings\`) и подпапки по месяцам (`YYYY-MM`).
- [ ] Vault Audio Brain и папка `00_inbox` существуют (`D:\Obsidian\Audio Brain\00_inbox`).
- [ ] В `C:\Users\sa\N8N-projects\transcription\` выполнены: `python -m venv .venv`, `activate`, `pip install -r requirements.txt`.
- [ ] Запуск: `python transcribe_to_obsidian.py "<папка_mp3>" "D:\Obsidian\Audio Brain\00_inbox"` (при необходимости с `--recursive` или `--manifest`).
- [ ] После первого запуска проверены появления .md в 00_inbox и открытие их в Obsidian.

После этого «всё на компьютере» установлено и связано: записи в своей папке, скрипт в проекте, результат — в Obsidian.

---

## 10. Новые записи с телефона через Google Drive

Если запись сделана на диктофон телефона и загружена в Google Drive, её можно включить в тот же поток:

1. Скачай новые файлы из нужной папки Google Drive в локальную папку, например  
   `D:\1 ЗАПИСИ ГОЛОС\phone-import\`.
2. Запусти import-скрипт:

   ```powershell
   python ingest_phone_recordings.py `
     "D:\1 ЗАПИСИ ГОЛОС\phone-import" `
     "D:\1 ЗАПИСИ ГОЛОС\recordings" `
     --recursive --log-file "D:\1 ЗАПИСИ ГОЛОС\recordings\phone_ingest_log.csv"
   ```

3. Скрипт сам:
   - разложит файлы по `recordings\YYYY-MM\`;
   - нормализует имя в формат `YYYY-MM-DD_NNN_phone-...`;
   - не создаст дубликаты (sha256 + реестр);
   - обновит `phone_ingest_log.csv`.

4. Сразу после импорта можно автозапустить транскрибацию в текущий пайплайн:

   ```powershell
   python ingest_phone_recordings.py `
     "D:\1 ЗАПИСИ ГОЛОС\phone-import" `
     "D:\1 ЗАПИСИ ГОЛОС\recordings" `
     --recursive `
     --trigger-transcribe `
     --transcribe-script "C:\Users\sa\N8N-projects\transcription\transcribe_to_obsidian.py" `
     --inbox-dir "D:\Obsidian\Audio Brain\00_inbox" `
     --transcribe-asset-root "D:\1 ЗАПИСИ ГОЛОС\audio-work" `
     --transcribe-recursive
   ```

После этого новые телефонные записи проходят те же фазы (`00_inbox` → assets → Phase B), что и записи с компьютера.

---

## 11. Phase B в этом проекте (фиксированный способ)

В `N8N-projects` Phase B зафиксирована как единый путь:

- skill: `.cursor/skills/phase-b-process/SKILL.md`
- модель: `kimi-k2.5`
- backend в `meta.json`: `cursor`

Старые альтернативы через `phase_b_processor.py`, Ollama и LM Studio считаются архивными и для рабочих прогонов не используются.

---

## 12. Автобатчинг под лимиты бесплатной транскрибации

Для Phase A добавлен диспетчер очереди:

```powershell
python transcription_limit_dispatcher.py --help
```

Назначение:
- режет входные файлы на партии под лимиты;
- после исчерпания лимита ждёт следующее окно;
- сразу отправляет следующую партию, когда лимит открывается.

Базовый профиль по умолчанию: **Groq Whisper Free**  
(`20 RPM`, `2000 RPD`, `7200 audio sec/hour`, `28800 audio sec/day`, `max 25 MB`).
