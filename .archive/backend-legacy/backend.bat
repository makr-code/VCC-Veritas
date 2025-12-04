@echo off
REM VERITAS Backend Management - Schnellzugriff

if "%1"=="" (
    echo.
    echo VERITAS Backend Management
    echo ========================
    echo.
    echo Verwendung: backend.bat [start^|stop^|restart^|status]
    echo.
    echo   start   - Startet das Backend
    echo   stop    - Stoppt das Backend
    echo   restart - Startet das Backend neu
    echo   status  - Zeigt Backend-Status
    echo.
    exit /b 1
)

powershell -ExecutionPolicy Bypass -File "manage_backend.ps1" -Action %1
