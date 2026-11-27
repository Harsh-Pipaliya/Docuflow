$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (!(Test-Path .env)) {
    docker build -t docuflow-app:local .
    if ($LASTEXITCODE) {throw 'Image build failed'}
    $pair=docker run --rm docuflow-app:local python -c "import bcrypt,secrets,json; p=secrets.token_urlsafe(16); print(json.dumps([p,bcrypt.hashpw(p.encode(),bcrypt.gensalt()).decode()]))" | ConvertFrom-Json
    if (!$pair) {throw 'Password generation failed'}
    Set-Content -Encoding ascii .env ("DEMO_PASSWORD_HASH='"+$pair[1]+"'")
    Write-Host ('Demo username: demo. Save this local password: '+$pair[0])
}
docker compose up -d --build
exit $LASTEXITCODE
