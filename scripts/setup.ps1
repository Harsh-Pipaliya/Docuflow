$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (!(Test-Path .env)) {
    docker build -t docuflow-app:local .
    if ($LASTEXITCODE) {throw 'Image build failed'}
    $pair=docker run --rm docuflow-app:local python -c "import bcrypt,secrets,json; p=secrets.token_urlsafe(16); print(json.dumps([p,bcrypt.hashpw(p.encode(),bcrypt.gensalt()).decode()]))" | ConvertFrom-Json
    if (!$pair) {throw 'Password generation failed'}
    Set-Content -Encoding ascii .env ("DEMO_PASSWORD_HASH='"+$pair[1]+"'")
    Set-Content -Encoding ascii .env.demo-login $pair[0]
    Write-Host ('Demo username: demo. Save this local password: '+$pair[0])
}
docker compose build api
if ($LASTEXITCODE) {exit 1}
docker compose up -d --no-build
exit $LASTEXITCODE

