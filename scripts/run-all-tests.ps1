$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (!(Test-Path .venv/Scripts/python.exe)) {python -m venv .venv}
& .venv/Scripts/python -m pip install -r requirements.txt
if ($LASTEXITCODE) {exit 1}
if (!(Test-Path .env.demo-login) -and !$env:DOCUFLOW_DEMO_PASSWORD) {throw 'Set DOCUFLOW_DEMO_PASSWORD to the password printed during setup.'}
& .venv/Scripts/python tests/verify.py
if ($LASTEXITCODE) {exit 1}
& .venv/Scripts/python tests/finish.py
exit $LASTEXITCODE
