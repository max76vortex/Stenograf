# Status Surface Runbook (вариант B)

## Назначение

Runbook объясняет, как оператору проверить состояние активного dry run прогона
мультиагентной системы через CLI:

- текущая точка `System State`;
- наличие/отсутствие блокирующих вопросов (`Blocking Questions`);
- последние артефакты активного прогона (`Last Artifacts`).

## Команда запуска

Из корня workspace (`N8N-projects`):

```powershell
pwsh -NoLogo -File "multi-agent-system/tools/dryrun-status.ps1" -Top 10
```

`-Top` ограничивает количество элементов в блоке `Last Artifacts`.

## Как читать отчёт

Отчёт всегда содержит 3 блока:

1. `--- System State ---`
   - `Variant` — версия/вариант подсистемы (сейчас `B`);
   - `Status` — ожидание подтверждения или другой этап;
   - `Current stage`, `Current iter.`, `Active task`, `Last updated by`;
   - `Next exp. step` — следующий ожидаемый шаг оркестратора;
   - `Confirmed stages` — список этапов, подтвержденных пользователем (по `- [x]` из `status.md`).

2. `--- Blocking Questions ---`
   - `Final status`:
     - `HAS_BLOCKERS` — в первичном источнике `open_questions.md` явно размечены блокирующие элементы;
     - `NO_BLOCKERS` — блокеров нет (либо явный маркер “нет открытых вопросов”, либо совпадающий fallback);
     - `UNKNOWN` — не удалось однозначно определить блокеры (например, нет маркеров `BLOCKER` и нет явного “no open questions”).
   - `Source used`:
     - `OPEN_QUESTIONS_PRIMARY` — первичный источник `current-run/open_questions.md`;
     - `STATUS_FALLBACK` — fallback из `multi-agent-system/status.md` (`## Open Questions Summary`).
   - `Diagnostics` — пояснения, почему выбран именно такой итог.

3. `--- Last Artifacts ---`
   - список последних `.md` файлов из `multi-agent-system/current-run/**`;
   - служебные `README.md` автоматически исключаются;
   - отсортировано по `mtime` (новее → старее);
   - tie-break при равном времени: лексикографический порядок пути;
   - если артефактов нет или каталог отсутствует — выводится явное сообщение.

## Что делать оператору

1. Если `Final status : HAS_BLOCKERS`
   - откройте `multi-agent-system/current-run/open_questions.md`;
   - устраните/ответьте на блокирующие вопросы;
   - после этого снова запустите `dryrun-status.ps1`.

2. Если `Final status : NO_BLOCKERS`
   - можно продолжать следующий крупный этап dry run (по runbook’у этапа).

3. Если `Final status : UNKNOWN`
   - сначала проверьте содержимое `open_questions.md`;
   - посмотрите `Diagnostics` и `Source used`;
   - если нужно — уточните трактовку блокеров пользователем и/или обновите `Open Questions Summary` в `status.md`.

## Параметры и коды выхода

- Основной параметр: `-Top` (алиас: `-Limit`).
- Override-параметры для тестов/диагностики:
  - `-StatusFilePathOverride` (алиас: `-StatusPath`)
  - `-OpenQuestionsFilePathOverride` (алиас: `-OpenQuestionsPath`)
  - `-CurrentRunDirectoryOverride` (алиас: `-RunPath`)
- Exit code:
  - `0` — отчет успешно собран и выведен;
  - `1` — критическая ошибка (например, модуль не импортирован или не удалось собрать отчет).

В обычной операторской работе override-параметры обычно не требуются.

