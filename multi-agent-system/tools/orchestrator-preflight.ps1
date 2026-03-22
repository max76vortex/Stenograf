# Preflight checks before start-orchestrator.ps1 (Variant B).
# Run from workspace root: pwsh -NoLogo -File multi-agent-system/tools/orchestrator-preflight.ps1
# Exit code: 0 = OK to proceed, 1 = fix issues first.

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Get-ScriptRoot {
    if ($PSScriptRoot) { return $PSScriptRoot }
    return (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

$scriptRoot = Get-ScriptRoot
$multiAgentRoot = Split-Path -Parent $scriptRoot
$workspaceRoot = Split-Path -Parent $multiAgentRoot

function Test-PreflightItem {
    param(
        [string]$Name,
        [bool]$Ok,
        [string]$Detail = ''
    )
    if ($Ok) {
        Write-Host ("[OK]   {0}" -f $Name) -ForegroundColor Green
        if ($Detail) { Write-Host ("       {0}" -f $Detail) -ForegroundColor DarkGray }
    }
    else {
        Write-Host ("[FAIL] {0}" -f $Name) -ForegroundColor Red
        if ($Detail) { Write-Host ("       {0}" -f $Detail) -ForegroundColor Yellow }
    }
    return $Ok
}

$allOk = $true
Write-Host "Orchestrator preflight (workspace root: $workspaceRoot)" -ForegroundColor Cyan
Write-Host ""

# --- Shell ---
$pwshCmd = Get-Command pwsh -ErrorAction SilentlyContinue
$allOk = (Test-PreflightItem -Name 'PowerShell 7 (pwsh)' -Ok ($null -ne $pwshCmd) -Detail $(if ($pwshCmd) { $pwshCmd.Source })) -and $allOk

# --- Cursor Agent CLI (at least one path to invoke agent) ---
$agentCmd = Get-Command agent -ErrorAction SilentlyContinue
$cursorAgentCmd = Get-Command cursor-agent -ErrorAction SilentlyContinue
$cursorCmd = Get-Command cursor -ErrorAction SilentlyContinue
$localAgentCmd = Join-Path $env:LOCALAPPDATA 'cursor-agent\agent.cmd'
$localCursorAgentCmd = Join-Path $env:LOCALAPPDATA 'cursor-agent\cursor-agent.cmd'
$hasLocalAgent = (Test-Path -LiteralPath $localAgentCmd)
$hasLocalCursorAgent = (Test-Path -LiteralPath $localCursorAgentCmd)

$cliOk = $null -ne $agentCmd -or $null -ne $cursorAgentCmd -or $hasLocalAgent -or $hasLocalCursorAgent -or $null -ne $cursorCmd
$cliDetail = @()
if ($agentCmd) { $cliDetail += 'agent in PATH' }
if ($cursorAgentCmd) { $cliDetail += 'cursor-agent in PATH' }
if ($hasLocalAgent) { $cliDetail += "local: $localAgentCmd" }
if ($hasLocalCursorAgent) { $cliDetail += "local: $localCursorAgentCmd" }
if ($cursorCmd -and -not $cliOk) { $cliDetail += 'cursor in PATH (fallback only)' }
if ($cliDetail.Count -eq 0) { $cliDetail = @('no agent entrypoint found') }

$allOk = (Test-PreflightItem -Name 'Cursor Agent CLI (agent / cursor-agent or local install)' -Ok $cliOk -Detail ($cliDetail -join '; ')) -and $allOk

# --- Required files (relative to workspace root) ---
$required = @(
    @{ Path = 'multi-agent-system/agents/01_orchestrator.md'; Desc = 'Orchestrator prompt' }
    @{ Path = 'multi-agent-system/start-orchestrator.ps1'; Desc = 'Orchestrator launcher' }
    @{ Path = 'multi-agent-system/run-agent.ps1'; Desc = 'Agent runner' }
    @{ Path = 'multi-agent-system/status.md'; Desc = 'Global status' }
)

foreach ($item in $required) {
    $full = Join-Path $workspaceRoot $item.Path
    $exists = Test-Path -LiteralPath $full
    $allOk = (Test-PreflightItem -Name $item.Desc -Ok $exists -Detail $item.Path) -and $allOk
}

# --- Optional: current-run placeholders (warn only) ---
$taskBrief = Join-Path $workspaceRoot 'multi-agent-system/current-run/task_brief.md'
$projCtx = Join-Path $workspaceRoot 'multi-agent-system/current-run/project_context.md'
if (-not (Test-Path -LiteralPath $taskBrief)) {
    Write-Host "[WARN] task_brief.md missing — create before start (or use /start-multi-agent-run)." -ForegroundColor Yellow
}
if (-not (Test-Path -LiteralPath $projCtx)) {
    Write-Host "[WARN] project_context.md missing — create before start (or use /start-multi-agent-run)." -ForegroundColor Yellow
}

Write-Host ""
if ($allOk) {
    Write-Host "Preflight passed. You can run start-orchestrator.ps1 with task_brief + project_context." -ForegroundColor Green
    exit 0
}
else {
    Write-Host "Preflight failed. Fix items above, then see multi-agent-system/runbooks/prerequisites.md" -ForegroundColor Red
    exit 1
}
