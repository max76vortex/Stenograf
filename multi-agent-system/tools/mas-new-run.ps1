<#
.SYNOPSIS
  Готовит чистый старт MAS (Variant B): бэкап current-run, сброс status.md, заготовки task_brief / project_context / open_questions, удаление артефактов прошлого прогона.

.DESCRIPTION
  Запуск из корня workspace:
    pwsh -NoLogo -File "multi-agent-system/tools/mas-new-run.ps1" -MasProjectId "my-feature-slug"

  Обязательный уникальный slug (kebab-case) для будущей архивации — см. runbooks/mas-archive-policy.md

.PARAMETER MasProjectId
  Уникальный идентификатор прогона (латиница, цифры, дефисы), например: audio-pipeline-v2

.PARAMETER ActiveTaskLabel
  Короткая метка для поля Active task в status.md (по умолчанию = MasProjectId)

.PARAMETER NoBackup
  Не копировать current-run в archive/mas-snapshots/ (рискованно)

.PARAMETER Force
  Не спрашивать подтверждение в консоли (для CI/скриптов)

.EXAMPLE
  pwsh -File multi-agent-system/tools/mas-new-run.ps1 -MasProjectId "next-task-2026"
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z][a-z0-9]*(-[a-z0-9]+)*$')]
    [string]$MasProjectId,

    [string]$ActiveTaskLabel = '',

    [switch]$NoBackup,

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $PSScriptRoot) {
    throw 'PSScriptRoot is not set. Run this script from file (not as dot-sourced bare string).'
}
$masRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Split-Path -Parent $masRoot
$currentRun = Join-Path $masRoot 'current-run'
$snapRoot = Join-Path $masRoot 'archive\mas-snapshots'
$statusTemplate = Join-Path $masRoot 'templates\status.initial.template.md'

if (-not (Test-Path -LiteralPath $currentRun)) {
    throw "current-run not found: $currentRun"
}
if (-not (Test-Path -LiteralPath $statusTemplate)) {
    throw "status template missing: $statusTemplate"
}

$label = $MasProjectId
if ($ActiveTaskLabel) {
    $label = $ActiveTaskLabel
}

if (-not $Force -and -not $WhatIf -and -not $PSCmdlet.ShouldContinue(
        "Будет подготовлен чистый прогон MAS. Текущий current-run будет скопирован в archive/mas-snapshots (если не -NoBackup), затем артефакты удалены и перезаписаны. Продолжить?",
        'MAS clean start')) {
    Write-Host 'Cancelled.' -ForegroundColor Yellow
    exit 2
}

$timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$snapshotName = "${timestamp}_${MasProjectId}_previous"
$snapshotPath = Join-Path $snapRoot $snapshotName

if (-not $NoBackup) {
    if (-not (Test-Path -LiteralPath $snapRoot)) {
        New-Item -ItemType Directory -Path $snapRoot -Force | Out-Null
    }
    if ($PSCmdlet.ShouldProcess($snapshotPath, 'Copy-Item current-run snapshot')) {
        Copy-Item -LiteralPath $currentRun -Destination $snapshotPath -Recurse -Force
        Write-Host "[OK] Backup: $snapshotPath" -ForegroundColor Green
    }
}
else {
    Write-Host '[WARN] Backup skipped (-NoBackup).' -ForegroundColor Yellow
}

# --- Remove previous run artifacts (keep README.md in subfolders) ---
$rootMdToRemove = @(
    'technical_specification.md',
    'architecture.md',
    'plan.md'
)
foreach ($name in $rootMdToRemove) {
    $p = Join-Path $currentRun $name
    if (Test-Path -LiteralPath $p) {
        if ($PSCmdlet.ShouldProcess($p, 'Remove')) {
            Remove-Item -LiteralPath $p -Force
        }
    }
}

foreach ($sub in @('tasks', 'reviews', 'reports')) {
    $dir = Join-Path $currentRun $sub
    if (-not (Test-Path -LiteralPath $dir)) { continue }
    Get-ChildItem -LiteralPath $dir -Filter '*.md' -File | ForEach-Object {
        if ($_.Name -eq 'README.md') { return }
        if ($PSCmdlet.ShouldProcess($_.FullName, 'Remove')) {
            Remove-Item -LiteralPath $_.FullName -Force
        }
    }
}

# --- Write fresh files ---
$taskBrief = @"
# Task Brief

## Задача

(TODO: кратко опишите задачу для нового прогона MAS.)

## Цель

(TODO: что должно быть на выходе.)

## Критерии успеха

- (TODO)

## Scope

- Входит: (TODO)
- Не входит: (TODO)

## Ограничения

- (TODO: стек, сроки, «нельзя трогать»)
"@

$projectContext = @'
# Project Context

**MAS Project ID:** `{0}`

## Workspace

- Name: (TODO: имя репозитория / продукта)
- Repository root: `{1}`

## Описание проекта

(TODO: 2–5 предложений — зачем этот прогон.)

## Стек и ограничения

(TODO)

## Структура репозитория

(TODO: важные папки от корня workspace.)

## Ссылки

- Промпты ролей: `multi-agent-system/agents/`
- Глобальный статус: `multi-agent-system/status.md`
- Артефакты прогона: `multi-agent-system/current-run/`
'@ -f $MasProjectId, $workspaceRoot

$openQuestions = @"
# Open Questions

Список блокирующих вопросов по текущему прогону.

## Status

- No open questions yet.
"@

$statusContent = Get-Content -LiteralPath $statusTemplate -Raw -Encoding UTF8
$statusContent = $statusContent.Replace('{{ACTIVE_TASK}}', $label)
$statusContent = $statusContent.Replace('{{MAS_PROJECT_ID}}', $MasProjectId)
$statusContent = $statusContent.Replace('{{TIMESTAMP}}', (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'))

$write = {
    param([string]$Path, [string]$Content)
    if ($PSCmdlet.ShouldProcess($Path, 'Set-Content')) {
        Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8 -NoNewline:$false
    }
}

& $write (Join-Path $currentRun 'task_brief.md') $taskBrief
& $write (Join-Path $currentRun 'project_context.md') $projectContext
& $write (Join-Path $currentRun 'open_questions.md') $openQuestions
& $write (Join-Path $masRoot 'status.md') $statusContent

if ($WhatIf) {
    Write-Host ''
    Write-Host 'WhatIf: preview only — файлы не изменены.' -ForegroundColor Yellow
    exit 0
}

Write-Host ''
Write-Host 'MAS clean start complete.' -ForegroundColor Cyan
Write-Host "  MAS Project ID: $MasProjectId"
Write-Host '  status.md + task_brief.md + project_context.md + open_questions.md updated.'
if (-not $NoBackup) {
    Write-Host "  Snapshot: $snapshotPath"
}
Write-Host ''
Write-Host 'Next: edit current-run/task_brief.md and project_context.md, then:' -ForegroundColor DarkGray
Write-Host '  pwsh -File multi-agent-system/tools/orchestrator-preflight.ps1' -ForegroundColor DarkGray
Write-Host '  .\multi-agent-system\start-orchestrator.ps1 -Model "auto"' -ForegroundColor DarkGray

exit 0
