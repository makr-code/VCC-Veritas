@echo off
REM VERITAS Services Stopper - Schnellzugriff

echo.
echo ====================================
echo   VERITAS Services stoppen
echo ====================================
echo.

powershell -ExecutionPolicy Bypass -File "scripts\stop_services.ps1" %*

if errorlevel 1 (
    echo.
    echo Hinweis: Es gab Probleme beim Stoppen
    pause
    exit /b 1
)

echo.
pause
