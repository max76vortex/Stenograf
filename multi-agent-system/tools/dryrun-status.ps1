<#
  Dry run status surface CLI.
  Renders System State (including next expected step and confirmed stages), blocking questions, and artifacts.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [Alias('Limit')]
    [int]$Top = 10,
    [Parameter(Mandatory = $false)]
    [Alias('StatusPath')]
    [string]$StatusFilePathOverride,
    [Parameter(Mandatory = $false)]
    [Alias('OpenQuestionsPath')]
    [string]$OpenQuestionsFilePathOverride,
    [Parameter(Mandatory = $false)]
    [Alias('RunPath')]
    [string]$CurrentRunDirectoryOverride
)

function Get-ScriptRoot {
    if ($PSScriptRoot) {
        return $PSScriptRoot
    }
    return (Split-Path -Parent $MyInvocation.MyCommand.Path)
}

function Initialize-DryRunStatusEnvironment {
    param(
        [int]$Top,
        [string]$StatusFilePathOverride,
        [string]$CurrentRunDirectoryOverride
    )

    $scriptRoot = Get-ScriptRoot

    $global:DryRunStatus_Context = [PSCustomObject]@{
        ScriptRoot          = $scriptRoot
        WorkspaceRoot       = (Split-Path -Parent $scriptRoot)
        MultiAgentRoot      = (Split-Path -Parent $scriptRoot)
        Top                 = $Top
        StatusFilePath      = if ($StatusFilePathOverride) { $StatusFilePathOverride } else { Join-Path (Split-Path -Parent $scriptRoot) 'status.md' }
        CurrentRunDirectory = if ($CurrentRunDirectoryOverride) { $CurrentRunDirectoryOverride } else { Join-Path (Split-Path -Parent $scriptRoot) 'current-run' }
        IsStub              = $true
    }
}

function Import-DryRunInternalModule {
    $scriptRoot = Get-ScriptRoot
    $internalModulePath = Join-Path $scriptRoot 'dryrun-status.internal.psm1'

    if (Test-Path -LiteralPath $internalModulePath) {
        # Suppress PowerShell name-verb warnings for internal helper functions.
        Import-Module -Name $internalModulePath -DisableNameChecking -ErrorAction Stop | Out-Null
    }
    else {
        throw "Internal module 'dryrun-status.internal.psm1' not found at '$internalModulePath'. Task 01 expects this module to be present."
    }
}

function Show-StatusSurfaceReport {
    param(
        [Parameter(Mandatory = $true)]
        $Report
    )

    Write-Host '========================================'
    Write-Host ' Dry Run Status Surface '
    Write-Host '========================================'
    Write-Host ''

    $generatedAtSuffix = ''
    if ($null -ne $Report -and $null -ne $Report.SystemState) {
        if ($Report.SystemState.Status -match '\(stub\)' -or $Report.SystemState.Variant -match '\(stub\)') {
            $generatedAtSuffix = ' (stub)'
        }
    }

    if ($null -ne $Report.GeneratedAt) {
        Write-Host ('Generated at: {0}' -f $Report.GeneratedAt.ToString('s')) $generatedAtSuffix
    }
    else {
        Write-Host ('Generated at: <unknown>{0}' -f $generatedAtSuffix)
    }

    if ($null -ne $global:DryRunStatus_Context) {
        Write-Host ('Script root: {0}' -f $global:DryRunStatus_Context.ScriptRoot)
        Write-Host ('Workspace root (heuristic): {0}' -f $global:DryRunStatus_Context.WorkspaceRoot)
        Write-Host ('Status path (expected): {0}' -f $global:DryRunStatus_Context.StatusFilePath)
        Write-Host ('Current-run dir (expected): {0}' -f $global:DryRunStatus_Context.CurrentRunDirectory)
    }
    Write-Host ''
    $systemStateLooksStub = $false
    if ($null -ne $Report -and $null -ne $Report.SystemState) {
        # In later tasks the report becomes partially real; this flag tells what part is stubbed.
        $systemStateLooksStub = ($Report.SystemState.Status -match '\(stub\)' -or $Report.SystemState.Variant -match '\(stub\)')
    }

    $blockingLooksStub = $false
    if ($null -ne $Report -and $null -ne $Report.Blocking -and $null -ne $Report.Blocking.SourceUsed) {
        $blockingLooksStub = ($Report.Blocking.SourceUsed -match '\(stub\)' -or $Report.Blocking.SourceUsed -match '^NONE')
    }

    $artifactsLooksStub = $false
    if ($null -ne $Report -and $null -ne $Report.Artifacts -and $Report.Artifacts.Count -gt 0) {
        $firstArtifact = $Report.Artifacts[0]
        $artifactsLooksStub = ($firstArtifact.MTime -match '\(stub\)' -or `
            ($firstArtifact.IsReadable -eq $false) -or `
            ($firstArtifact.Diagnostics -and ($firstArtifact.Diagnostics -match 'stub')))
    }

    if ($systemStateLooksStub -and $blockingLooksStub -and $artifactsLooksStub) {
        Write-Host 'NOTE: All sections are populated from stub implementations.'
    }
    elseif (-not $systemStateLooksStub -and $blockingLooksStub -and $artifactsLooksStub) {
        Write-Host 'NOTE: System State is read from status.md, but Blocking Questions and Last Artifacts are stubs.'
    }
    elseif (-not $systemStateLooksStub -and -not $blockingLooksStub -and -not $artifactsLooksStub) {
        Write-Host 'NOTE: All sections are populated with real data.'
    }
    else {
        Write-Host 'NOTE: Partial degradation/stubs detected; check diagnostics in the report.'
    }
    Write-Host ''

    Write-Host '--- System State ---'
    if ($null -ne $Report.SystemState) {
        Write-Host ('Variant         : {0}' -f $Report.SystemState.Variant)
        Write-Host ('Status          : {0}' -f $Report.SystemState.Status)
        Write-Host ('Current stage   : {0}' -f $Report.SystemState.CurrentStage)
        Write-Host ('Current iter.   : {0}' -f $Report.SystemState.CurrentIteration)
        Write-Host ('Active task     : {0}' -f $Report.SystemState.ActiveTask)
        Write-Host ('Last updated by : {0}' -f $Report.SystemState.LastUpdatedBy)
        $nextExpected = $Report.SystemState.NextExpectedStep
        if ([string]::IsNullOrWhiteSpace($nextExpected)) {
            $nextExpected = 'UNKNOWN'
        }
        Write-Host ('Next exp. step  : {0}' -f $nextExpected)
        Write-Host 'Confirmed stages:'
        $confirmed = $Report.SystemState.ConfirmedStages
        if ($null -eq $confirmed) {
            $confirmed = @()
        }
        if ($confirmed.Count -gt 0) {
            foreach ($s in $confirmed) {
                Write-Host ('  - {0}' -f $s)
            }
        }
        else {
            Write-Host '  (none)'
        }
        if ($Report.SystemState.Diagnostics -and $Report.SystemState.Diagnostics.Count -gt 0) {
            Write-Host 'Diagnostics:'
            foreach ($d in $Report.SystemState.Diagnostics) {
                Write-Host ('  - {0}' -f $d)
            }
        }
    }
    else {
        Write-Host 'SystemState is null.'
    }

    Write-Host ''
    if ($blockingLooksStub) {
        Write-Host '--- Blocking Questions (stub) ---'
    }
    else {
        Write-Host '--- Blocking Questions ---'
    }
    if ($null -ne $Report.Blocking) {
        Write-Host ('Final status : {0}' -f $Report.Blocking.FinalStatus)
        Write-Host ('Source used  : {0}' -f $Report.Blocking.SourceUsed)
        Write-Host ('Is ambiguous : {0}' -f $Report.Blocking.IsAmbiguous)
        if ($Report.Blocking.Diagnostics -and $Report.Blocking.Diagnostics.Count -gt 0) {
            Write-Host 'Diagnostics:'
            foreach ($d in $Report.Blocking.Diagnostics) {
                Write-Host ('  - {0}' -f $d)
            }
        }
        if ($Report.Blocking.Questions -and $Report.Blocking.Questions.Count -gt 0) {
            if ($blockingLooksStub) {
                Write-Host 'Questions (stubbed list):'
            }
            else {
                Write-Host 'Questions:'
            }
            foreach ($q in $Report.Blocking.Questions) {
                Write-Host ('  - {0}' -f $q)
            }
        }
        else {
            if ($blockingLooksStub) {
                Write-Host 'Questions list is empty (stub).'
            }
            else {
                Write-Host 'No blocking questions.'
            }
        }
    }
    else {
        if ($blockingLooksStub) {
            Write-Host 'BlockingQuestionsResult is null (stub).'
        }
        else {
            Write-Host 'BlockingQuestionsResult is null.'
        }
    }

    Write-Host ''
    if ($artifactsLooksStub) {
        Write-Host ('--- Last Artifacts (stub, Top = {0}) ---' -f $global:DryRunStatus_Context.Top)
    }
    else {
        Write-Host ('--- Last Artifacts (Top = {0}) ---' -f $global:DryRunStatus_Context.Top)
    }
    if ($null -ne $Report.Artifacts -and $Report.Artifacts.Count -gt 0) {
        $index = 0
        foreach ($a in $Report.Artifacts) {
            $index++
            Write-Host ('[{0}] {1}' -f $index, $a.RelativePath)
            Write-Host ('     mtime      : {0}' -f $a.MTime)
            Write-Host ('     isReadable : {0}' -f $a.IsReadable)
            if ($a.Diagnostics) {
                Write-Host ('     note       : {0}' -f $a.Diagnostics)
            }
        }
    }
    else {
        if ($artifactsLooksStub) {
            Write-Host 'No artifacts available (stub).'
        }
        else {
            Write-Host 'No artifacts to display.'
        }
    }

    Write-Host ''
    Write-Host 'END OF REPORT.'
}

function Invoke-DryRunStatus {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $false)]
        [int]$Top = 10,
        [string]$StatusFilePathOverride,
        [string]$OpenQuestionsFilePathOverride,
        [string]$CurrentRunDirectoryOverride
    )

    Initialize-DryRunStatusEnvironment -Top $Top -StatusFilePathOverride $StatusFilePathOverride -CurrentRunDirectoryOverride $CurrentRunDirectoryOverride

    try {
        Import-DryRunInternalModule
    }
    catch {
        Write-Error "Failed to import internal module for dry run status. Details: $($_.Exception.Message)"
        throw
    }

    try {
        $report = Build-StatusSurfaceReport -Top $Top `
            -StatusFilePathOverride $StatusFilePathOverride `
            -OpenQuestionsFilePathOverride $OpenQuestionsFilePathOverride `
            -CurrentRunDirectoryOverride $CurrentRunDirectoryOverride
        Show-StatusSurfaceReport -Report $report
    }
    catch {
        Write-Error "Unexpected error while building or rendering dry run status report. Details: $($_.Exception.Message)"
        throw
    }
}

try {
    Invoke-DryRunStatus -Top $Top `
        -StatusFilePathOverride $StatusFilePathOverride `
        -OpenQuestionsFilePathOverride $OpenQuestionsFilePathOverride `
        -CurrentRunDirectoryOverride $CurrentRunDirectoryOverride
}
catch {
    exit 1
}

