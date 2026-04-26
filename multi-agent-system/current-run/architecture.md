# Architecture

## 1. Краткая связь с ТЗ

- **Source TZ:** `multi-agent-system/current-run/technical_specification.md` (`1.2-delta`).
- **MAS Project ID:** `audio-transcription-v1`.
- **Mode:** продолжение текущего MAS run без `mas-new-run`.
- **Цель:** локальный, повторно запускаемый конвейер `mp3 -> Markdown/Obsidian` для vault `Audio Brain`, с предсказуемым именованием, связью результата с исходником через `audio_file`, контролем покрытия и возможностью менять ASR backend только через provider abstraction и benchmark decision gate.

Архитектура остается простой: это однопользовательский Windows/Python-пайплайн без сервера и БД. Основной источник правды - файловая система: входные аудио в `recordings/YYYY-MM/`, выходные заметки в `00_inbox`, optional asset-директории и manifest. Дельта v1.2 добавляет не новую платформу, а границу между Core pipeline и ASR backend, чтобы Core/MAS Delivery не зависел напрямую от конкретной ASR-библиотеки или внешнего API.

```text
recordings/YYYY-MM/*.mp3
        |
        v
transcribe_to_obsidian.py
        |
        +-- naming helper / traversal / skip-overwrite / manifest
        |
        +-- ASR provider interface
        |       |
        |       +-- faster-whisper-local (default, local baseline)
        |       +-- future provider ids only behind benchmark gate
        |
        v
Audio Brain/00_inbox/*.md
optional: audio-work/<asset>/01_transcript__inbox.md + meta.json

check_coverage.py uses the same expected-name rules.
transcribe_gui.py remains a wrapper over the same CLI path.
```

## 2. Функциональные компоненты

### Core Transcription Pipeline

- **Назначение:** обработать папку или дерево аудиофайлов, пропустить уже готовые результаты без `--overwrite`, получить текст через ASR provider, собрать Markdown/frontmatter, записать inbox/asset outputs и manifest.
- **Основные файлы:** `transcription/transcribe_to_obsidian.py`, `transcription/check_coverage.py`, `transcription/transcribe_gui.py`, `transcription/README.md`, `transcription/SETUP.md`.
- **Инвариант:** Core отвечает за traversal, naming, idempotency, Markdown, assets, manifest и coverage-совместимость; ASR provider отвечает только за распознавание аудио и нормализацию результата в общий контракт.

### Naming and Coverage Layer

- **Назначение:** единое правило преобразования source audio в ожидаемое имя `.md` и asset identity.
- **Потребители:** `transcribe_to_obsidian.py` и `check_coverage.py`.
- **Требование:** если реализация затрагивает traversal, recursive mode, slug или output naming, правило должно быть общим helper-слоем или покрыто parity-проверкой между transcription и coverage. Это снижает риск ложных пропусков в `check_coverage.py`.

### ASR Provider Abstraction

- **Назначение:** единая точка подключения ASR backend для Core/MAS Delivery.
- **Планируемое размещение:** интерфейс и общие типы - отдельный модуль в `transcription/asr_providers/`; реализация `faster-whisper-local` - отдельный provider-модуль. `transcribe_to_obsidian.py` не должен импортировать или создавать `WhisperModel` напрямую.
- **Минимальная операция:** `transcribe(request) -> AsrResult` или явная ошибка provider-уровня.

`AsrRequest`:

- `audio_path`: абсолютный путь к локальному аудиофайлу.
- `language`: `ru`, `auto` или другой поддерживаемый код.
- `provider_id`: выбранный backend, например `faster-whisper-local`.
- `model`: логическое имя модели или профиля, например `large-v3`.
- `runtime_options`: provider-neutral параметры (`device`, `compute_type`, `beam_size`, `temperature`, `vad_filter`, `initial_prompt`, retry hints).
- `source_metadata`: исходное имя, relative path, expected output name, asset path, run/manifest context.

`AsrResult`:

- `text`: итоговый текст транскрипта.
- `segments`: optional timing/text segments, если backend их возвращает.
- `language_detected`: optional detected language.
- `duration_sec`: optional duration.
- `provider_id`, `provider_version`, `model`, `runtime_options_effective`.
- `quality_flags`: optional `empty_output`, `suspiciously_short`, `loop_risk`, `coherence_risk`, `needs_review`.
- `usage`: optional elapsed time, API status, quota/cost metadata для внешних providers.
- `artifacts`: optional paths to raw/debug provider artifacts.
- `created_at`: timestamp для manifest/meta traceability.

`AsrError` categories:

- `input_not_found` или unsupported format.
- `provider_unavailable` или initialization/import failure.
- `auth_or_quota` для API providers.
- `timeout_or_network` для API providers.
- `decode_failed` для model/runtime failures.
- `empty_or_invalid_result` если usable transcript отсутствует.
- `config_invalid` если provider/options несовместимы.

### faster-whisper-local Provider

- **Назначение:** текущая локальная baseline-реализация и default provider Core pipeline.
- **Backend:** `faster-whisper` / CTranslate2, default model `large-v3`, GPU path `device=cuda`, `compute_type=float16`, CPU fallback через `device=cpu`.
- **Граница:** provider мапит neutral request options в вызовы `faster-whisper` и возвращает `AsrResult`; остальной Core не знает о `WhisperModel`.

### Benchmark / ASR R&D Package

- **Назначение:** Worktree 2 валидирует ASR-кандидатов и передает Worktree 1 decision package, но не меняет Core delivery path напрямую.
- **Canonical artifacts:** `transcription/asr-benchmark/decision.md`, `transcription/asr-benchmark/results.csv`, `transcription/asr-benchmark/runs/*`, `memory-bank/creative/ws-026-worktree2-handoff.md`.
- **Current status:** Nexara остается рабочим кандидатом R&D, но наличие measured rows и текущих billing/environment blockers само по себе не переключает Core default.

### GUI Wrapper

- `transcribe_gui.py` может оставаться tkinter/subprocess-оберткой, но должен вызывать тот же CLI/Core path и не вводить отдельный ASR обход provider gate.

## 3. Системные компоненты и взаимодействия

### Main Flow

1. Пользователь запускает CLI или GUI wrapper с `input_dir`, `output_dir` и опциями.
2. Core находит аудиофайлы с учетом `--recursive`, `--ext`, `--existing-asset` и asset options.
3. Naming layer вычисляет expected inbox `.md` и asset identity.
4. Core пропускает существующий успешный результат, если не указан `--overwrite`.
5. Core выбирает provider из allowlist. Default для v1.2 - `faster-whisper-local`.
6. Core формирует `AsrRequest` и вызывает provider.
7. При успехе Core пишет Markdown transcript, optional asset transcript, `meta.json` и optional manifest row.
8. При ошибке Core не публикует успешный transcript. Для batch/recursive режима предпочтительное поведение - продолжить следующие файлы, зафиксировав статус ошибки в manifest/meta там, где такие артефакты включены. Если текущая CLI-реализация остается fail-fast на первом этапе, это допустимо только при сохранении инварианта: частичный успешный transcript не создается, а повторный запуск остается идемпотентным.
9. `check_coverage.py` отдельно сравнивает source files с expected `.md` по тем же naming rules.

### Provider Selection and Config

- Accepted provider ids должны быть allowlist, а не произвольной строкой из CLI.
- Default provider в Core v1.2: `faster-whisper-local`.
- Внешний/API provider может быть добавлен как disabled/experimental integration, но не становится production/default без свежего approved benchmark decision.
- Provider-specific secrets, endpoints, model names, billing settings и API tokens не должны попадать в Core business logic, committed config, Markdown transcripts или manifest.

### Benchmark Gate Consumption

Перед тем как Worktree 1 меняет default provider, включает provider-specific fallback routing или убирает локальный baseline, должны быть выполнены условия:

- `decision.md` существует и называет точный provider/profile.
- `results.csv` содержит строки для этого provider/profile с обязательными gate fields.
- Статус решения явно approved/accepted/pass for primary или эквивалентен этому для текущего профиля.
- Simulated-only, provisional, blocked, rejected, validation-in-progress или stale statuses не разрешают switch Core default.
- Decision package свежий для `audio-transcription-v1` v1.2-delta или явно помечен применимым к нему.
- Пакет содержит достаточно metadata для аудита: dataset/protocol, даты, known blockers, raw artifacts where available.

Если package отсутствует, устарел или заблокирован, Core сохраняет `faster-whisper-local` как default и может только держать другой provider за experimental flag.

### Documentation Compatibility

`README.md` и `SETUP.md` должны быть синхронизированы с этой архитектурой: operational default для Core v1.2 - `faster-whisper-local`; любые внешние/API providers описываются как экспериментальные или R&D до approved decision package. Документация не должна представлять Yandex/Deepgram/Nexara или другой API provider как production/default path без прохождения gate.

## 4. Модель данных

### Source Audio

- **Storage:** пользовательская папка, обычно `D:\1 ЗАПИСИ ГОЛОС\recordings\YYYY-MM\`.
- **Primary format:** `.mp3` для текущего прогона; другие форматы возможны только через явный `--ext`/config.
- **Recommended name:** `YYYY-MM-DD_NNN[_label].mp3`.
- **Derived fields:** `source_basename`, `relative_path`, `date`, `sequence`, `label`, `slug`, `expected_md_name`, optional `asset_id`.

### Transcript Markdown

- **Location:** `D:\Obsidian\Audio Brain\00_inbox\` или другой `output_dir`, переданный пользователем.
- **Name:** deterministic `.md` name from source name; recursive mode must encode enough relative-path context to avoid collisions.
- **Required frontmatter:** `type: transcript`, `source: audio`, `audio_file`, `phase: A`, `date`, `status: inbox`.
- **Optional frontmatter:** `asset_path`, `tags`, `links`, `asr_provider`, `asr_model`, `quality_flags`.
- **Body sections:** heading/title, short summary placeholder if used by existing template, section `Транскрипт`.
- **Relation:** `audio_file` stores the source basename; `asset_path` links to asset mode if enabled.

### Asset Mode

- **Asset directory:** `<asset-root>/<YYYY-MM>/<YYYY-MM-DD>_<NNN>_<slug>__src-<YYYYMMDD>/`.
- **Core files:** source audio copy/move/reference, `01_transcript__inbox.md`, `meta.json`.
- **Optional publication:** inbox copy unless `--no-publish-inbox`.
- **meta.json required fields:** `phase`, `audio_file`, `source_audio_path`, `asset_path`, `created_at`, `updated_at`, `versions[]`.
- **ASR metadata extension:** `asr_provider`, `asr_model`, `asr_runtime`, `asr_status`, optional `asr_artifacts`, optional `quality_flags`, optional `error` for failed provider runs.

### Manifest

- **Non-asset fields:** `timestamp`, `mp3_path`, `md_name`, `date`.
- **Asset/existing-asset fields:** `timestamp`, `mp3_path`, `asset_dir`, `transcript_file`, `inbox_md`, `date`, `source_action`.
- **Provider extension fields:** append-only columns such as `asr_provider`, `asr_model`, `asr_status`, `error_category`, `elapsed_sec`. Existing columns remain stable.

### Benchmark Decision Package

`results.csv` Core-readable columns:

- `file_id`, `duration_min`, `noise`, `engine`.
- Gate fields: `A_loops`, `A_empty`, `A_coherence`, `A_pass`.
- Operational fields: `post_edit_min_per_10`, `punctuation_1_5`, `terms_1_5`, `notes`.
- Rows must distinguish real/measured data from simulated, blocked or dry-run rows.

`decision.md` required content:

- scope/protocol and dataset reference.
- candidate engines and recommendation.
- aggregate pass/fail and threshold interpretation.
- freshness date and final/approved/provisional/blocked/rejected status.
- known blockers such as missing API key, quota/billing or runtime errors.
- links/paths to raw run artifacts where available.

## 5. Внешние и внутренние интерфейсы

### CLI

- Main CLI: `python transcribe_to_obsidian.py <input_dir> <output_dir> [options]`.
- Preserved options: `--recursive`, `--manifest`, `--overwrite`, `--model`, `--device`, `--compute-type`, `--language`, `--asset-root`, `--copy-source`, `--move-source`, `--no-publish-inbox`, retry/decoding options.
- Future `--provider`, if added, selects only allowlisted provider ids and passes normalized options through the abstraction.

### Provider Interface

- Internal Python interface under `transcription/asr_providers/`.
- Core-facing operation: transcribe one local audio file and return normalized result/error.
- Provider-specific network/API calls, SDKs, auth and raw response parsing stay inside provider implementation modules.

### File Interfaces

- Inputs and outputs are local filesystem paths.
- No HTTP server/API is exposed by Core.
- Obsidian integration is file-based: generated Markdown is written into vault directories.
- External ASR APIs are allowed only inside explicitly enabled provider implementations and only when the benchmark gate permits operational use.

### Worktree Handoff Interface

- Worktree 2 produces benchmark artifacts and recommendation documents.
- Worktree 1 owns Core integration, provider enablement, docs compatibility and acceptance checks.
- Direct Worktree 2 changes to Markdown generation, asset naming, coverage logic or default provider behavior are out of contract unless reviewed and accepted by Worktree 1.

## 6. Технологический стек

- **Runtime:** Python 3.10+ on Windows 10/11.
- **Current local ASR:** `faster-whisper`, CTranslate2, model `large-v3`.
- **GPU path:** NVIDIA CUDA, `device=cuda`, `compute_type=float16`, RTX 3060-class 6+ GB VRAM.
- **CPU fallback:** supported but slower.
- **GUI:** stdlib tkinter/subprocess wrapper.
- **Storage:** local filesystem and Obsidian vault directories.
- **Artifacts:** Markdown, JSON `meta.json`, CSV manifest, CSV/Markdown benchmark package.
- **Smoke testing:** PowerShell help/smoke commands that do not download the model.

## 7. Безопасность и ограничения

- Base Core pipeline is local/offline and does not require secrets.
- Audio must not be uploaded to external services unless a non-local provider is explicitly selected, configured and benchmark-approved for the current run.
- API keys/tokens must live in environment variables or ignored local config, never in git, manifests, `meta.json` or generated notes.
- Idempotency is mandatory: existing successful transcripts are not overwritten without `--overwrite`.
- Failed provider output must not be represented as a successful transcript.
- Out of scope for this run: Ghost/CMS publishing, n8n publishing flows, mandatory LLM/manual content editing as a condition for Phase A success.

## 8. Развертывание и миграции

- **Install:** create venv under `transcription/.venv`, install `transcription/requirements.txt`, first real `faster-whisper` run downloads `large-v3`.
- **Smoke check:** `transcription/run-smoke-test.ps1` verifies CLI/help paths without downloading the model.
- **Migration from current code:** introduce provider boundary without changing default behavior, Markdown shape, naming rules, manifest compatibility or existing asset semantics.
- **Compatibility guards:**
  - existing `00_inbox/*.md` remain valid.
  - existing asset directories and `meta.json` remain valid.
  - manifest readers tolerate append-only columns.
  - `check_coverage.py` remains aligned with Core naming.
  - `transcribe_gui.py` remains a wrapper over the same CLI path.
  - Core default remains `faster-whisper-local` until approved decision package explicitly permits another provider/profile.

## 9. Открытые вопросы

- **Blocking:** none.
- **Non-blocking:** Worktree 2 still needs a fresh approved benchmark decision before Core can switch default ASR provider away from `faster-whisper-local`.
- **Non-blocking:** final implementation should choose and document exact batch error policy if it differs from the preferred continue-and-record-error behavior above.
