$ErrorActionPreference='Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$context=docker context inspect --format '{{.Endpoints.docker.Host}}'
if ($env:DOCKER_HOST -or $context -notmatch '^npipe:'){throw 'Reset requires the local Windows Docker engine'}
$config=docker compose config --format json | ConvertFrom-Json
if ($config.name -ne 'docuflow' -or $config.services.api.environment.EMULATOR_URL -ne 'http://cloud:4588' -or $config.services.cloud.image -notlike 'floci/floci-gcp@sha256:*'){throw 'Unexpected project or emulator'}
docker compose down --volumes
if ($LASTEXITCODE) {exit 1}
docker compose up -d --no-build
exit $LASTEXITCODE
