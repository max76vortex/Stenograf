param(
    [Parameter(Mandatory = $true)]
    [string]$PromptFile,

    [string]$Model = "",

    [string]$ContextFile = "",

    [string]$InlineContext = ""
)

if (-not (Test-Path -LiteralPath $PromptFile)) {
    throw "Prompt file not found: $PromptFile"
}

$agentCommand = Get-Command agent -ErrorAction SilentlyContinue
$cursorAgentCommand = Get-Command cursor-agent -ErrorAction SilentlyContinue
$cursorCommand = Get-Command cursor -ErrorAction SilentlyContinue

# Prefer explicit local Cursor Agent entrypoints installed by Cursor CLI
# when `agent`/`cursor-agent` aren't visible in the current PATH.
$localCursorAgentRoot = Join-Path $env:LOCALAPPDATA 'cursor-agent'
$localAgentCmdPath = Join-Path $localCursorAgentRoot 'agent.cmd'
$localAgentPs1Path = Join-Path $localCursorAgentRoot 'agent.ps1'
$localCursorAgentCmdPath = Join-Path $localCursorAgentRoot 'cursor-agent.cmd'
$localCursorAgentPs1Path = Join-Path $localCursorAgentRoot 'cursor-agent.ps1'

$agentEntrypoint = $null
$cursorAgentEntrypoint = $null

if ($agentCommand) {
    $agentEntrypoint = $agentCommand.Name
}
elseif (Test-Path -LiteralPath $localAgentCmdPath) {
    $agentEntrypoint = $localAgentCmdPath
}
elseif (Test-Path -LiteralPath $localAgentPs1Path) {
    $agentEntrypoint = $localAgentPs1Path
}

if ($cursorAgentCommand) {
    $cursorAgentEntrypoint = $cursorAgentCommand.Name
}
elseif (Test-Path -LiteralPath $localCursorAgentCmdPath) {
    $cursorAgentEntrypoint = $localCursorAgentCmdPath
}
elseif (Test-Path -LiteralPath $localCursorAgentPs1Path) {
    $cursorAgentEntrypoint = $localCursorAgentPs1Path
}

$promptText = Get-Content -LiteralPath $PromptFile -Raw

if ($ContextFile) {
    if (-not (Test-Path -LiteralPath $ContextFile)) {
        throw "Context file not found: $ContextFile"
    }

    $contextText = Get-Content -LiteralPath $ContextFile -Raw
    $promptText = $promptText + "`n`n# Дополнительный контекст`n`n" + $contextText
}

if ($InlineContext) {
    $promptText = $promptText + "`n`n# Дополнительный контекст`n`n" + $InlineContext
}

$arguments = @("-f")

if ($Model) {
    $arguments += @("--model", $Model)
}

$arguments += @("-p", $promptText)

if ($agentEntrypoint) {
    & $agentEntrypoint @arguments
    return
}

try {
    # Legacy fallback: if `agent` is available as a terminal integration alias/function.
    & agent @arguments
    return
}
catch {
    # continue to fallbacks
}

if ($cursorAgentEntrypoint) {
    & $cursorAgentEntrypoint @arguments
    return
}

if ($cursorCommand) {
    # Last-resort fallback: `cursor agent` subcommand.
    # Note: in some versions it doesn't accept the same flags (-p/-model).
    & $cursorCommand.Name "agent" @arguments
    return
}

throw "Unable to start Cursor agent: could not locate `agent`/`cursor-agent` entrypoint (PATH or local install)."
