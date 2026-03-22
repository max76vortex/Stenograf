# Скрипты workspace (журнал активности)

## `append-activity-journal.ps1`

Дописывает строку в `memory-bank/activity-journal.md` с **локальным** ISO-временем.

Из корня репозитория:

```powershell
pwsh -NoLogo -File "scripts/append-activity-journal.ps1" -Message "Кратко: что сделали"
```

Параметр `-Source`: `Manual` (по умолчанию), `GitCommit`, `Scheduled`.

## `Get-ActivityReport.ps1`

Печатает в консоль **хвост журнала** + **`git log`** за последние N дней (по умолчанию 7).

```powershell
pwsh -NoLogo -File "scripts/Get-ActivityReport.ps1"
pwsh -NoLogo -File "scripts/Get-ActivityReport.ps1" -SinceDays 1 -JournalLines 100
```

## Хук Git (post-commit)

Чтобы после каждого коммита автоматически дописывалась строка в журнал:

```powershell
cd <корень репозитория>
git config core.hooksPath .githooks
```

Хук: `.githooks/post-commit` (в репозитории уже есть). Требуется `pwsh` в PATH и `git`.

Отключить: `git config --unset core.hooksPath` (или удалить настройку).

## Планировщик задач Windows (опционально)

Раз в день «напоминание» без нагрузки — один запуск:

```powershell
pwsh -NoLogo -File "C:\path\to\<repo>\scripts\append-activity-journal.ps1" -Message "Ежедневная отметка: сессия" -Source Scheduled
```

Создай задачу в `taskschd.msc` с этой командой и рабочей папкой = корень репозитория.
