# Tasks
## Current Task
- Status: IN_PROGRESS
- Complexity: 3
- Description: **Фаза 1 — Транскрибация:** порядок в папке записей и в пайплайне, готовые .md в 00_inbox. Фаза 2 (постинг, Ghost) — после появления материалов, готовых к публикации.

## Phase 1 — Транскрибация (сейчас)

### Plan / Checklist
- [x] Спроектировать структуру Obsidian-vault и шаблоны (транскрипт, идеи, статья, проект).
- [x] Выбрать инструмент транскрибации (faster-whisper large-v3, скрипт transcription/).
- [x] Спроектировать порядок и рабочий процесс: папка записей (recordings/YYYY-MM/), именование mp3 (YYYY-MM-DD_NNN[_метка].mp3), выход в 00_inbox, связь по audio_file (creative-transcription-workflow.md).
- [x] Реализовать в скрипте: рекурсивный обход подпапок (--recursive), опциональный манифест (--manifest) для лога обработанных файлов.
- [x] Задокументировать в transcription/README.md структуру папки записей и шаблон имён; примеры запуска по папке месяца и по корню recordings.
- [ ] (Опционально) Утилита или инструкция для проверки «какие mp3 ещё без .md» / отчёт по манифесту.

## Phase 2 — Постинг (позже, когда есть материалы к публикации)

- [ ] Выбрать реализацию интеграции Obsidian ↔ Ghost (скрипт/сервис/n8n).
- [ ] Реализовать поток Obsidian → Ghost (создание/обновление постов по article-draft, запись ghost_id в frontmatter).
- [ ] Реализовать поток Ghost → Obsidian (периодическая синхронизация статусов + валидация записи в файле).
- [ ] Протестировать полный цикл на 1–2 статьях.

## Supporting Tooling — Multi-Agent System

- [x] Собрать локальный комплект ролей в `multi-agent-system/agents/` для оркестратора и агентов 02-09.
- [x] Создать рабочую зону `multi-agent-system/` со статусом, активным прогоном, шаблонами и runbook'ами.
- [x] Зафиксировать contracts, acceptance checklists и e2e-flow варианта B.
- [x] Реализовать `Blocking Questions Resolver` и `Run Artifacts Indexer` (Task 03) для CLI `dryrun-status.ps1`.
- [x] Выполнить `Task 04` (тесты и сценарии деградации) для CLI `dryrun-status.ps1`.
- [x] Выполнить `Task 05` (документация/runbook) для CLI `dryrun-status.ps1`.
- [x] Выполнить `Task 06` (real E2E) через Cursor CLI, чтобы проверить работу всех агентов на “живых” задачах.
- [x] Установить и проверить Cursor CLI (`agent`/`cursor-agent` entrypoint доступен через локальный путь `AppData\\Local\\cursor-agent`).

## Backlog / Future Projects

- [ ] Спроектировать универсальный модуль `Supervisor/Sentinel` (вне одного проекта): протокол heartbeat/lease, SLA no-progress, escalation policy, states `DEGRADED/STALLED/ESCALATED`, интеграция как отдельный агент-наблюдатель в мультиагентный контур.
- [ ] Спроектировать отдельного субагента `Delivery Observer / Project Documenter`: наблюдает за ключевыми субагентами (01 + контрольные роли review/dev), собирает артефакты и автоматически формирует полноценную итоговую документацию по проделанной работе и проекту; за базовый шаблон взять `memory-bank/archive/Архив - мультиагентная система Variant B.md`.
