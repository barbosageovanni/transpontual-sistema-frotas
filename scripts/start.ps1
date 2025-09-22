Param(
    [int]$BuildTimeoutSeconds = 300,
    [int]$DbWaitSeconds = 25
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

Write-Host "=== Transpontual - Start (Docker + Seed) ===" -ForegroundColor Cyan

# 1) Garantir .env
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Criado .env a partir de .env.example" -ForegroundColor Yellow
    } else {
        Write-Error "Arquivo .env.example não encontrado. Crie .env manualmente."
        exit 1
    }
}

# 2) Subir containers
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

& $composeCmd up -d --build
if ($LASTEXITCODE -ne 0) {
    Write-Error "Falha ao subir containers."
    exit 1
}

Write-Host "Aguardando banco iniciar ($DbWaitSeconds s)..." -ForegroundColor Yellow
Start-Sleep -Seconds $DbWaitSeconds

# 3) Preparar seed: instalar dependências mínimas para rodar scripts/apply_sql.py
Write-Host "Instalando dependências Python para seed (local)..." -ForegroundColor Yellow
python -m pip install --quiet --disable-pip-version-check SQLAlchemy psycopg2-binary python-dotenv | Out-Null

# 4) Ajustar DATABASE_URL temporário para host (localhost)
$originalDatabaseUrl = $env:DATABASE_URL
$hostDatabaseUrl = "postgresql+psycopg2://postgres:postgres@localhost:5432/frotadb"
$env:DATABASE_URL = $hostDatabaseUrl

# 5) Rodar seed com retries
$maxRetries = 5
for ($i = 1; $i -le $maxRetries; $i++) {
    Write-Host "Aplicando DDL/seed (tentativa $i de $maxRetries)..." -ForegroundColor Cyan
    python scripts/apply_sql.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Seed aplicado com sucesso." -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 5
}
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Não foi possível aplicar o seed automaticamente. Tente novamente depois que o DB estiver pronto."
}

# 6) Restaurar DATABASE_URL anterior
if ($null -ne $originalDatabaseUrl) {
    $env:DATABASE_URL = $originalDatabaseUrl
} else {
    Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue | Out-Null
}

Write-Host "\n=== Serviços Online ===" -ForegroundColor Green
Write-Host "API:       http://localhost:8005/docs"
Write-Host "Dashboard: http://localhost:8050"
Write-Host "Login DEV: admin@transpontual.com / admin123"

