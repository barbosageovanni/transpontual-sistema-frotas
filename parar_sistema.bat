@echo off
echo ========================================
echo   Parando Sistema de Gestao de Frotas
echo ========================================
echo.

echo Parando servicos Docker...
docker compose down

if %errorlevel% equ 0 (
    echo.
    echo Servicos parados com sucesso!
) else (
    echo.
    echo Erro ao parar servicos.
)

echo.
pause