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
    Write-Host "→ $text" -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "  ✅ $text" -ForegroundColor Green
}

function Write-Info($text) {
    Write-Host "  ℹ️  $text" -ForegroundColor Blue
}

Write-Header "VERITAS Service Starter"

# Backend starten
if (-not $FrontendOnly) {
    Write-Step "Starte Backend (Port 5000)..."
    
    $backendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        # Nutze uvicorn statt direktem Python-Call
        python -m uvicorn backend.api.veritas_api_backend:app --host 0.0.0.0 --port 5000
    }
    
    Write-Success "Backend gestartet (Job ID: $($backendJob.Id))"
    Write-Info "Warte 5 Sekunden auf Backend-Start..."
    Start-Sleep -Seconds 5
    
    # Health Check
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/health" -TimeoutSec 5
        Write-Success "Backend Health Check: OK"
        Write-Host "    Response: $($response | ConvertTo-Json -Compress)" -ForegroundColor Gray
    } catch {
        Write-Host "  ⚠️  Backend Health Check fehlgeschlagen (startet möglicherweise noch)" -ForegroundColor Yellow
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
    Write-Host "Backend:  " -NoNewline -ForegroundColor White
    Write-Host "http://127.0.0.1:5000" -ForegroundColor Cyan
    Write-Host "  • Health:    http://127.0.0.1:5000/health" -ForegroundColor Gray
    Write-Host "  • Docs:      http://127.0.0.1:5000/docs" -ForegroundColor Gray
    Write-Host "  • Job ID:    $($backendJob.Id)" -ForegroundColor Gray
}

if (-not $BackendOnly) {
    Write-Host "`nFrontend: " -NoNewline -ForegroundColor White
    Write-Host "GUI (Tkinter)" -ForegroundColor Cyan
    Write-Host "  • Job ID:    $($frontendJob.Id)" -ForegroundColor Gray
}

# Befehle anzeigen
Write-Host "`n📋 Nützliche Befehle:" -ForegroundColor Cyan
Write-Host "  • Logs anzeigen:    Get-Job | Receive-Job -Keep" -ForegroundColor White
Write-Host "  • Services stoppen: Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor White
Write-Host "  • Status prüfen:    Get-Job" -ForegroundColor White

Write-Host "`n✅ Services laufen im Hintergrund!`n" -ForegroundColor Green
