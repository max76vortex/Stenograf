[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [switch]$KeepTmp
)

$ErrorActionPreference = 'Stop'

function Get-ScriptRoot {
    if ($PSScriptRoot) { return $PSScriptRoot }
    return (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

function Assert-Contains {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text,
        [Parameter(Mandatory = $true)]
        [string]$Substr,
        [Parameter(Mandatory = $false)]
        [string]$Message = ''
    )

    if ($Text -notmatch [Regex]::Escape($Substr)) {
        if (-not $Message) { $Message = "Expected output to contain: '$Substr'" }
        throw $Message
    }
}

function Assert-NotContains {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Text,
        [Parameter(Mandatory = $true)]
        [string]$Substr,
        [Parameter(Mandatory = $false)]
        [string]$Message = ''
    )

    if ($Text -match [Regex]::Escape($Substr)) {
        if (-not $Message) { $Message = "Expected output to NOT contain: '$Substr'" }
        throw $Message
    }
}

$scriptRoot = Get-ScriptRoot
$multiAgentRoot = Split-Path -Parent $scriptRoot
$cliPath = Join-Path $scriptRoot 'dryrun-status.ps1'
$tmpRoot = Join-Path $multiAgentRoot 'current-run\tmp_task_04'

if (Test-Path -LiteralPath $tmpRoot) {
    Remove-Item -LiteralPath $tmpRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $tmpRoot | Out-Null

$results = New-Object System.Collections.Generic.List[object]
$success = $false

function Invoke-Scenario {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$StatusFilePath,
        [Parameter(Mandatory = $true)]
        [string]$OpenQuestionsFilePath,
        [Parameter(Mandatory = $true)]
        [string]$CurrentRunDirectory
    )

    $out = & pwsh -NoLogo -File $cliPath `
        -Top 3 `
        -StatusFilePathOverride $StatusFilePath `
        -OpenQuestionsFilePathOverride $OpenQuestionsFilePath `
        -CurrentRunDirectoryOverride $CurrentRunDirectory 2>&1 | Out-String

    return $out
}

function New-ScenarioDir {
    param([Parameter(Mandatory = $true)][string]$Name)
    $d = Join-Path $tmpRoot $Name
    if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force }
    New-Item -ItemType Directory -Path $d | Out-Null
    return $d
}

function Write-StatusMd {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $false)][string]$OpenQuestionsSummaryLine
    )

    $content = @(
        '# Status',
        '## System State',
        '- Variant: B',
        '- Status: TEST_STATUS',
        '- Current stage: task_04_tests',
        '- Current iteration: 1',
        '- Active task: task_04_tests',
        '- Last updated by: test',
        '## Confirmed By User',
        '- [x] Analysis',
        '- [ ] Development',
        '## Open Questions Summary',
        $OpenQuestionsSummaryLine,
        '## Orchestrator Step State',
        '- Next expected step: wait for user confirmation in tests'
    )

    Set-Content -LiteralPath $Path -Value $content -Encoding UTF8
}

function Add-MdFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][datetime]$LastWriteTimeValue,
        [Parameter(Mandatory = $false)][string]$Content = 'test'
    )

    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }

    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
    (Get-Item -LiteralPath $Path) | ForEach-Object { $_.LastWriteTime = $LastWriteTimeValue }
}

Write-Host "Task 04 tests: starting..."

try {
    # -------------------------
    # Unit-like checks (parsers)
    # -------------------------
    Import-Module -Name (Join-Path $scriptRoot 'dryrun-status.internal.psm1') -DisableNameChecking -Force | Out-Null

    $parsedNoSection = Get-SystemStateSection -Lines @('## Something else','- Status: X')
    $stateNoSection = Convert-SystemStateLinesToObject -SectionLines $parsedNoSection.SectionLines
    if ($stateNoSection.Status -ne 'UNKNOWN') { throw "SystemState without section: expected Status=UNKNOWN" }
    if ($stateNoSection.CurrentStage -ne 'unknown') { throw "SystemState without section: expected CurrentStage=unknown" }

    $parsedMissingKeys = Get-SystemStateSection -Lines @(
        '## System State',
        '- Status: WAITING_FOR_USER_CONFIRMATION'
    )
    $stateMissingKeys = Convert-SystemStateLinesToObject -SectionLines $parsedMissingKeys.SectionLines
    if ($stateMissingKeys.Status -ne 'WAITING_FOR_USER_CONFIRMATION') { throw "Missing keys case: Status should be taken from section" }
    if ($stateMissingKeys.CurrentStage -ne 'unknown') { throw "Missing keys case: CurrentStage should be unknown" }

    Write-Host "Unit-like checks: OK"

    # -------------------------
    # E2E scripted scenarios via CLI overrides
    # -------------------------

    # 1) Fallback: open_questions missing -> status Open Questions Summary says none
    $s1 = New-ScenarioDir -Name 'fallback_open_missing_none'
    Write-StatusMd -Path (Join-Path $s1 'status.md') -OpenQuestionsSummaryLine '- None'
    $open1 = Join-Path $s1 'open_questions.md'  # intentionally missing
    $scan1 = Join-Path $s1 'current-run'
    New-Item -ItemType Directory -Path $scan1 | Out-Null

    $out1 = Invoke-Scenario -Name 's1' -StatusFilePath (Join-Path $s1 'status.md') -OpenQuestionsFilePath $open1 -CurrentRunDirectory $scan1
    Assert-Contains -Text $out1 -Substr 'Final status : NO_BLOCKERS'
    Assert-Contains -Text $out1 -Substr 'Source used  : STATUS_FALLBACK'
    Assert-Contains -Text $out1 -Substr 'No blocking questions.'
    Assert-Contains -Text $out1 -Substr 'Next exp. step  : wait for user confirmation in tests'
    Assert-Contains -Text $out1 -Substr 'Confirmed stages:'
    Assert-Contains -Text $out1 -Substr '  - Analysis'
    Assert-NotContains -Text $out1 -Substr '  - Development'

    $results.Add([pscustomobject]@{ Name='fallback_open_missing_none'; Status='PASS' })

    # 2) Primary ambiguous: open_questions without BLOCKER and without "no open questions"
    $s2 = New-ScenarioDir -Name 'primary_ambiguous_no_markers'
    Write-StatusMd -Path (Join-Path $s2 'status.md') -OpenQuestionsSummaryLine '- None'
    $open2 = Join-Path $s2 'open_questions.md'
    Set-Content -LiteralPath $open2 -Value @(
        '# Open Questions',
        '- How to proceed?'
    ) -Encoding UTF8
    $scan2 = Join-Path $s2 'current-run'
    New-Item -ItemType Directory -Path $scan2 | Out-Null

    $out2 = Invoke-Scenario -Name 's2' -StatusFilePath (Join-Path $s2 'status.md') -OpenQuestionsFilePath $open2 -CurrentRunDirectory $scan2
    Assert-Contains -Text $out2 -Substr 'Final status : UNKNOWN'
    Assert-Contains -Text $out2 -Substr 'Source used  : OPEN_QUESTIONS_PRIMARY'
    Assert-Contains -Text $out2 -Substr 'Is ambiguous : True'

    $results.Add([pscustomobject]@{ Name='primary_ambiguous_no_markers'; Status='PASS' })

    # 3) Primary: HAS_BLOCKERS by BLOCKER markers in open_questions
    $s3 = New-ScenarioDir -Name 'primary_has_blockers'
    Write-StatusMd -Path (Join-Path $s3 'status.md') -OpenQuestionsSummaryLine '- None'
    $open3 = Join-Path $s3 'open_questions.md'
    Set-Content -LiteralPath $open3 -Value @(
        '# Open Questions',
        '- [BLOCKER] Please confirm the scope.',
        '- BLOCKER: Choose the orchestrator model.'
    ) -Encoding UTF8
    $scan3 = Join-Path $s3 'current-run'
    New-Item -ItemType Directory -Path $scan3 | Out-Null

    $out3 = Invoke-Scenario -Name 's3' -StatusFilePath (Join-Path $s3 'status.md') -OpenQuestionsFilePath $open3 -CurrentRunDirectory $scan3
    Assert-Contains -Text $out3 -Substr 'Final status : HAS_BLOCKERS'
    Assert-Contains -Text $out3 -Substr 'Source used  : OPEN_QUESTIONS_PRIMARY'
    Assert-Contains -Text $out3 -Substr 'Questions:'
    Assert-Contains -Text $out3 -Substr 'Please confirm the scope.'

    $results.Add([pscustomobject]@{ Name='primary_has_blockers'; Status='PASS' })

    # 4) Primary: NO_BLOCKERS with "no open questions" marker
    $s4 = New-ScenarioDir -Name 'primary_no_open_questions_marker'
    Write-StatusMd -Path (Join-Path $s4 'status.md') -OpenQuestionsSummaryLine '- None'
    $open4 = Join-Path $s4 'open_questions.md'
    Set-Content -LiteralPath $open4 -Value @(
        '# Open Questions',
        'No open questions yet.'
    ) -Encoding UTF8
    $scan4 = Join-Path $s4 'current-run'
    New-Item -ItemType Directory -Path $scan4 | Out-Null

    $out4 = Invoke-Scenario -Name 's4' -StatusFilePath (Join-Path $s4 'status.md') -OpenQuestionsFilePath $open4 -CurrentRunDirectory $scan4
    Assert-Contains -Text $out4 -Substr 'Final status : NO_BLOCKERS'
    Assert-Contains -Text $out4 -Substr 'Source used  : OPEN_QUESTIONS_PRIMARY'
    Assert-Contains -Text $out4 -Substr 'No blocking questions.'

    $results.Add([pscustomobject]@{ Name='primary_no_open_questions_marker'; Status='PASS' })

    # 5) Artifacts: current-run missing -> no artifacts to display
    $s5 = New-ScenarioDir -Name 'artifacts_current_run_missing'
    Write-StatusMd -Path (Join-Path $s5 'status.md') -OpenQuestionsSummaryLine '- None'
    $open5 = Join-Path $s5 'open_questions.md'
    Set-Content -LiteralPath $open5 -Value @('# Open Questions','No open questions yet.') -Encoding UTF8
    $scan5 = Join-Path $s5 'current-run'  # directory intentionally not created

    $out5 = Invoke-Scenario -Name 's5' -StatusFilePath (Join-Path $s5 'status.md') -OpenQuestionsFilePath $open5 -CurrentRunDirectory $scan5
    Assert-Contains -Text $out5 -Substr 'No artifacts to display.'

    $results.Add([pscustomobject]@{ Name='artifacts_current_run_missing'; Status='PASS' })

    # 6) Artifacts: determinism + Top N
    $s6 = New-ScenarioDir -Name 'artifacts_sort_and_top'
    Write-StatusMd -Path (Join-Path $s6 'status.md') -OpenQuestionsSummaryLine '- None'
    $open6 = Join-Path $s6 'open_questions.md'
    Set-Content -LiteralPath $open6 -Value @('# Open Questions','No open questions yet.') -Encoding UTF8
    $scan6 = Join-Path $s6 'current-run'
    New-Item -ItemType Directory -Path $scan6 | Out-Null

    $now = Get-Date
    Add-MdFile -Path (Join-Path $scan6 'a.md') -LastWriteTimeValue ($now.AddMinutes(-10)) -Content 'a'
    Add-MdFile -Path (Join-Path $scan6 'b.md') -LastWriteTimeValue ($now.AddMinutes(-5)) -Content 'b'
    Add-MdFile -Path (Join-Path $scan6 'c.md') -LastWriteTimeValue ($now.AddMinutes(-1)) -Content 'c'
    Add-MdFile -Path (Join-Path $scan6 'README.md') -LastWriteTimeValue ($now.AddMinutes(1)) -Content 'readme must be excluded'

    $out6 = Invoke-Scenario -Name 's6' -StatusFilePath (Join-Path $s6 'status.md') -OpenQuestionsFilePath $open6 -CurrentRunDirectory $scan6
    # Top=3 for run; c should be first (newest)
    Assert-Contains -Text $out6 -Substr '[1] multi-agent-system/current-run/c.md'
    Assert-Contains -Text $out6 -Substr '[2] multi-agent-system/current-run/b.md'
    Assert-NotContains -Text $out6 -Substr 'README.md'

    $results.Add([pscustomobject]@{ Name='artifacts_sort_and_top'; Status='PASS' })

    Write-Host "All scenarios: OK"
    $success = $true
}
catch {
    Write-Host "Task 04 tests FAILED: $($_.Exception.Message)"
    throw
}
finally {
    if ($success -and -not $KeepTmp) {
        if (Test-Path -LiteralPath $tmpRoot) {
            Remove-Item -LiteralPath $tmpRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Host ""
    Write-Host "Results:"
    foreach ($r in $results) {
        Write-Host ("- {0}: {1}" -f $r.Name, $r.Status)
    }
}

