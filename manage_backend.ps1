# VERITAS Backend Management Script
# Verwaltung des FastAPI Backend-Servers

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('start', 'stop', 'restart', 'status')]
    [string]$Action
)

# Konfiguration
$BackendScript = "start_backend.py"
$BackendPort = 5000
$ProcessName = "python"
$LogFile = "data\veritas_backend.log"

# Farbige Ausgaben
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# Prüfe ob Backend läuft
function Test-BackendRunning {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# Hole Backend-Prozess
function Get-BackendProcess {
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*$BackendScript*"
    }
    
    # Fallback: Prüfe über Port
    if (-not $processes) {
        $connection = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            $processes = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        }
    }
    
    return $processes
}

# Starte Backend
function Start-Backend {
    Write-Info "Prüfe Backend-Status..."
    
    if (Test-BackendRunning) {
        Write-Warning "Backend läuft bereits auf Port $BackendPort"
        Show-BackendStatus
        return
    }
    
    Write-Info "Starte Backend-Server..."
    
    # Prüfe ob start_backend.py existiert
    if (-not (Test-Path $BackendScript)) {
        Write-Error "Script '$BackendScript' nicht gefunden!"
        return
    }
    
    # Starte Backend als Background-Prozess
    $process = Start-Process -FilePath "python" -ArgumentList $BackendScript -NoNewWindow -PassThru -RedirectStandardOutput $LogFile
    
    # Warte auf Start (max 10 Sekunden)
    Write-Info "Warte auf Backend-Start..."
    $timeout = 10
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 1
        $elapsed++
        
        if (Test-BackendRunning) {
            Write-Success "Backend erfolgreich gestartet!"
            Write-Info "PID: $($process.Id)"
            Write-Info "Port: $BackendPort"
            Write-Info "Log: $LogFile"
            Show-BackendStatus
            return
        }
        
        Write-Host "." -NoNewline
    }
    
    Write-Host ""
    Write-Error "Backend-Start fehlgeschlagen (Timeout nach ${timeout}s)"
    Write-Info "Prüfe Log-Datei: $LogFile"
}

# Stoppe Backend
function Stop-Backend {
    Write-Info "Suche Backend-Prozess..."
    
    $processes = Get-BackendProcess
    
    if (-not $processes) {
        Write-Warning "Kein Backend-Prozess gefunden"
        return
    }
    
    foreach ($proc in $processes) {
        Write-Info "Stoppe Prozess PID: $($proc.Id)"
        try {
            Stop-Process -Id $proc.Id -Force
            Write-Success "Backend-Prozess gestoppt"
        }
        catch {
            Write-Error "Fehler beim Stoppen: $_"
        }
    }
    
    # Warte und verifiziere
    Start-Sleep -Seconds 2
    
    if (Test-BackendRunning) {
        Write-Error "Backend läuft noch! Erzwinge Stopp..."
        # Erzwinge über Port
        $connection = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            Stop-Process -Id $connection.OwningProcess -Force
        }
    }
    else {
        Write-Success "Backend vollständig gestoppt"
    }
}

# Zeige Backend-Status
function Show-BackendStatus {
    Write-Info "Backend-Status:"
    Write-Host ("=" * 50)
    
    $isRunning = Test-BackendRunning
    
    if ($isRunning) {
        Write-Success "Status: RUNNING"
        
        $processes = Get-BackendProcess
        if ($processes) {
            foreach ($proc in $processes) {
                Write-Host "  PID:        $($proc.Id)" -ForegroundColor White
                Write-Host "  Name:       $($proc.ProcessName)" -ForegroundColor White
                Write-Host "  CPU:        $([math]::Round($proc.CPU, 2))s" -ForegroundColor White
                Write-Host "  Memory:     $([math]::Round($proc.WorkingSet64 / 1MB, 2)) MB" -ForegroundColor White
                Write-Host "  Started:    $($proc.StartTime)" -ForegroundColor White
            }
        }
        
        Write-Host "  Port:       $BackendPort" -ForegroundColor White
        Write-Host "  URL:        http://localhost:$BackendPort" -ForegroundColor White
        Write-Host "  Health:     http://localhost:$BackendPort/health" -ForegroundColor White
        Write-Host "  API Docs:   http://localhost:$BackendPort/docs" -ForegroundColor White
        
        # Teste Health Endpoint
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:$BackendPort/health" -TimeoutSec 2
            Write-Success "Health Check: OK"
            if ($health.status) {
                Write-Host "  Status:     $($health.status)" -ForegroundColor White
            }
        }
        catch {
            Write-Warning "Health Check: FAILED"
        }
    }
    else {
        Write-Error "Status: STOPPED"
        
        # Prüfe ob Port blockiert ist
        $connection = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
        if ($connection) {
            Write-Warning "Port $BackendPort wird von Prozess $($connection.OwningProcess) blockiert"
        }
    }
    
    Write-Host ("=" * 50)
}

# Starte Backend neu
function Restart-Backend {
    Write-Info "Starte Backend neu..."
    Stop-Backend
    Start-Sleep -Seconds 2
    Start-Backend
}

# Hauptlogik
switch ($Action) {
    'start' {
        Start-Backend
    }
    'stop' {
        Stop-Backend
    }
    'restart' {
        Restart-Backend
    }
    'status' {
        Show-BackendStatus
    }
}
