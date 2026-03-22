<#
.SYNOPSIS
  Выводит сводку для отчёта: хвост журнала + git log (по желанию). Без фоновых процессов.

.PARAMETER SinceDays
  За сколько последних дней смотреть git log (по умолчанию 7).

.PARAMETER JournalLines
  Сколько последних строк журнала показать (по умолчанию 40).

.EXAMPLE
  pwsh -File scripts/Get-ActivityReport.ps1

.EXAMPLE
  pwsh -File scripts/Get-ActivityReport.ps1 -SinceDays 1 -JournalLines 80
#>
[CmdletBinding()]
param(
    [int]$SinceDays = 7,
    [int]$JournalLines = 40
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Читаем журнал как UTF-8; для консоли Windows — UTF-8 вывод
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

if (-not $PSScriptRoot) { throw 'PSScriptRoot required.' }
$repoRoot = Split-Path -Parent $PSScriptRoot
$journalPath = Join-Path $repoRoot 'memory-bank\activity-journal.md'

Push-Location $repoRoot
try {
    Write-Host '=== Activity journal (tail) ===' -ForegroundColor Cyan
    if (Test-Path -LiteralPath $journalPath) {
        Get-Content -LiteralPath $journalPath -Tail $JournalLines -Encoding UTF8
    }
    else {
        Write-Host '(journal file not created yet)' -ForegroundColor DarkGray
    }

    Write-Host ''
    Write-Host "=== Git log (last $SinceDays days) ===" -ForegroundColor Cyan
    $since = (Get-Date).AddDays(-$SinceDays).ToString('yyyy-MM-dd')
    git -C $repoRoot log --since="$since" --pretty=format:'%h %ad %s' --date=iso 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host '(git log failed or not a repo)' -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}
