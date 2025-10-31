@echo off
echo ========================================
echo    Sistema de Gestao de Frotas (Local)
echo ========================================
echo.

echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado.
    echo Por favor, instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

echo Python encontrado!
echo.

echo Instalando dependencias do backend (versoes compatveis)...
cd backend_fastapi

echo Instalando pacotes principais...
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pydantic pydantic-settings python-jose passlib python-multipart python-dotenv requests pandas openpyxl

echo Tentando instalar Pillow...
pip install Pillow

if %errorlevel% neq 0 (
    echo Aviso: Pillow falhou, tentando versao mais nova...
    pip install --upgrade Pillow
)

cd ..

echo.
echo Instalando dependencias do dashboard...
cd flask_dashboard
pip install flask requests jinja2 werkzeug python-dotenv markupsafe
cd ..

echo.
echo ========================================
echo    Iniciando servicos...
echo ========================================
echo.

echo Iniciando Backend (FastAPI)...
start "Backend FastAPI" cmd /k "cd backend_fastapi && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload"

echo Aguardando backend iniciar...
timeout /t 5 /nobreak >nul

echo Iniciando Dashboard (Flask)...
start "Dashboard Flask" cmd /k "cd flask_dashboard && python app/dashboard.py"

echo.
echo ========================================
echo    Servicos iniciados!
echo ========================================
echo.
echo Backend:     http://localhost:8005/docs
echo Dashboard:   http://localhost:8050
echo.
echo Aguardando servicos carregarem completamente...
timeout /t 8 /nobreak >nul

echo Abrindo navegadores automaticamente...
start http://localhost:8005/docs
start http://localhost:8050

echo.
echo IMPORTANTE:
echo - Configure o banco de dados no arquivo .env
echo - Para parar, feche as janelas do terminal abertas
echo.
pause