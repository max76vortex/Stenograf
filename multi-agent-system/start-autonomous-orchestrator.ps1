[CmdletBinding()]
param(
    [ValidateSet("cursor","ollama","openai","lmstudio")]
    [string]$AgentBackend = "cursor",
    [string]$ModelProfile = "default-quality",
    [string]$TaskFile = "",
    [string]$ProjectContextFile = "",
    [switch]$SkipPreflight
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$profilesPath = Join-Path $root "config\model-profiles.json"
$runAgent = Join-Path $root "run-agent.ps1"
$preflight = Join-Path $root "tools\orchestrator-preflight.ps1"

if (-not $TaskFile) { $TaskFile = Join-Path $root "current-run\task_brief.md" }
if (-not $ProjectContextFile) { $ProjectContextFile = Join-Path $root "current-run\project_context.md" }

if (!(Test-Path -LiteralPath $profilesPath)) { throw "Missing model profiles: $profilesPath" }
if (!(Test-Path -LiteralPath $runAgent)) { throw "Missing runner: $runAgent" }
if (!(Test-Path -LiteralPath $TaskFile)) { throw "Task file not found: $TaskFile" }
if (!(Test-Path -LiteralPath $ProjectContextFile)) { throw "Project context file not found: $ProjectContextFile" }

if (-not $SkipPreflight) {
    & pwsh -NoLogo -File $preflight -AgentBackend $AgentBackend
    if ($LASTEXITCODE -ne 0) { throw "Preflight failed for backend '$AgentBackend'" }
}

$profiles = Get-Content -LiteralPath $profilesPath -Raw | ConvertFrom-Json
$modelProfileConfig = $profiles.profiles.$ModelProfile
if ($null -eq $modelProfileConfig) { throw "Model profile '$ModelProfile' not found in $profilesPath" }

$taskText = Get-Content -LiteralPath $TaskFile -Raw
$projectContextText = Get-Content -LiteralPath $ProjectContextFile -Raw
$baseContext = @"
Постановка задачи:

$taskText

Описание проекта:

$projectContextText

Рабочая зона артефактов: multi-agent-system/current-run/
Глобальный статус: multi-agent-system/status.md
"@

function Invoke-Role {
    param(
        [Parameter(Mandatory = $true)][string]$RoleName,
        [Parameter(Mandatory = $true)][string]$PromptRelPath,
        [Parameter(Mandatory = $true)][string]$Model,
        [Parameter(Mandatory = $true)][string]$ExtraContext
    )

    $promptPath = Join-Path $root $PromptRelPath
    if (!(Test-Path -LiteralPath $promptPath)) { throw "Prompt not found: $promptPath" }

    Write-Host "[INFO] Running role '$RoleName' with model '$Model' (backend: $AgentBackend)"
    & $runAgent -PromptFile $promptPath -Model $Model -AgentBackend $AgentBackend -InlineContext ($baseContext + "`n`n" + $ExtraContext)
    if ($LASTEXITCODE -ne 0) {
        throw "Role '$RoleName' failed with exit code $LASTEXITCODE"
    }
}

Invoke-Role -RoleName "orchestrator" -PromptRelPath "agents\01_orchestrator.md" -Model ([string]$modelProfileConfig.orchestrator) -ExtraContext "Режим: автономный пайплайн. Вмешательство пользователя не требуется, если нет блокеров."
Invoke-Role -RoleName "analyst" -PromptRelPath "agents\02_analyst_prompt.md" -Model ([string]$modelProfileConfig.analyst) -ExtraContext "Сформируй/обнови technical_specification.md."
Invoke-Role -RoleName "tz_reviewer" -PromptRelPath "agents\03_tz_reviewer_prompt.md" -Model ([string]$modelProfileConfig.tz_reviewer) -ExtraContext "Проведи review ТЗ и обнови tz_review.md."
Invoke-Role -RoleName "architect" -PromptRelPath "agents\04_architect_prompt.md" -Model ([string]$modelProfileConfig.architect) -ExtraContext "Сформируй architecture.md."
Invoke-Role -RoleName "architecture_reviewer" -PromptRelPath "agents\05_architecture_reviewer_prompt.md" -Model ([string]$modelProfileConfig.architecture_reviewer) -ExtraContext "Проведи review архитектуры и обнови architecture_review.md."
Invoke-Role -RoleName "planner" -PromptRelPath "agents\06_agent_planner.md" -Model ([string]$modelProfileConfig.planner) -ExtraContext "Сформируй plan.md и task-файлы в current-run/tasks."
Invoke-Role -RoleName "plan_reviewer" -PromptRelPath "agents\07_agent_plan_reviewer.md" -Model ([string]$modelProfileConfig.plan_reviewer) -ExtraContext "Проведи review плана и обнови plan_review.md."

$tasksDir = Join-Path $root "current-run\tasks"
$taskFiles = if (Test-Path -LiteralPath $tasksDir) {
    @(Get-ChildItem -LiteralPath $tasksDir -File | Where-Object { $_.Name -ne "README.md" } | Sort-Object Name)
} else { @() }

foreach ($task in $taskFiles) {
    $taskCtx = "Текущий task-файл: $($task.FullName)`nВыполни задачу и зафиксируй результаты в текущем коде и reports/."
    Invoke-Role -RoleName "developer:$($task.Name)" -PromptRelPath "agents\08_agent_developer.md" -Model ([string]$modelProfileConfig.developer) -ExtraContext $taskCtx
    Invoke-Role -RoleName "code-reviewer:$($task.Name)" -PromptRelPath "agents\09_agent_code_reviewer.md" -Model ([string]$modelProfileConfig.code_reviewer) -ExtraContext $taskCtx
}

Write-Host "[OK] Autonomous run completed with profile '$ModelProfile'."
