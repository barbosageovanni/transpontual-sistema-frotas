Param(
    [switch]$RemoveVolumes,
    [switch]$Prune
)

function Test-Command {
    param([string]$Name)
    $old = $ErrorActionPreference
    $ErrorActionPreference = 'SilentlyContinue'
    $null = Get-Command $Name
    $ok = $?
    $ErrorActionPreference = $old
    return $ok
}

Write-Host "=== Transpontual - Stop (Docker) ===" -ForegroundColor Cyan

$composeCmd = $null
if (Test-Command "docker") {
    if ((docker compose version) 2>$null) {
        $composeCmd = { docker compose }
    } elseif (Test-Command "docker-compose") {
        $composeCmd = { docker-compose }
    }
}
if (-not $composeCmd) {
    Write-Error "Docker (compose) não encontrado. Instale Docker Desktop."
    exit 1
}

if ($RemoveVolumes) {
    & $composeCmd down -v --remove-orphans
} else {
    & $composeCmd down --remove-orphans
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Falha ao parar serviços."
    exit $LASTEXITCODE
}

if ($Prune) {
    Write-Host "Limpando recursos não utilizados (docker system prune -f)..." -ForegroundColor Yellow
    docker system prune -f | Out-Null
    docker volume prune -f | Out-Null
}

Write-Host "Serviços parados." -ForegroundColor Green

