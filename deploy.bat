@echo off
REM ==============================
REM Script de Deploy - Sistema de Gestão de Frotas
REM Transpontual
REM ==============================

echo ========================================
echo Deploy do Sistema de Gestão de Frotas
echo Transpontual
echo ========================================

REM Verificar se Docker está disponível
docker --version >nul 2>&1
if errorlevel 1 (
    echo Erro: Docker não está instalado ou não está em execução
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Erro: Docker Compose não está instalado
    pause
    exit /b 1
)

REM Verificar se arquivo .env existe
if not exist ".env" (
    echo Erro: Arquivo .env não encontrado
    echo Copie o arquivo .env.example para .env e configure as variáveis
    pause
    exit /b 1
)

REM Verificar se as senhas padrão foram alteradas
findstr /C:"MUDE_ESTA_SENHA" .env >nul 2>&1
if not errorlevel 1 (
    echo Erro: Você deve alterar as senhas padrão no arquivo .env
    pause
    exit /b 1
)

echo 1. Parando containers existentes...
docker-compose down

echo 2. Construindo imagens...
docker-compose build

echo 3. Iniciando serviços...
docker-compose up -d

echo 4. Aguardando banco de dados...
timeout /t 10 /nobreak

echo 5. Executando migrações...
docker-compose exec -T backend python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine); print('Migracoes executadas')"

echo 6. Criando usuário administrador...
docker-compose exec -T backend python create_admin.py

echo ========================================
echo Deploy concluído com sucesso!
echo ========================================
echo Sistema disponível em:
echo Dashboard: http://localhost:8050
echo API: http://localhost:8005
echo.
echo Credenciais iniciais:
echo Email: admin@transpontual.com
echo Senha: admin123
echo.
echo IMPORTANTE: Altere a senha do administrador após o primeiro login!
echo ========================================

REM Mostrar status dos containers
echo Status dos containers:
docker-compose ps

pause