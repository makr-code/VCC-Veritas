#!/usr/bin/env pwsh
<#
.SYNOPSIS
    VERITAS API v3 Backend Management Script
    
.DESCRIPTION
    Verwaltet das VERITAS API v3 Backend (Start, Stop, Restart, Status)
    
.PARAMETER Action
    Aktion: start, stop, restart, status
    
.PARAMETER Wait
    Wartezeit in Sekunden nach dem Start (Standard: 5)
    
.EXAMPLE
    .\manage_backend_v3.ps1 -Action start
    .\manage_backend_v3.ps1 -Action stop
    .\manage_backend_v3.ps1 -Action restart
    .\manage_backend_v3.ps1 -Action status
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "test")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [int]$Wait = 5
)

# =============================================================================
# KONFIGURATION
# =============================================================================

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$BACKEND_SCRIPT = Join-Path $PROJECT_ROOT "start_backend.py"
$PID_FILE = Join-Path $PROJECT_ROOT "data" "backend_v3.pid"
$LOG_FILE = Join-Path $PROJECT_ROOT "data" "veritas_api_v3.log"
$API_BASE = "http://localhost:5000"
$API_V3_BASE = "$API_BASE/api/v3"

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Text)
    Write-Host "⚠️  $Text" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Text)
    Write-Host "ℹ️  $Text" -ForegroundColor Blue
}

function Get-BackendProcess {
    <#
    .SYNOPSIS
        Findet den Backend-Prozess
    #>
    
    # Versuche PID aus File zu lesen
    if (Test-Path $PID_FILE) {
        $processPid = Get-Content $PID_FILE -ErrorAction SilentlyContinue
        if ($processPid) {
            $process = Get-Process -Id $processPid -ErrorAction SilentlyContinue
            if ($process -and $process.ProcessName -eq "python") {
                return $process
            }
        }
    }
    
    # Fallback: Suche nach Python-Prozess mit start_backend.py
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue
    foreach ($proc in $processes) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -like "*start_backend.py*" -or $cmdLine -like "*veritas_api_backend_v3*") {
                return $proc
            }
        } catch {
            # CIM-Zugriff fehlgeschlagen, weiter
        }
    }
    
    return $null
}

function Stop-Backend {
    <#
    .SYNOPSIS
        Stoppt das Backend
    #>
    
    Write-Header "VERITAS Backend v3 Stoppen"
    
    $process = Get-BackendProcess
    
    if ($null -eq $process) {
        Write-Warning-Custom "Backend läuft nicht"
        
        # Cleanup PID-File
        if (Test-Path $PID_FILE) {
            Remove-Item $PID_FILE -Force
            Write-Info "PID-Datei gelöscht"
        }
        
        return $false
    }
    
    Write-Info "Backend-Prozess gefunden (PID: $($process.Id))"
    Write-Host "→ Stoppe Backend..." -ForegroundColor Yellow
    
    try {
        # Versuche graceful shutdown
        $process | Stop-Process -Force
        Start-Sleep -Seconds 2
        
        # Prüfe ob beendet
        $stillRunning = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
        if ($stillRunning) {
            Write-Warning-Custom "Prozess läuft noch, erzwinge Beendigung..."
            $stillRunning | Stop-Process -Force
            Start-Sleep -Seconds 1
        }
        
        Write-Success "Backend gestoppt"
        
        # Cleanup PID-File
        if (Test-Path $PID_FILE) {
            Remove-Item $PID_FILE -Force
        }
        
        return $true
    }
    catch {
        Write-Error-Custom "Fehler beim Stoppen: $_"
        return $false
    }
}

function Start-Backend {
    <#
    .SYNOPSIS
        Startet das Backend
    #>
    
    Write-Header "VERITAS Backend v3 Starten"
    
    # Prüfe ob bereits läuft
    $process = Get-BackendProcess
    if ($null -ne $process) {
        Write-Warning-Custom "Backend läuft bereits (PID: $($process.Id))"
        return $false
    }
    
    # Prüfe ob Backend-Script existiert
    if (-not (Test-Path $BACKEND_SCRIPT)) {
        Write-Error-Custom "Backend-Script nicht gefunden: $BACKEND_SCRIPT"
        return $false
    }
    
    Write-Info "Starte Backend..."
    Write-Info "Script: $BACKEND_SCRIPT"
    Write-Info "API Base: $API_V3_BASE"
    Write-Host ""
    
    try {
        # Wechsle ins Projektverzeichnis
        Push-Location $PROJECT_ROOT
        
        # Starte Backend im Hintergrund
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "python"
        $processInfo.Arguments = $BACKEND_SCRIPT
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        $processInfo.RedirectStandardOutput = $false
        $processInfo.RedirectStandardError = $false
        $processInfo.WorkingDirectory = $PROJECT_ROOT
        
        $proc = New-Object System.Diagnostics.Process
        $proc.StartInfo = $processInfo
        $proc.Start() | Out-Null
        
        Pop-Location
        
        # Speichere PID
        $proc.Id | Out-File $PID_FILE -Force
        
        Write-Success "Backend-Prozess gestartet (PID: $($proc.Id))"
        Write-Info "Warte $Wait Sekunden auf Initialisierung..."
        
        # Warte auf Start
        Start-Sleep -Seconds $Wait
        
        # Prüfe ob Prozess noch läuft
        $stillRunning = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
        if ($null -eq $stillRunning) {
            Write-Error-Custom "Backend-Prozess wurde beendet (Check Logs: $LOG_FILE)"
            return $false
        }
        
        Write-Success "Backend läuft!"
        Write-Host ""
        Write-Host "📍 API Base:       $API_V3_BASE" -ForegroundColor Cyan
        Write-Host "📖 Documentation: $API_BASE/docs" -ForegroundColor Cyan
        Write-Host "📊 Health Check:  $API_BASE/health" -ForegroundColor Cyan
        Write-Host "📝 Logs:          $LOG_FILE" -ForegroundColor Cyan
        Write-Host ""
        
        return $true
    }
    catch {
        Write-Error-Custom "Fehler beim Starten: $_"
        Pop-Location
        return $false
    }
}

function Get-BackendStatus {
    <#
    .SYNOPSIS
        Zeigt Backend-Status
    #>
    
    Write-Header "VERITAS Backend v3 Status"
    
    $process = Get-BackendProcess
    
    if ($null -eq $process) {
        Write-Host "Status:      " -NoNewline
        Write-Host "❌ STOPPED" -ForegroundColor Red
        Write-Host ""
        return $false
    }
    
    Write-Host "Status:      " -NoNewline
    Write-Host "✅ RUNNING" -ForegroundColor Green
    Write-Host "PID:         $($process.Id)" -ForegroundColor White
    Write-Host "Memory:      $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor White
    Write-Host "CPU Time:    $($process.TotalProcessorTime.ToString('hh\:mm\:ss'))" -ForegroundColor White
    Write-Host "Started:     $($process.StartTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor White
    
    # Teste API-Verbindung
    Write-Host ""
    Write-Host "→ Teste API-Verbindung..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "$API_BASE/health" -Method GET -TimeoutSec 5
        Write-Success "API erreichbar"
        Write-Host "  Version:     $($response.version)" -ForegroundColor White
        Write-Host "  Status:      $($response.status)" -ForegroundColor White
        if ($response.services) {
            Write-Host "  Services:" -ForegroundColor White
            Write-Host "    - UDS3:      $(if($response.services.uds3){'✅'}else{'❌'})" -ForegroundColor White
            Write-Host "    - Pipeline:  $(if($response.services.pipeline){'✅'}else{'❌'})" -ForegroundColor White
            Write-Host "    - Streaming: $(if($response.services.streaming){'✅'}else{'❌'})" -ForegroundColor White
        }
    }
    catch {
        Write-Error-Custom "API nicht erreichbar: $_"
    }
    
    Write-Host ""
    Write-Host "📍 API Base:       $API_V3_BASE" -ForegroundColor Cyan
    Write-Host "📖 Documentation: $API_BASE/docs" -ForegroundColor Cyan
    Write-Host "📝 Logs:          $LOG_FILE" -ForegroundColor Cyan
    Write-Host ""
    
    return $true
}

function Test-Backend {
    <#
    .SYNOPSIS
        Testet Backend-Endpoints
    #>
    
    Write-Header "VERITAS Backend v3 Tests"
    
    $process = Get-BackendProcess
    if ($null -eq $process) {
        Write-Error-Custom "Backend läuft nicht!"
        Write-Info "Starte Backend mit: .\manage_backend_v3.ps1 -Action start"
        return $false
    }
    
    Write-Success "Backend läuft (PID: $($process.Id))"
    Write-Host ""
    
    $tests = @(
        @{ Name = "Root Endpoint"; Url = "$API_BASE/"; Expected = "VERITAS API v3" },
        @{ Name = "Health Check"; Url = "$API_BASE/health"; Expected = "healthy" },
        @{ Name = "API v3 Root"; Url = "$API_V3_BASE/"; Expected = "VERITAS API v3" }
    )
    
    $passed = 0
    $failed = 0
    
    foreach ($test in $tests) {
        Write-Host "→ Teste: $($test.Name)..." -NoNewline
        
        try {
            $response = Invoke-RestMethod -Uri $test.Url -Method GET -TimeoutSec 10
            $responseJson = $response | ConvertTo-Json -Depth 3
            
            if ($responseJson -like "*$($test.Expected)*") {
                Write-Host " ✅" -ForegroundColor Green
                $passed++
            }
            else {
                Write-Host " ⚠️  (Unexpected response)" -ForegroundColor Yellow
                $failed++
            }
        }
        catch {
            Write-Host " ❌" -ForegroundColor Red
            Write-Host "  Error: $_" -ForegroundColor Red
            $failed++
        }
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Ergebnis: $passed/$($tests.Count) Tests bestanden" -ForegroundColor $(if($failed -eq 0){"Green"}else{"Yellow"})
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    return ($failed -eq 0)
}

function Restart-Backend {
    <#
    .SYNOPSIS
        Restart Backend
    #>
    
    Write-Header "VERITAS Backend v3 Neustart"
    
    # Stoppe Backend
    $stopped = Stop-Backend
    
    # Warte kurz
    Start-Sleep -Seconds 2
    
    # Starte Backend
    $started = Start-Backend
    
    if ($started) {
        Write-Success "Backend erfolgreich neu gestartet"
        return $true
    }
    else {
        Write-Error-Custom "Backend-Neustart fehlgeschlagen"
        return $false
    }
}

# =============================================================================
# HAUPTLOGIK
# =============================================================================

# Erstelle data-Verzeichnis falls nicht vorhanden
$dataDir = Join-Path $PROJECT_ROOT "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

# Führe Aktion aus
switch ($Action) {
    "start" {
        $success = Start-Backend
        exit $(if($success){0}else{1})
    }
    "stop" {
        $success = Stop-Backend
        exit $(if($success){0}else{1})
    }
    "restart" {
        $success = Restart-Backend
        exit $(if($success){0}else{1})
    }
    "status" {
        $success = Get-BackendStatus
        exit $(if($success){0}else{1})
    }
    "test" {
        $success = Test-Backend
        exit $(if($success){0}else{1})
    }
}
