$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (!(Test-Path .venv/Scripts/python.exe)) {
    throw '.venv not found. Run scripts\run-all-tests.ps1 or create .venv first.'
}
& .venv/Scripts/python.exe scripts/generate-samples.py
exit $LASTEXITCODE
