param(
    [Parameter(Mandatory = $true)]
    [string]$PromptFile,

    [string]$Model = "",

    [ValidateSet("cursor","ollama","openai","lmstudio")]
    [string]$AgentBackend = "cursor",

    [string]$ContextFile = "",

    [string]$InlineContext = ""
)

if (-not (Test-Path -LiteralPath $PromptFile)) {
    throw "Prompt file not found: $PromptFile"
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

function Invoke-CursorBackend {
    param(
        [Parameter(Mandatory = $true)][string[]]$CliArguments
    )

    $agentCommand = Get-Command agent -ErrorAction SilentlyContinue
    $cursorAgentCommand = Get-Command cursor-agent -ErrorAction SilentlyContinue
    $cursorCommand = Get-Command cursor -ErrorAction SilentlyContinue

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

    if ($agentEntrypoint) {
        & $agentEntrypoint @CliArguments
        return
    }

    try {
        & agent @CliArguments
        return
    }
    catch {
        # continue
    }

    if ($cursorAgentEntrypoint) {
        & $cursorAgentEntrypoint @CliArguments
        return
    }

    if ($cursorCommand) {
        & $cursorCommand.Name "agent" @CliArguments
        return
    }

    throw "Unable to start Cursor agent: could not locate `agent`/`cursor-agent` entrypoint (PATH or local install)."
}

function Invoke-OpenAICompatibleChat {
    param(
        [Parameter(Mandatory = $true)][string]$ResolvedPrompt,
        [Parameter(Mandatory = $true)][string]$ResolvedModel,
        [Parameter(Mandatory = $true)][string]$Endpoint,
        [string]$ApiKey
    )

    $body = @{
        model = $ResolvedModel
        messages = @(
            @{ role = "user"; content = $ResolvedPrompt }
        )
        temperature = 0.2
    } | ConvertTo-Json -Depth 6

    $headers = @{ "Content-Type" = "application/json" }
    if ($ApiKey) { $headers["Authorization"] = "Bearer $ApiKey" }

    $response = Invoke-RestMethod -Method Post -Uri $Endpoint -Headers $headers -Body $body
    $content = $response.choices[0].message.content
    if (-not $content) {
        throw "Empty response from endpoint: $Endpoint"
    }
    Write-Output $content
}

switch ($AgentBackend) {
    "cursor" {
        Invoke-CursorBackend -CliArguments $arguments
    }
    "ollama" {
        $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
        if (-not $ollamaCommand) { throw "Backend 'ollama' requires 'ollama' CLI in PATH." }
        $resolvedModel = if ($Model) { $Model } else { "llama3.1:8b" }
        $promptText | & $ollamaCommand.Source run $resolvedModel
    }
    "openai" {
        if (-not $env:OPENAI_API_KEY) { throw "Backend 'openai' requires OPENAI_API_KEY environment variable." }
        $resolvedModel = if ($Model) { $Model } else { "gpt-4.1-mini" }
        Invoke-OpenAICompatibleChat -ResolvedPrompt $promptText -ResolvedModel $resolvedModel -Endpoint "https://api.openai.com/v1/chat/completions" -ApiKey $env:OPENAI_API_KEY
    }
    "lmstudio" {
        $resolvedModel = if ($Model) { $Model } else { "local-model" }
        Invoke-OpenAICompatibleChat -ResolvedPrompt $promptText -ResolvedModel $resolvedModel -Endpoint "http://127.0.0.1:1234/v1/chat/completions"
    }
}
