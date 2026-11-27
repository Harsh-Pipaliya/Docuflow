$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

if (!(Test-Path .env.demo-login) -and !$env:DOCUFLOW_DEMO_PASSWORD) {
    throw 'Set DOCUFLOW_DEMO_PASSWORD or ensure .env.demo-login exists.'
}

& .venv/Scripts/python.exe scripts/generate-samples.py
if ($LASTEXITCODE) { exit $LASTEXITCODE }

$py = @'
import os
from pathlib import Path
import requests

base = "http://127.0.0.1:8080"
password = os.getenv("DOCUFLOW_DEMO_PASSWORD") or Path(".env.demo-login").read_text().strip()
s = requests.Session()
csrf = s.get(f"{base}/api/auth/me", timeout=10).json()["csrf"]
s.headers.update({"X-CSRF-Token": csrf})
r = s.post(f"{base}/api/auth/login", json={"username": "demo", "password": password}, timeout=10)
r.raise_for_status()
s.headers.update({"X-CSRF-Token": r.json()["csrf"]})

samples = Path("samples/generated")
for fname in ["valid.pdf", "multipage.pdf", "identical.pdf", "marker.pdf", "corrupt.pdf"]:
    resp = s.post(f"{base}/api/documents", files={"file": (fname, (samples / fname).read_bytes(), "application/pdf")}, timeout=30)
    resp.raise_for_status()
    print(f"Uploaded {fname}: HTTP {resp.status_code} -> {resp.json()}")
'@

$py | & .venv/Scripts/python.exe -
exit $LASTEXITCODE
