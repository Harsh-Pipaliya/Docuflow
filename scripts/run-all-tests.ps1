$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (!(Test-Path .venv/Scripts/python.exe)) {python -m venv .venv}
& .venv/Scripts/python -m pip install -r requirements.txt
if ($LASTEXITCODE) {exit 1}
if (!(Test-Path .env.demo-login) -and !$env:DOCUFLOW_DEMO_PASSWORD) {throw 'Set DOCUFLOW_DEMO_PASSWORD to the password printed during setup.'}
& .venv/Scripts/python tests/verify.py
if ($LASTEXITCODE) {exit 1}
& .venv/Scripts/python tests/finish.py
if ($LASTEXITCODE) {exit 1}
& .venv/Scripts/python scripts/generate-samples.py
if ($LASTEXITCODE) {exit 1}
& .venv/Scripts/python tests/extra.py
if ($LASTEXITCODE) {exit 1}
docker compose exec -T processor python -m tests.reliability | Tee-Object evidence/after/reliability.txt
if ($LASTEXITCODE) {exit 1}
docker compose exec -T api python -m tests.session_expiry | Tee-Object evidence/after/session-expiry.txt
exit $LASTEXITCODE
