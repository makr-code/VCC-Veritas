# VERITAS Service Starter - Backend + Frontend
# Startet beide Services parallel

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

function Write-Header($text) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host " $text" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Write-Step($text) {
    Write-Host "-> $text" -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "  [OK] $text" -ForegroundColor Green
}

function Write-Info($text) {
    Write-Host "  [INFO] $text" -ForegroundColor Blue
}

# Basis-Pfade/PID-Datei
$RootDir = Split-Path -Parent $PSScriptRoot
$PidDir = Join-Path $RootDir "data"
if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir | Out-Null }
$BackendPidFile = Join-Path $PidDir ".veritas_backend.pid"
"$null" | Out-Null

# Logs-Verzeichnis und Log-Datei
$LogsDir = Join-Path $RootDir "logs"
if (-not (Test-Path $LogsDir)) { New-Item -ItemType Directory -Path $LogsDir | Out-Null }
$BackendLogFile = Join-Path $LogsDir "backend_uvicorn.log"

Write-Header "VERITAS Service Starter"

# Backend starten
if (-not $FrontendOnly) {
    Write-Step "Starte Backend (Port 5000)..."

    # Clean Python cache (wichtig für Code-Updates)
    Write-Step "Loesche __pycache__ fuer frischen Start..."
    Get-ChildItem -Path (Join-Path $RootDir "backend") -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    Get-ChildItem -Path (Join-Path $RootDir "backend") -Filter "*.pyc" -Recurse -File -ErrorAction SilentlyContinue | Remove-Item -Force
    Write-Success "Cache gelöscht"

    # Sicherstellen, dass 'uds3' als Schwester-Ordner gefunden wird (falls vorhanden)
    try {
        $ParentDir = Split-Path -Parent $RootDir
        $pythonPathParts = @()
        # Repo-Root selbst (für 'backend', 'shared', etc.)
        $pythonPathParts += $RootDir
        # Falls ein lokales uds3 innerhalb des Repos liegt
        if (Test-Path (Join-Path $RootDir 'uds3')) { $pythonPathParts += (Join-Path $RootDir '') }
        # Falls uds3 als Schwester-Ordner existiert (z.B. C:\VCC\uds3)
        if (Test-Path (Join-Path $ParentDir 'uds3')) { $pythonPathParts += $ParentDir }
        # PYTHONPATH setzen (vorhandene Werte beibehalten)
        $existingPyPath = $env:PYTHONPATH
        $newPyPath = ($pythonPathParts -join ';')
        if ([string]::IsNullOrEmpty($existingPyPath)) {
            $env:PYTHONPATH = $newPyPath
        } else {
            $env:PYTHONPATH = "$newPyPath;$existingPyPath"
        }
    Write-Info "PYTHONPATH gesetzt: $($env:PYTHONPATH)"
    } catch {
        Write-Host "  [WARN] Konnte PYTHONPATH nicht setzen: $_" -ForegroundColor Yellow
    }

    # Starte gezielt den uvicorn Prozess und speichere PID
    # ⚡ Backend v4.0.0: Unified backend.app:app (flat structure)
    $arguments = "-m uvicorn backend.app:app --host 0.0.0.0 --port 5000 --log-level info"
    try {
        # Vor Start: alte Log-Datei rotieren
        if (Test-Path $BackendLogFile) {
            try { Move-Item -Path $BackendLogFile -Destination ($BackendLogFile + ".old") -Force -ErrorAction SilentlyContinue } catch {}
        }

        $BackendErrFile = $BackendLogFile.Replace('.log', '.err.log')
        $proc = Start-Process -FilePath "python" -ArgumentList $arguments -WorkingDirectory $RootDir -PassThru -WindowStyle Hidden -RedirectStandardOutput $BackendLogFile -RedirectStandardError $BackendErrFile
        $proc.Id | Out-File -FilePath $BackendPidFile -Encoding ascii -Force
        Write-Success "Backend v4.0.0 gestartet (PID: $($proc.Id))"
        Write-Info "PID gespeichert in: $BackendPidFile"
        Write-Info "Logs: $BackendLogFile"
        Write-Info "Errors: $BackendErrFile"
    } catch {
        Write-Host "  [ERROR] Backend konnte nicht gestartet werden: $_" -ForegroundColor Red
        exit 1
    }

    # Health Check mit Retry (max. 20s) - Backend v4.0.0
    Write-Info "Pruefe Health-Status (bis zu 20s)..."
    $healthy = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/api/system/health" -TimeoutSec 2 -ErrorAction Stop
            $healthy = $true
            Write-Success "Backend v4.0.0 Health Check: OK"
            if ($response.status) {
                Write-Host "    Status: $($response.status)" -ForegroundColor Gray
                if ($response.components) {
                    Write-Host "    Components:" -ForegroundColor Gray
                    if ($response.components.uds3) { Write-Host "      - UDS3: OK" -ForegroundColor Green }
                    if ($response.components.pipeline) { Write-Host "      - Pipeline: OK" -ForegroundColor Green }
                    if ($response.components.agents) { Write-Host "      - Agents: OK" -ForegroundColor Green }
                }
            }
            break
        } catch { Start-Sleep -Milliseconds 800 }
    }
    if (-not $healthy) {
        Write-Host "  [WARN] Backend Health Check fehlgeschlagen (bitte Logs pruefen)" -ForegroundColor Yellow
        Write-Host "     Tipp: Get-CimInstance Win32_Process -Filter 'ProcessId = $((Get-Content $BackendPidFile))' | Select-Object CommandLine" -ForegroundColor DarkYellow
        if (Test-Path $BackendLogFile) {
            Write-Host "     Letzte Log-Zeilen:" -ForegroundColor DarkYellow
            try { Get-Content -Path $BackendLogFile -Tail 60 | ForEach-Object { Write-Host ("       " + $_) -ForegroundColor DarkGray } } catch {}
        }
    }
}

# Frontend starten
if (-not $BackendOnly) {
    Write-Step "Starte Frontend (GUI)..."
    
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        python frontend\veritas_app.py
    }
    
    Write-Success "Frontend gestartet (Job ID: $($frontendJob.Id))"
    Write-Info "GUI sollte sich öffnen..."
}

# Status anzeigen
Write-Host "`n" -NoNewline
Write-Header "Services gestartet"

if (-not $FrontendOnly) {
    Write-Host "Backend v4.0.0:  " -NoNewline -ForegroundColor White
    Write-Host "http://127.0.0.1:5000" -ForegroundColor Cyan
    Write-Host "  • Health:    http://127.0.0.1:5000/api/system/health" -ForegroundColor Gray
    Write-Host "  • Info:      http://127.0.0.1:5000/api/system/info" -ForegroundColor Gray
    Write-Host "  • Docs:      http://127.0.0.1:5000/docs" -ForegroundColor Gray
    Write-Host "  • Query:     http://127.0.0.1:5000/api/query" -ForegroundColor Gray
    if (Test-Path $BackendPidFile) {
        $backendPid = Get-Content $BackendPidFile -ErrorAction SilentlyContinue
        if ($backendPid) { Write-Host "  • PID:       $backendPid" -ForegroundColor Gray }
    }
}

if (-not $BackendOnly) {
    Write-Host "`nFrontend: " -NoNewline -ForegroundColor White
    Write-Host "GUI (Tkinter)" -ForegroundColor Cyan
    Write-Host "  - Job ID:    $($frontendJob.Id)" -ForegroundColor Gray
}

# Befehle anzeigen
Write-Host "`nNuetzliche Befehle:" -ForegroundColor Cyan
Write-Host "  - Logs anzeigen:    Get-Job | Receive-Job -Keep" -ForegroundColor White
Write-Host "  - Backend stoppen:  .\\scripts\\stop_services.ps1 -BackendOnly" -ForegroundColor White
Write-Host "  - Status pruefen:    Get-Job" -ForegroundColor White

Write-Host "`nServices laufen im Hintergrund!`n" -ForegroundColor Green
