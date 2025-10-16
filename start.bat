@echo off
REM VERITAS Services Starter - Schnellzugriff

echo.
echo ====================================
echo   VERITAS Services starten
echo ====================================
echo.

powershell -ExecutionPolicy Bypass -File "scripts\start_services.ps1" %*

if errorlevel 1 (
    echo.
    echo Fehler beim Starten der Services!
    pause
    exit /b 1
)

echo.
echo Services erfolgreich gestartet!
pause
