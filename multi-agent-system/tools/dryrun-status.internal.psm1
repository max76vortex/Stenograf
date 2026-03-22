<#
  Internal module for dry run status CLI.
  SystemState is read from multi-agent-system/status.md (System State, Orchestrator Step State, Confirmed By User).
#>

class SystemState {
    [string]$Variant
    [string]$Status
    [string]$CurrentStage
    [string]$CurrentIteration
    [string]$ActiveTask
    [string]$LastUpdatedBy
    [string]$NextExpectedStep
    [string[]]$ConfirmedStages
    [string[]]$Diagnostics

    SystemState() {
        $this.Diagnostics = @()
        $this.ConfirmedStages = @()
        $this.NextExpectedStep = 'UNKNOWN'
    }
}

class BlockingQuestionsResult {
    [string]$FinalStatus
    [string]$SourceUsed
    [bool]$IsAmbiguous
    [object[]]$Questions
    [string[]]$Diagnostics

    BlockingQuestionsResult() {
        $this.Questions = @()
        $this.Diagnostics = @()
    }
}

class ArtifactEntry {
    [string]$RelativePath
    [string]$MTime
    [bool]$IsReadable
    [string]$Diagnostics
}

class StatusSurfaceReport {
    [SystemState]$SystemState
    [BlockingQuestionsResult]$Blocking
    [ArtifactEntry[]]$Artifacts
    [datetime]$GeneratedAt
    [bool]$IsStub
}

function Get-SystemStateStub {
    [OutputType([SystemState])]
    param ()

    $state = [SystemState]::new()
    $state.Variant = 'dry-run (stub)'
    $state.Status = 'PLANNING_IN_PROGRESS (stub)'
    $state.CurrentStage = 'Task 01 skeleton (stub)'
    $state.CurrentIteration = '1 (stub)'
    $state.ActiveTask = 'Task 01 – CLI status skeleton (stub)'
    $state.LastUpdatedBy = 'multi-agent-system/tools/dryrun-status.internal.psm1 (stub)'
    $state.NextExpectedStep = 'UNKNOWN'
    $state.ConfirmedStages = @()
    $state.Diagnostics += 'SystemState is populated from stub implementation. No files are read yet.'
    return $state
}

function Get-StatusFilePath {
    [OutputType([string])]
    param (
        [string]$BasePath
    )

    if (-not $BasePath) {
        $BasePath = (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
    }

    return (Join-Path $BasePath 'status.md')
}

function Read-StatusFileContent {
    [OutputType([hashtable])]
    param (
        [string]$StatusFilePath
    )

    $result = @{
        Lines      = @()
        Diagnostics = @()
    }

    if (-not (Test-Path -LiteralPath $StatusFilePath)) {
        $result.Diagnostics += "Status file not found at '$StatusFilePath'."
        return $result
    }

    try {
        $result.Lines = Get-Content -LiteralPath $StatusFilePath -ErrorAction Stop
    }
    catch {
        $result.Diagnostics += "Failed to read status file '$StatusFilePath': $($_.Exception.Message)"
    }

    return $result
}

function Get-SystemStateSection {
    [OutputType([hashtable])]
    param (
        [string[]]$Lines
    )

    $result = @{
        SectionLines = @()
        Diagnostics  = @()
    }

    if (-not $Lines -or $Lines.Count -eq 0) {
        $result.Diagnostics += 'Status file content is empty.'
        # Keep SectionLines empty; Convert will mark fields as unknown.
        return $result
    }

    $startIndex = $Lines.IndexOf('## System State')
    if ($startIndex -lt 0) {
        $result.Diagnostics += 'Section ''## System State'' not found in status.md.'
        # Keep SectionLines empty; Convert will mark fields as unknown.
        return $result
    }

    $sectionLines = @()
    for ($i = $startIndex + 1; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i]
        if ($line -like '## *') {
            break
        }
        if ($line.Trim().Length -gt 0) {
            $sectionLines += $line
        }
    }

    $result.SectionLines = $sectionLines
    return $result
}

function Get-StatusMarkdownSection {
    [OutputType([hashtable])]
    param (
        [string[]]$Lines,
        [Parameter(Mandatory = $true)]
        [string]$SectionHeading
    )

    $result = @{
        SectionLines = @()
        Diagnostics  = @()
    }

    if (-not $Lines -or $Lines.Count -eq 0) {
        $result.Diagnostics += 'Status file content is empty.'
        return $result
    }

    $startIndex = $Lines.IndexOf($SectionHeading)
    if ($startIndex -lt 0) {
        $result.Diagnostics += "Section '$SectionHeading' not found in status.md."
        return $result
    }

    $sectionLines = @()
    for ($i = $startIndex + 1; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i]
        if ($line -like '## *') {
            break
        }
        if ($line.Trim().Length -gt 0) {
            $sectionLines += $line
        }
    }

    $result.SectionLines = $sectionLines
    return $result
}

function Parse-NextExpectedStepFromOrchestratorSectionLines {
    [OutputType([hashtable])]
    param (
        [string[]]$SectionLines
    )

    $result = @{
        Value        = 'UNKNOWN'
        Diagnostics  = @()
    }

    if (-not $SectionLines -or $SectionLines.Count -eq 0) {
        $result.Diagnostics += 'Orchestrator Step State section has no lines to parse for Next expected step.'
        return $result
    }

    foreach ($line in $SectionLines) {
        if ($line -notmatch '^\s*-\s*([^:]+)\s*:\s*(.*)$') {
            continue
        }

        $key = $Matches[1].Trim()
        if ($key -ne 'Next expected step') {
            continue
        }

        $value = $Matches[2].Trim()
        if ($value) {
            $result.Value = $value
        }
        else {
            $result.Diagnostics += "Key 'Next expected step' present but value is empty."
        }
        return $result
    }

    $result.Diagnostics += "Key 'Next expected step' not found in Orchestrator Step State section."
    return $result
}

function Parse-ConfirmedStagesFromConfirmedByUserLines {
    [OutputType([hashtable])]
    param (
        [string[]]$SectionLines
    )

    $result = @{
        Stages      = [string[]]@()
        Diagnostics = @()
    }

    if (-not $SectionLines -or $SectionLines.Count -eq 0) {
        $result.Diagnostics += 'Confirmed By User section has no lines to parse for checked items.'
        return $result
    }

    $stages = @()
    foreach ($line in $SectionLines) {
        if ($line -match '^\s*-\s*\[\s*[xX]\s*\]\s*(.+)$') {
            $text = $Matches[1].Trim()
            if ($text) {
                $stages += $text
            }
        }
    }

    $result.Stages = @($stages)
    return $result
}

function Add-OrchestratorAndConfirmedFieldsToSystemState {
    param (
        [string[]]$Lines,
        [SystemState]$State
    )

    $orch = Get-StatusMarkdownSection -Lines $Lines -SectionHeading '## Orchestrator Step State'
    $next = Parse-NextExpectedStepFromOrchestratorSectionLines -SectionLines $orch.SectionLines
    $State.NextExpectedStep = $next.Value
    if ($next.Diagnostics) {
        $State.Diagnostics += $next.Diagnostics
    }
    if ($orch.Diagnostics) {
        $State.Diagnostics += $orch.Diagnostics
    }

    $confSec = Get-StatusMarkdownSection -Lines $Lines -SectionHeading '## Confirmed By User'
    $parsedConf = Parse-ConfirmedStagesFromConfirmedByUserLines -SectionLines $confSec.SectionLines
    $State.ConfirmedStages = @($parsedConf.Stages)
    if ($parsedConf.Diagnostics) {
        $State.Diagnostics += $parsedConf.Diagnostics
    }
    if ($confSec.Diagnostics) {
        $State.Diagnostics += $confSec.Diagnostics
    }
}

function Convert-SystemStateLinesToObject {
    [OutputType([SystemState])]
    param (
        [string[]]$SectionLines
    )

    $state = [SystemState]::new()

    if (-not $SectionLines -or $SectionLines.Count -eq 0) {
        $state.Diagnostics += 'System State section is empty; all fields will be unknown.'
        # Ensure required fields always have values for downstream rendering.
        $state.Variant = 'unknown'
        $state.Status = 'UNKNOWN'
        $state.CurrentStage = 'unknown'
        $state.CurrentIteration = 'unknown'
        $state.ActiveTask = 'unknown'
        $state.LastUpdatedBy = ''
        $state.NextExpectedStep = 'UNKNOWN'
        $state.ConfirmedStages = @()
        return $state
    }

    foreach ($line in $SectionLines) {
        if ($line -notmatch '^\s*-\s*([^:]+)\s*:\s*(.*)$') {
            continue
        }

        $key = $Matches[1].Trim()
        $value = $Matches[2].Trim()

        switch -Regex ($key) {
            '^Variant$'            { $state.Variant = $value; continue }
            '^Status$'             { $state.Status = $value; continue }
            '^Current stage$'      { $state.CurrentStage = $value; continue }
            '^Current iteration$'  { $state.CurrentIteration = $value; continue }
            '^Active task$'        { $state.ActiveTask = $value; continue }
            '^Last updated by$'    { $state.LastUpdatedBy = $value; continue }
            default                { continue }
        }
    }

    if (-not $state.Status) {
        $state.Diagnostics += 'Key ''Status'' not found in System State section.'
    }
    if (-not $state.CurrentStage) {
        $state.Diagnostics += 'Key ''Current stage'' not found in System State section.'
    }
    if (-not $state.CurrentIteration) {
        $state.Diagnostics += 'Key ''Current iteration'' not found in System State section.'
    }
    if (-not $state.ActiveTask) {
        $state.Diagnostics += 'Key ''Active task'' not found in System State section.'
    }

    if (-not $state.Variant) {
        $state.Variant = 'unknown'
    }
    if (-not $state.Status) {
        $state.Status = 'UNKNOWN'
    }
    if (-not $state.CurrentStage) {
        $state.CurrentStage = 'unknown'
    }
    if (-not $state.CurrentIteration) {
        $state.CurrentIteration = 'unknown'
    }
    if (-not $state.ActiveTask) {
        $state.ActiveTask = 'unknown'
    }

    return $state
}

function Get-SystemStateFromStatusFile {
    [OutputType([SystemState])]
    param (
        [string]$BasePath,
        [string]$StatusFilePathOverride
    )

    if ($StatusFilePathOverride) {
        $path = $StatusFilePathOverride
    }
    else {
        $path = Get-StatusFilePath -BasePath $BasePath
    }
    $readResult = Read-StatusFileContent -StatusFilePath $path

    $state = $null
    if ($readResult.Lines -and $readResult.Lines.Count -gt 0) {
        $parsed = Get-SystemStateSection -Lines $readResult.Lines
        $state = Convert-SystemStateLinesToObject -SectionLines $parsed.SectionLines
        if ($parsed.Diagnostics) {
            $state.Diagnostics += $parsed.Diagnostics
        }
    }
    else {
        $state = [SystemState]::new()
        $state.Variant = 'unknown'
        $state.Status = 'UNKNOWN'
        $state.CurrentStage = 'unknown'
        $state.CurrentIteration = 'unknown'
        $state.ActiveTask = 'unknown'
        $state.LastUpdatedBy = ''
        $state.NextExpectedStep = 'UNKNOWN'
        $state.ConfirmedStages = @()
    }

    if ($readResult.Lines -and $readResult.Lines.Count -gt 0) {
        Add-OrchestratorAndConfirmedFieldsToSystemState -Lines $readResult.Lines -State $state
    }

    if ($readResult.Diagnostics) {
        $state.Diagnostics += $readResult.Diagnostics
    }

    return $state
}

function Get-OpenQuestionsFilePath {
    [OutputType([string])]
    param(
        [string]$BasePath
    )

    if (-not $BasePath) {
        $BasePath = (Split-Path -Parent (Split-Path -Parent $PSCommandPath))
    }
    return (Join-Path $BasePath 'current-run/open_questions.md')
}

function Read-OpenQuestionsFileContent {
    [OutputType([hashtable])]
    param(
        [string]$OpenQuestionsFilePath
    )

    $result = @{
        Lines      = @()
        Diagnostics = @()
    }

    if (-not $OpenQuestionsFilePath -or -not (Test-Path -LiteralPath $OpenQuestionsFilePath)) {
        $result.Diagnostics += "open_questions.md not found at '$OpenQuestionsFilePath'."
        return $result
    }

    try {
        $result.Lines = Get-Content -LiteralPath $OpenQuestionsFilePath -ErrorAction Stop
    }
    catch {
        $result.Diagnostics += "Failed to read open questions file '$OpenQuestionsFilePath': $($_.Exception.Message)"
    }

    return $result
}

function Parse-BlockingQuestionsFromOpenQuestionsLines {
    [OutputType([hashtable])]
    param(
        [string[]]$Lines
    )

    $result = @{
        FinalStatus = 'UNKNOWN'  # HAS_BLOCKERS | NO_BLOCKERS | UNKNOWN
        Questions   = @()
        IsAmbiguous = $false
        Diagnostics = @()
    }

    if (-not $Lines -or $Lines.Count -eq 0) {
        $result.Diagnostics += 'open_questions.md is empty.'
        $result.FinalStatus = 'UNKNOWN'
        $result.IsAmbiguous = $true
        return $result
    }

    $blockerLines = @()
    foreach ($l in $Lines) {
        if ($null -ne $l -and ($l -match '(?i)\bBLOCKER\b')) {
            $blockerLines += $l
        }
    }

    if ($blockerLines.Count -gt 0) {
        $questions = @()
        foreach ($line in $blockerLines) {
            $text = $line
            # Common formats:
            # - [BLOCKER] some question
            # - BLOCKER: some question
            # - ... (BLOCKER) some question
            if ($text -match '^\s*-\s*\[\s*BLOCKER\s*\]\s*[:\-]?\s*(.+)$') {
                $text = $Matches[1]
            }
            elseif ($text -match '(?i)BLOCKER\s*[:\-]?\s*(.+)$') {
                $text = $Matches[1]
            }
            elseif ($text -match '^(.+?)\s*\(\s*(?i)BLOCKER\s*\)\s*$') {
                $text = $Matches[1]
            }
            else {
                $text = ($text -replace '(?i)\bBLOCKER\b', '').Trim()
                $text = $text.Trim(':','-',' ')
            }

            if ($text -and $text.Trim().Length -gt 0) {
                $questions += $text.Trim()
            }
        }

        $result.FinalStatus = 'HAS_BLOCKERS'
        $result.Questions = $questions
        $result.IsAmbiguous = $false
        $result.Diagnostics += "Found BLOCKER markers in open_questions.md: $($blockerLines.Count)."
        return $result
    }

    $hasNoQuestionsMarker =
        ($Lines -match '(?i)\bno\s+open\s+questions\b') -or
        ($Lines -match '(?i)\bнет\s+открытых\s+вопросов\b')

    if ($hasNoQuestionsMarker) {
        $result.FinalStatus = 'NO_BLOCKERS'
        $result.Questions = @()
        $result.IsAmbiguous = $false
        $result.Diagnostics += 'open_questions.md states there are no open questions.'
        return $result
    }

    # No BLOCKER and no explicit "no questions": treat as ambiguous.
    $result.FinalStatus = 'UNKNOWN'
    $result.IsAmbiguous = $true
    $result.Diagnostics += 'No explicit BLOCKER markers found in open_questions.md and no explicit "no open questions" marker detected.'
    return $result
}

function Parse-OpenQuestionsSummarySection {
    [OutputType([hashtable])]
    param(
        [string[]]$Lines
    )

    $result = @{
        SectionLines = @()
        Diagnostics  = @()
    }

    if (-not $Lines -or $Lines.Count -eq 0) {
        $result.Diagnostics += 'status.md content is empty.'
        return $result
    }

    $startIndex = $Lines.IndexOf('## Open Questions Summary')
    if ($startIndex -lt 0) {
        $result.Diagnostics += 'Section ''## Open Questions Summary'' not found in status.md.'
        return $result
    }

    $sectionLines = @()
    for ($i = $startIndex + 1; $i -lt $Lines.Count; $i++) {
        $line = $Lines[$i]
        if ($line -like '## *') {
            break
        }
        if ($line.Trim().Length -gt 0) {
            $sectionLines += $line
        }
    }

    $result.SectionLines = $sectionLines
    return $result
}

function Convert-OpenQuestionsSummaryToBlockingResult {
    [OutputType([BlockingQuestionsResult])]
    param(
        [string[]]$SummaryLines,
        [string[]]$Diagnostics
    )

    $res = [BlockingQuestionsResult]::new()

    $text = ($SummaryLines -join ' ')
    if ($text -match '(?i)\bnone\b') {
        $res.FinalStatus = 'NO_BLOCKERS'
        $res.IsAmbiguous = $false
        $res.SourceUsed = 'STATUS_FALLBACK'
        $res.Diagnostics += @($Diagnostics)
        $res.Diagnostics += 'Fallback summary indicates no open questions.'
        return $res
    }

    $res.FinalStatus = 'UNKNOWN'
    $res.IsAmbiguous = $true
    $res.SourceUsed = 'STATUS_FALLBACK'
    $res.Diagnostics += @($Diagnostics)
    $res.Diagnostics += 'Fallback summary did not clearly indicate "none".'
    return $res
}

function Get-BlockingQuestionsFromOpenQuestionsFile {
    [OutputType([BlockingQuestionsResult])]
    param(
        [string]$BasePath,
        [string]$OpenQuestionsFilePathOverride,
        [string]$StatusFilePathOverride
    )

    if ($OpenQuestionsFilePathOverride) {
        $openQuestionsPath = $OpenQuestionsFilePathOverride
    }
    else {
        $openQuestionsPath = Get-OpenQuestionsFilePath -BasePath $BasePath
    }

    $readResult = Read-OpenQuestionsFileContent -OpenQuestionsFilePath $openQuestionsPath
    $primaryDiag = @($readResult.Diagnostics)

    if ($readResult.Lines -and $readResult.Lines.Count -gt 0) {
        $parsed = Parse-BlockingQuestionsFromOpenQuestionsLines -Lines $readResult.Lines

        $res = [BlockingQuestionsResult]::new()
        $res.FinalStatus = $parsed.FinalStatus
        $res.Questions = @($parsed.Questions)
        $res.IsAmbiguous = [bool]$parsed.IsAmbiguous
        $res.SourceUsed = 'OPEN_QUESTIONS_PRIMARY'
        $res.Diagnostics += @($parsed.Diagnostics)
        return $res
    }

    # Fallback when primary cannot be used
    if ($StatusFilePathOverride) {
        $statusPath = $StatusFilePathOverride
    }
    else {
        $statusPath = Get-StatusFilePath -BasePath $BasePath
    }
    $statusRead = Read-StatusFileContent -StatusFilePath $statusPath
    $openSummaryParsed = Parse-OpenQuestionsSummarySection -Lines $statusRead.Lines
    $res = Convert-OpenQuestionsSummaryToBlockingResult -SummaryLines $openSummaryParsed.SectionLines -Diagnostics $statusRead.Diagnostics

    if ($openSummaryParsed.Diagnostics) {
        $res.Diagnostics += @($openSummaryParsed.Diagnostics)
    }
    if ($primaryDiag) {
        $res.Diagnostics += $primaryDiag
    }

    return $res
}

function Get-BlockingQuestionsStub {
    [OutputType([BlockingQuestionsResult])]
    param ()

    $result = [BlockingQuestionsResult]::new()
    $result.FinalStatus = 'UNKNOWN'
    $result.SourceUsed = 'NONE (stub)'
    $result.IsAmbiguous = $true
    $result.Diagnostics += 'BlockingQuestionsResult is a stub. open_questions.md and status.md are not read yet.'
    return $result
}

function Get-NormalizedRelativePathFromRunRoot {
    [OutputType([string])]
    param (
        [Parameter(Mandatory = $true)]
        [string]$RunRoot,
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )

    $rootResolved = [System.IO.Path]::GetFullPath($RunRoot)
    $fileResolved = [System.IO.Path]::GetFullPath($FilePath)

    $rootPrefix = $rootResolved
    if (-not ($rootPrefix.EndsWith([System.IO.Path]::DirectorySeparatorChar) -or $rootPrefix.EndsWith([System.IO.Path]::AltDirectorySeparatorChar))) {
        $rootPrefix = $rootPrefix + [System.IO.Path]::DirectorySeparatorChar
    }

    if ($fileResolved.Length -ge $rootPrefix.Length -and $fileResolved.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return ($fileResolved.Substring($rootPrefix.Length) -replace '\\', '/')
    }

    return [System.IO.Path]::GetFileName($fileResolved)
}

function Get-RunArtifactsFromCurrentRun {
    [OutputType([ArtifactEntry[]])]
    param (
        [int]$Top = 10,
        [string]$CurrentRunDirectoryOverride
    )

    $defaultCurrentRunRoot = Join-Path (Split-Path -Parent (Split-Path -Parent $PSCommandPath)) 'current-run'
    $currentRunDir = if ($CurrentRunDirectoryOverride) { $CurrentRunDirectoryOverride } else { $defaultCurrentRunRoot }

    $entries = @()
    $files = @()
    if (-not (Test-Path -LiteralPath $currentRunDir)) {
        return @()
    }

    try {
        $files = Get-ChildItem -LiteralPath $currentRunDir -Recurse -File -Filter '*.md' -ErrorAction SilentlyContinue
    }
    catch {
        return @()
    }

    $files = @(
        $files | Where-Object {
            -not [string]::Equals(
                [System.IO.Path]::GetFileName($_.FullName),
                'README.md',
                [System.StringComparison]::OrdinalIgnoreCase)
        }
    )

    $sorted = $files | Sort-Object -Property `
        @{ Expression = { $_.LastWriteTime }; Descending = $true }, `
        @{ Expression = {
            Get-NormalizedRelativePathFromRunRoot -RunRoot $currentRunDir -FilePath $_.FullName
        }; Ascending = $true }

    $topFiles = $sorted | Select-Object -First $Top

    foreach ($f in $topFiles) {
        $relativeFromCurrentRun = Get-NormalizedRelativePathFromRunRoot -RunRoot $currentRunDir -FilePath $f.FullName
        $entry = [ArtifactEntry]::new()
        $entry.RelativePath = ("multi-agent-system/current-run/{0}" -f $relativeFromCurrentRun)
        $entry.MTime = $f.LastWriteTime.ToString('s')
        $entry.IsReadable = $true
        $entry.Diagnostics = $null
        $entries += $entry
    }

    return @($entries)
}

function Build-StatusSurfaceReport {
    [OutputType([StatusSurfaceReport])]
    param (
        [int]$Top = 10,
        [string]$BasePath,
        [string]$StatusFilePathOverride,
        [string]$OpenQuestionsFilePathOverride,
        [string]$CurrentRunDirectoryOverride
    )

    $report = [StatusSurfaceReport]::new()
    $report.SystemState = Get-SystemStateFromStatusFile -BasePath $BasePath -StatusFilePathOverride $StatusFilePathOverride
    $report.Blocking = Get-BlockingQuestionsFromOpenQuestionsFile -BasePath $BasePath -OpenQuestionsFilePathOverride $OpenQuestionsFilePathOverride -StatusFilePathOverride $StatusFilePathOverride
    $report.Artifacts = Get-RunArtifactsFromCurrentRun -Top $Top -CurrentRunDirectoryOverride $CurrentRunDirectoryOverride
    $report.GeneratedAt = Get-Date
    $report.IsStub = $false

    return $report
}

Export-ModuleMember -Function `
    Get-SystemStateStub, `
    Get-StatusFilePath, `
    Read-StatusFileContent, `
    Get-SystemStateSection, `
    Convert-SystemStateLinesToObject, `
    Get-SystemStateFromStatusFile, `
    Get-BlockingQuestionsStub, `
    Get-BlockingQuestionsFromOpenQuestionsFile, `
    Get-RunArtifactsFromCurrentRun, `
    Build-StatusSurfaceReport

