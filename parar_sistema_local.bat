@echo off
echo ========================================
echo   Parando Sistema Local
echo ========================================
echo.

echo Encerrando processos Python...
taskkill /f /im python.exe 2>nul
taskkill /f /im uvicorn.exe 2>nul

echo Sistema parado!
echo.
pause