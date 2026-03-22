<#
.SYNOPSIS
  Дописывает строку в memory-bank/activity-journal.md с локальным ISO-временем.

.EXAMPLE
  pwsh -File scripts/append-activity-journal.ps1 -Message "Ручная заметка"

.EXAMPLE
  pwsh -File scripts/append-activity-journal.ps1 -Message "git: feat foo" -Source GitCommit
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Message,

    [ValidateSet('Manual', 'GitCommit', 'Scheduled')]
    [string]$Source = 'Manual'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $PSScriptRoot) {
    throw 'Run this script as a file (PSScriptRoot required).'
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$journalPath = Join-Path $repoRoot 'memory-bank\activity-journal.md'
$ts = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fffzzz')
$line = "- ``$ts`` [$Source] $Message"

if (-not (Test-Path -LiteralPath $journalPath)) {
    $header = @"
# Activity journal

Краткий лог для отчётов по запросу (агент/человек). Формат: локальное ISO-время, источник, текст.

- Ручная запись: ``pwsh -File scripts/append-activity-journal.ps1 -Message \"...\"``
- После коммитов: `git config core.hooksPath .githooks` и хук `post-commit` (см. `scripts/README.md`)
- Отчёт: скилл **workspace-activity-report** или ``pwsh -File scripts/Get-ActivityReport.ps1``

## Entries

"@
    $utf8Bom = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($journalPath, $header + [Environment]::NewLine, $utf8Bom)
}

$utf8 = New-Object System.Text.UTF8Encoding $true
[System.IO.File]::AppendAllText($journalPath, $line + [Environment]::NewLine, $utf8)
Write-Host "OK: $journalPath" -ForegroundColor Green
