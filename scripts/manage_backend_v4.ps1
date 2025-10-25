#!/usr/bin/env pwsh
<#
.SYNOPSIS
    VERITAS Backend v4.0.0 Management Script
    
.DESCRIPTION
    Verwaltet das VERITAS Unified Backend v4.0.0 (Start, Stop, Restart, Status, Test)
    
.PARAMETER Action
    Aktion: start, stop, restart, status, test, info
    
.PARAMETER Wait
    Wartezeit in Sekunden nach dem Start (Standard: 5)
    
.PARAMETER Debug
    Startet Backend mit Debug-Logging
    
.EXAMPLE
    .\manage_backend_v4.ps1 -Action start
    .\manage_backend_v4.ps1 -Action stop
    .\manage_backend_v4.ps1 -Action restart
    .\manage_backend_v4.ps1 -Action status
    .\manage_backend_v4.ps1 -Action test
    .\manage_backend_v4.ps1 -Action info
    .\manage_backend_v4.ps1 -Action start -Debug
#>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "test", "info")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [int]$Wait = 5,
    
    [Parameter(Mandatory=$false)]
    [switch]$DebugMode
)

# =============================================================================
# KONFIGURATION - Backend v4.0.0
# =============================================================================

$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$BACKEND_MODULE = "backend.app:app"  # Unified backend (flat structure)
$PID_FILE = Join-Path $PROJECT_ROOT "data" "backend_v4.pid"
$LOG_FILE = Join-Path $PROJECT_ROOT "logs" "backend_v4.log"
$API_BASE = "http://localhost:5000"

# v4.0.0 Endpoints (flat structure)
$ENDPOINTS = @{
    health = "$API_BASE/api/system/health"
    info = "$API_BASE/api/system/info"
    capabilities = "$API_BASE/api/system/capabilities"
    modes = "$API_BASE/api/system/modes"
    query = "$API_BASE/api/query"
    docs = "$API_BASE/docs"
}

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

function Write-Step {
    param([string]$Text)
    Write-Host "→ $Text" -ForegroundColor Yellow
}

function Get-BackendProcess {
    <#
    .SYNOPSIS
        Findet den Backend v4.0.0 Prozess
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
    
    # Fallback: Suche nach Python-Prozess mit uvicorn + backend.backend
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue
    foreach ($proc in $processes) {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine -like "*backend.app*" -or $cmdLine -like "*uvicorn*backend*") {
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
        Stoppt das Backend v4.0.0
    #>
    
    Write-Header "VERITAS Backend v4.0.0 Stoppen"
    
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
    Write-Step "Stoppe Backend v4.0.0..."
    
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
        
        Write-Success "Backend v4.0.0 gestoppt"
        
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
        Startet das Backend v4.0.0
    #>
    
    Write-Header "VERITAS Backend v4.0.0 Starten"
    
    # Prüfe ob bereits läuft
    $process = Get-BackendProcess
    if ($null -ne $process) {
        Write-Warning-Custom "Backend läuft bereits (PID: $($process.Id))"
        return $false
    }
    
    Write-Info "Starte Backend v4.0.0 (Unified Architecture)..."
    Write-Info "Module: $BACKEND_MODULE"
    Write-Info "API Base: $API_BASE"
    Write-Info "Log: $LOG_FILE"
    Write-Host ""
    
    try {
        # Erstelle Verzeichnisse falls nicht vorhanden
        $logsDir = Split-Path -Parent $LOG_FILE
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
        }
        
        $pidDir = Split-Path -Parent $PID_FILE
        if (-not (Test-Path $pidDir)) {
            New-Item -ItemType Directory -Path $pidDir -Force | Out-Null
        }
        
        # Log-Rotation
        if (Test-Path $LOG_FILE) {
            $backupLog = "$LOG_FILE.old"
            Move-Item -Path $LOG_FILE -Destination $backupLog -Force -ErrorAction SilentlyContinue
        }
        
        # Wechsle ins Projektverzeichnis
        Push-Location $PROJECT_ROOT
        
        # Baue Uvicorn-Befehl
        $logLevel = if ($DebugMode) { "debug" } else { "info" }
        $uvicornCmd = "-m uvicorn $BACKEND_MODULE --host 0.0.0.0 --port 5000 --log-level $logLevel"
        
        Write-Step "Starte Uvicorn..."
        Write-Host "  Command: python $uvicornCmd" -ForegroundColor Gray
        
        # Starte Backend-Prozess
        $processInfo = New-Object System.Diagnostics.ProcessStartInfo
        $processInfo.FileName = "python"
        $processInfo.Arguments = $uvicornCmd
        $processInfo.UseShellExecute = $false
        $processInfo.CreateNoWindow = $true
        $processInfo.RedirectStandardOutput = $true
        $processInfo.RedirectStandardError = $true
        $processInfo.WorkingDirectory = $PROJECT_ROOT
        
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $processInfo
        
        # Event Handler für Output
        $outHandler = {
            if (-not [string]::IsNullOrEmpty($EventArgs.Data)) {
                Add-Content -Path $using:LOG_FILE -Value $EventArgs.Data
            }
        }
        
        $errHandler = {
            if (-not [string]::IsNullOrEmpty($EventArgs.Data)) {
                $errLine = "[ERROR] $($EventArgs.Data)"
                Add-Content -Path $using:LOG_FILE -Value $errLine
            }
        }
        
        Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action $outHandler | Out-Null
        Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action $errHandler | Out-Null
        
        # Starte Prozess
        $started = $process.Start()
        if (-not $started) {
            throw "Prozess konnte nicht gestartet werden"
        }
        
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()
        
        # Speichere PID
        $process.Id | Out-File -FilePath $PID_FILE -Encoding ascii -Force
        
        Pop-Location
        
        Write-Success "Backend v4.0.0 gestartet (PID: $($process.Id))"
        Write-Info "PID-Datei: $PID_FILE"
        Write-Info "Log-Datei: $LOG_FILE"
        
        # Warte auf Start
        Write-Step "Warte $Wait Sekunden auf Initialisierung..."
        Start-Sleep -Seconds $Wait
        
        # Health Check
        Write-Step "Führe Health Check durch..."
        $maxRetries = 10
        $healthy = $false
        
        for ($i = 0; $i -lt $maxRetries; $i++) {
            try {
                $response = Invoke-RestMethod -Uri $ENDPOINTS.health -TimeoutSec 2 -ErrorAction Stop
                
                if ($response.status -eq "healthy") {
                    $healthy = $true
                    Write-Success "Backend v4.0.0 ist healthy!"
                    
                    # Zeige Components
                    if ($response.components) {
                        Write-Host "  Components:" -ForegroundColor Gray
                        foreach ($comp in $response.components.PSObject.Properties) {
                            $status = if ($comp.Value) { "✓" } else { "✗" }
                            $color = if ($comp.Value) { "Green" } else { "Yellow" }
                            Write-Host "    $status $($comp.Name)" -ForegroundColor $color
                        }
                    }
                    
                    break
                }
            }
            catch {
                if ($i -eq ($maxRetries - 1)) {
                    Write-Warning-Custom "Health Check fehlgeschlagen nach $maxRetries Versuchen"
                    Write-Info "Backend läuft möglicherweise trotzdem (prüfe Logs)"
                } else {
                    Start-Sleep -Milliseconds 800
                }
            }
        }
        
        return $healthy
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
        Zeigt Backend v4.0.0 Status
    #>
    
    Write-Header "VERITAS Backend v4.0.0 Status"
    
    # Prozess-Status
    $process = Get-BackendProcess
    
    if ($null -eq $process) {
        Write-Error-Custom "Backend läuft nicht"
        return $false
    }
    
    Write-Success "Backend v4.0.0 läuft"
    Write-Host ""
    Write-Host "Prozess-Info:" -ForegroundColor Cyan
    Write-Host "  • PID:       $($process.Id)" -ForegroundColor White
    Write-Host "  • Name:      $($process.ProcessName)" -ForegroundColor White
    Write-Host "  • CPU:       $($process.CPU.ToString('0.00'))s" -ForegroundColor White
    Write-Host "  • Memory:    $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor White
    Write-Host "  • Threads:   $($process.Threads.Count)" -ForegroundColor White
    Write-Host "  • Start:     $($process.StartTime)" -ForegroundColor White
    
    # API-Status
    Write-Host ""
    Write-Host "API-Status:" -ForegroundColor Cyan
    
    try {
        $health = Invoke-RestMethod -Uri $ENDPOINTS.health -TimeoutSec 2
        
        if ($health.status -eq "healthy") {
            Write-Success "Health: $($health.status)"
        } else {
            Write-Warning-Custom "Health: $($health.status)"
        }
        
        if ($health.components) {
            Write-Host "  Components:" -ForegroundColor White
            foreach ($comp in $health.components.PSObject.Properties) {
                $status = if ($comp.Value) { "✅" } else { "⚠️ " }
                Write-Host "    $status $($comp.Name): $($comp.Value)" -ForegroundColor Gray
            }
        }
        
        if ($health.version) {
            Write-Host "  Version: $($health.version)" -ForegroundColor White
        }
    }
    catch {
        Write-Error-Custom "Health Check fehlgeschlagen: $_"
    }
    
    # Endpoints
    Write-Host ""
    Write-Host "Verfügbare Endpoints:" -ForegroundColor Cyan
    Write-Host "  • Health:        $($ENDPOINTS.health)" -ForegroundColor Gray
    Write-Host "  • Info:          $($ENDPOINTS.info)" -ForegroundColor Gray
    Write-Host "  • Capabilities:  $($ENDPOINTS.capabilities)" -ForegroundColor Gray
    Write-Host "  • Modes:         $($ENDPOINTS.modes)" -ForegroundColor Gray
    Write-Host "  • Query:         $($ENDPOINTS.query)" -ForegroundColor Gray
    Write-Host "  • Docs:          $($ENDPOINTS.docs)" -ForegroundColor Gray
    
    return $true
}

function Test-Backend {
    <#
    .SYNOPSIS
        Testet Backend v4.0.0 mit Beispiel-Queries
    #>
    
    Write-Header "VERITAS Backend v4.0.0 Test"
    
    # Prüfe ob läuft
    $process = Get-BackendProcess
    if ($null -eq $process) {
        Write-Error-Custom "Backend läuft nicht. Starte zuerst mit: -Action start"
        return $false
    }
    
    Write-Success "Backend läuft (PID: $($process.Id))"
    Write-Host ""
    
    # Test 1: Health
    Write-Step "Test 1: Health Check"
    try {
        $health = Invoke-RestMethod -Uri $ENDPOINTS.health -TimeoutSec 5
        Write-Success "Health: $($health.status)"
    } catch {
        Write-Error-Custom "Health Check fehlgeschlagen: $_"
        return $false
    }
    
    # Test 2: System Info
    Write-Step "Test 2: System Info"
    try {
        $info = Invoke-RestMethod -Uri $ENDPOINTS.info -TimeoutSec 5
        Write-Success "Backend Version: $($info.version)"
        Write-Host "  Architecture: $($info.architecture)" -ForegroundColor Gray
    } catch {
        Write-Error-Custom "System Info fehlgeschlagen: $_"
    }
    
    # Test 3: Capabilities
    Write-Step "Test 3: Capabilities"
    try {
        $caps = Invoke-RestMethod -Uri $ENDPOINTS.capabilities -TimeoutSec 5
        Write-Success "Features: $($caps.features.Count)"
        foreach ($feature in $caps.features) {
            Write-Host "  • $feature" -ForegroundColor Gray
        }
    } catch {
        Write-Error-Custom "Capabilities fehlgeschlagen: $_"
    }
    
    # Test 4: Modes
    Write-Step "Test 4: Query Modes"
    try {
        $modes = Invoke-RestMethod -Uri $ENDPOINTS.modes -TimeoutSec 5
        Write-Success "Modi: $($modes.modes.Count)"
        foreach ($mode in $modes.modes) {
            Write-Host "  • $($mode.key): $($mode.name)" -ForegroundColor Gray
        }
    } catch {
        Write-Error-Custom "Modes fehlgeschlagen: $_"
    }
    
    # Test 5: Simple Query
    Write-Step "Test 5: Simple Query (Mock)"
    try {
        $body = @{
            query = "Was ist VERITAS?"
            mode = "ask"
            model = "llama3.1"
        } | ConvertTo-Json
        
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri $ENDPOINTS.query -Method Post -Body $body -Headers $headers -TimeoutSec 10
        
        if ($response.content) {
            Write-Success "Query erfolgreich"
            Write-Host "  Content: $($response.content.Substring(0, [Math]::Min(100, $response.content.Length)))..." -ForegroundColor Gray
            Write-Host "  Sources: $($response.sources.Count)" -ForegroundColor Gray
            Write-Host "  Mode: $($response.metadata.mode)" -ForegroundColor Gray
            Write-Host "  Model: $($response.metadata.model)" -ForegroundColor Gray
        }
    } catch {
        Write-Warning-Custom "Query fehlgeschlagen (erwartet wenn UDS3 nicht verfügbar): $_"
    }
    
    Write-Host ""
    Write-Success "Tests abgeschlossen!"
    
    return $true
}

function Get-BackendInfo {
    <#
    .SYNOPSIS
        Zeigt detaillierte Backend-Informationen
    #>
    
    Write-Header "VERITAS Backend v4.0.0 Informationen"
    
    try {
        $info = Invoke-RestMethod -Uri $ENDPOINTS.info -TimeoutSec 5
        
        Write-Host "System:" -ForegroundColor Cyan
        Write-Host "  • Version:      $($info.version)" -ForegroundColor White
        Write-Host "  • Architecture: $($info.architecture)" -ForegroundColor White
        Write-Host "  • Description:  $($info.description)" -ForegroundColor White
        
        if ($info.components) {
            Write-Host ""
            Write-Host "Components:" -ForegroundColor Cyan
            foreach ($comp in $info.components.PSObject.Properties) {
                Write-Host "  • $($comp.Name): $($comp.Value)" -ForegroundColor White
            }
        }
        
        if ($info.features) {
            Write-Host ""
            Write-Host "Features:" -ForegroundColor Cyan
            foreach ($feature in $info.features) {
                Write-Host "  • $feature" -ForegroundColor White
            }
        }
        
        # Capabilities
        $caps = Invoke-RestMethod -Uri $ENDPOINTS.capabilities -TimeoutSec 5
        Write-Host ""
        Write-Host "Capabilities:" -ForegroundColor Cyan
        Write-Host "  • Query Modes:   $($caps.query_modes.Count)" -ForegroundColor White
        Write-Host "  • Agent Types:   $($caps.agent_types.Count)" -ForegroundColor White
        Write-Host "  • Vector DBs:    $($caps.vector_databases -join ', ')" -ForegroundColor White
        Write-Host "  • Embeddings:    $($caps.embedding_models -join ', ')" -ForegroundColor White
        
    } catch {
        Write-Error-Custom "Info konnte nicht abgerufen werden: $_"
        return $false
    }
    
    return $true
}

# =============================================================================
# HAUPTLOGIK
# =============================================================================

switch ($Action.ToLower()) {
    "start" {
        Start-Backend
    }
    
    "stop" {
        Stop-Backend
    }
    
    "restart" {
        Write-Header "VERITAS Backend v4.0.0 Restart"
        
        $stopped = Stop-Backend
        if ($stopped -or -not (Get-BackendProcess)) {
            Start-Sleep -Seconds 2
            Start-Backend
        }
    }
    
    "status" {
        Get-BackendStatus
    }
    
    "test" {
        Test-Backend
    }
    
    "info" {
        Get-BackendInfo
    }
}

Write-Host ""
