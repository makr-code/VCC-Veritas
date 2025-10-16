# VERITAS Service Stopper
# Stoppt Backend und Frontend Services

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$Force
)

function Write-Header($text) {
    Write-Host "`n========================================" -ForegroundColor Red
    Write-Host " $text" -ForegroundColor Red
    Write-Host "========================================`n" -ForegroundColor Red
}

function Write-Step($text) {
    Write-Host "→ $text" -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "  ✅ $text" -ForegroundColor Green
}

function Write-Info($text) {
    Write-Host "  ℹ️  $text" -ForegroundColor Blue
}

function Write-Warning($text) {
    Write-Host "  ⚠️  $text" -ForegroundColor Yellow
}

function Write-Error($text) {
    Write-Host "  ❌ $text" -ForegroundColor Red
}

Write-Header "VERITAS Service Stopper"

# Konfiguration
$RootDir = Split-Path -Parent $PSScriptRoot
$BackendPort = 5000
$PidFile = Join-Path $RootDir "data\.veritas_pids.txt"

# Funktion: Stoppe Prozess über PID
function Stop-ProcessByPid {
    param(
        [int]$ProcessId,
        [string]$ServiceName
    )
    
    try {
        $process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Step "Stoppe $ServiceName (PID: $ProcessId)..."
            Stop-Process -Id $ProcessId -Force
            Start-Sleep -Seconds 1
            
            # Verifiziere
            $stillRunning = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
            if ($stillRunning) {
                Write-Warning "$ServiceName läuft noch, erzwinge Stop..."
                Stop-Process -Id $ProcessId -Force
            }
            else {
                Write-Success "$ServiceName gestoppt"
            }
            return $true
        }
        else {
            Write-Info "$ServiceName-Prozess (PID: $ProcessId) läuft nicht mehr"
            return $false
        }
    }
    catch {
        Write-Error "Fehler beim Stoppen von ${ServiceName}: $_"
        return $false
    }
}

# Funktion: Stoppe Backend über Port
function Stop-BackendByPort {
    Write-Step "Suche Backend über Port $BackendPort..."
    
    try {
        $connection = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
        if ($connection) {
            $pid = $connection.OwningProcess
            Write-Info "Backend gefunden (PID: $pid)"
            Stop-ProcessByPid -ProcessId $pid -ServiceName "Backend"
            return $true
        }
        else {
            Write-Info "Kein Prozess auf Port $BackendPort gefunden"
            return $false
        }
    }
    catch {
        Write-Warning "Fehler beim Suchen über Port: $_"
        return $false
    }
}

# Funktion: Stoppe Python-Prozesse
function Stop-PythonProcesses {
    param([string]$ScriptPattern)
    
    Write-Step "Suche Python-Prozesse mit '$ScriptPattern'..."
    
    $found = $false
    Get-Process -Name "python" -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
            if ($cmdLine -like "*$ScriptPattern*") {
                Write-Info "Gefunden: $cmdLine"
                Stop-Process -Id $_.Id -Force
                Write-Success "Prozess gestoppt (PID: $($_.Id))"
                $found = $true
            }
        }
        catch {
            # Ignoriere Fehler (Prozess könnte bereits beendet sein)
        }
    }
    
    return $found
}

# Funktion: Stoppe PowerShell Jobs
function Stop-PowerShellJobs {
    Write-Step "Prüfe PowerShell Background Jobs..."
    
    $jobs = Get-Job -ErrorAction SilentlyContinue
    if ($jobs) {
        $jobs | ForEach-Object {
            Write-Info "Stoppe Job: $($_.Name) (ID: $($_.Id))"
            Stop-Job -Id $_.Id
            Remove-Job -Id $_.Id -Force
        }
        Write-Success "Alle Background Jobs gestoppt"
        return $true
    }
    else {
        Write-Info "Keine Background Jobs gefunden"
        return $false
    }
}

# Hauptlogik
$stoppedAny = $false

# Methode 1: Stoppe über gespeicherte PIDs
if (Test-Path $PidFile) {
    Write-Step "Lade gespeicherte Process IDs..."
    
    try {
        $pidInfo = Get-Content $PidFile | ConvertFrom-Json
        Write-Info "Services gestartet am: $($pidInfo.StartTime)"
        
        if (-not $FrontendOnly -and $pidInfo.Backend) {
            $stoppedAny = Stop-ProcessByPid -ProcessId $pidInfo.Backend -ServiceName "Backend" -or $stoppedAny
        }
        
        if (-not $BackendOnly -and $pidInfo.Frontend) {
            $stoppedAny = Stop-ProcessByPid -ProcessId $pidInfo.Frontend -ServiceName "Frontend" -or $stoppedAny
        }
        
        # Lösche PID-Datei
        Remove-Item $PidFile -Force
        Write-Info "PID-Datei gelöscht"
    }
    catch {
        Write-Warning "Fehler beim Laden der PID-Datei: $_"
    }
}

# Methode 2: Stoppe Backend über Port
if (-not $FrontendOnly) {
    $stoppedAny = Stop-BackendByPort -or $stoppedAny
}

# Methode 3: Stoppe über Skript-Namen
if (-not $FrontendOnly -or $Force) {
    $stoppedAny = Stop-PythonProcesses -ScriptPattern "start_backend.py" -or $stoppedAny
    $stoppedAny = Stop-PythonProcesses -ScriptPattern "veritas_api_backend" -or $stoppedAny
}

if (-not $BackendOnly -or $Force) {
    $stoppedAny = Stop-PythonProcesses -ScriptPattern "start_frontend.py" -or $stoppedAny
    $stoppedAny = Stop-PythonProcesses -ScriptPattern "veritas_app.py" -or $stoppedAny
}

# Methode 4: Stoppe PowerShell Jobs
$stoppedAny = Stop-PowerShellJobs -or $stoppedAny

# Zusammenfassung
Write-Host ""
if ($stoppedAny) {
    Write-Header "✅ Services gestoppt"
}
else {
    Write-Header "ℹ️  Keine laufenden Services gefunden"
}

# Finale Überprüfung
Write-Step "Finale Überprüfung..."

$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://localhost:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
    $backendRunning = $response.StatusCode -eq 200
}
catch {
    $backendRunning = $false
}

if ($backendRunning) {
    Write-Warning "Backend läuft NOCH auf Port $BackendPort!"
    
    if ($Force) {
        Write-Step "Force-Modus: Erzwinge Backend-Stop..."
        Stop-BackendByPort
    }
    else {
        Write-Info "Verwenden Sie -Force Parameter zum Erzwingen"
    }
}
else {
    Write-Success "Backend gestoppt"
}

$pythonProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue
if ($pythonProcesses) {
    Write-Warning "Es laufen noch $($pythonProcesses.Count) Python-Prozesse"
    
    if ($Force) {
        Write-Step "Force-Modus: Stoppe alle Python-Prozesse..."
        $pythonProcesses | ForEach-Object {
            Stop-Process -Id $_.Id -Force
        }
        Write-Success "Alle Python-Prozesse gestoppt"
    }
    else {
        Write-Info "Verwenden Sie -Force zum Stoppen aller Python-Prozesse"
    }
}

Write-Host ""
Write-Host "✅ Stopp-Vorgang abgeschlossen`n" -ForegroundColor Green
