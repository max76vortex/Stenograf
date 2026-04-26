# Smoke: venv + pip + --help для transcribe_to_obsidian.py и check_coverage.py
# Запуск из папки transcription:  pwsh -File .\run-smoke-test.ps1
# Или из корня репозитория:       pwsh -File .\transcription\run-smoke-test.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$here = $PSScriptRoot
Set-Location -LiteralPath $here

$venvPython = Join-Path $here ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "Creating venv in $here\.venv ..."
    $venvPath = Join-Path $here ".venv"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $venvPath
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venvPath
    } else {
        throw "Need Python: install from python.org or ensure 'py' / 'python' is in PATH."
    }
    if (-not (Test-Path -LiteralPath $venvPython)) {
        throw "venv python not found at $venvPython"
    }
}

Write-Host "pip install -r requirements.txt ..."
& $venvPython -m pip install -r (Join-Path $here "requirements.txt")

Write-Host "`n--- transcribe_to_obsidian.py --help ---"
& $venvPython (Join-Path $here "transcribe_to_obsidian.py") --help

Write-Host "`n--- check_coverage.py --help ---"
& $venvPython (Join-Path $here "check_coverage.py") --help

Write-Host "`n--- unittest discover transcription/tests ---"
& $venvPython -m unittest discover -s (Join-Path $here "tests") -p "test_*.py"

Write-Host "`n[OK] Smoke test finished (no transcription run; model not downloaded until first real transcribe)."
