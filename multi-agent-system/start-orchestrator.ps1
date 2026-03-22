# Starts the orchestrator (multi-agent-system/agents/01_orchestrator.md) via run-agent.ps1.
# Defaults: TaskFile = multi-agent-system/current-run/task_brief.md
#           ProjectContextFile = current-run/project_context.md if that file exists
param(
    [string]$TaskFile = "",

    [string]$ProjectContextFile = "",

    [string]$Model = ""
)

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$promptFile = Join-Path $scriptRoot "agents\01_orchestrator.md"
$runnerFile = Join-Path $scriptRoot "run-agent.ps1"

# Defaults: canonical active-run inputs (Variant B)
$defaultTaskFile = Join-Path $scriptRoot 'current-run\task_brief.md'
$defaultProjectContextFile = Join-Path $scriptRoot 'current-run\project_context.md'

if (-not $TaskFile) {
    $TaskFile = $defaultTaskFile
}

if (-not $ProjectContextFile -and (Test-Path -LiteralPath $defaultProjectContextFile)) {
    $ProjectContextFile = $defaultProjectContextFile
}

if (-not (Test-Path -LiteralPath $TaskFile)) {
    throw "Task file not found: $TaskFile"
}

$taskText = Get-Content -LiteralPath $TaskFile -Raw
$inlineContext = "Постановка задачи:`n`n$taskText"

if ($ProjectContextFile) {
    if (-not (Test-Path -LiteralPath $ProjectContextFile)) {
        throw "Project context file not found: $ProjectContextFile"
    }

    $projectContextText = Get-Content -LiteralPath $ProjectContextFile -Raw
    $inlineContext += "`n`nОписание проекта:`n`n$projectContextText"
}

$inlineContext += "`n`nРабочая зона артефактов: multi-agent-system/current-run/"
$inlineContext += "`nГлобальный статус: multi-agent-system/status.md"
$inlineContext += "`nПосле каждого крупного этапа требуется подтверждение пользователя."

& $runnerFile -PromptFile $promptFile -Model $Model -InlineContext $inlineContext
