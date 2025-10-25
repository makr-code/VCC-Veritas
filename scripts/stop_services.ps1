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

# Konfiguration (gezielt)
$RootDir = Split-Path -Parent $PSScriptRoot
$BackendPidFile = Join-Path $RootDir "data\.veritas_backend.pid"
$BackendPort = 5000

# Funktion: Stoppe gezielt Backend via PID-Datei
function Stop-VeritasBackend {
    if (Test-Path $BackendPidFile) {
        try {
            $backendPid = Get-Content $BackendPidFile -ErrorAction Stop
            if ($backendPid) {
                Write-Step "Stoppe VERITAS Backend (PID: $backendPid)..."
                $proc = Get-Process -Id $backendPid -ErrorAction SilentlyContinue
                if ($proc) {
                    Stop-Process -Id $backendPid -Force
                    Write-Success "Backend-Prozess gestoppt"
                } else {
                    Write-Info "Kein Prozess mit PID $backendPid gefunden"
                }
            }
            Remove-Item $BackendPidFile -Force -ErrorAction SilentlyContinue
            Write-Info "PID-Datei gelöscht"
        } catch {
            Write-Error "Fehler beim Beenden: $_"
        }
    } else {
        Write-Info "Keine PID-Datei gefunden ($BackendPidFile)"
    }
}

# Ausführung (nur Backend gezielt stoppen)
if (-not $FrontendOnly) {
    Stop-VeritasBackend
}

# Finale Überprüfung (nur Health) - Backend v4.0.0
Write-Step "Finale Überprüfung..."
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:$BackendPort/api/system/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    if ($resp.StatusCode -eq 200) {
        Write-Warning "Backend v4.0.0 antwortet noch (Port $BackendPort)"
    } else {
        Write-Success "Backend v4.0.0 gestoppt"
    }
} catch {
    Write-Success "Backend v4.0.0 gestoppt"
}

Write-Host "`n✅ Stopp-Vorgang abgeschlossen`n" -ForegroundColor Green
