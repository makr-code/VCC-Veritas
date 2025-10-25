# Quick Test - VERITAS Modern UI
# Startet Backend + Frontend zum schnellen Testen

Write-Host "`n🚀 VERITAS Modern UI - Quick Test`n" -ForegroundColor Cyan

# 1. Backend starten
Write-Host "→ Starte Backend..." -ForegroundColor Yellow
cd C:\VCC\veritas

$backendJob = Start-Job -ScriptBlock {
    cd C:\VCC\veritas
    python -m uvicorn backend.api.veritas_api_backend:app --host 0.0.0.0 --port 5000
}

Write-Host "  ✅ Backend gestartet (Job ID: $($backendJob.Id))" -ForegroundColor Green

# 2. Warte auf Backend Health
Write-Host "→ Warte auf Backend Health Check..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

for ($i = 0; $i -lt 10; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:5000/health" -TimeoutSec 2 -ErrorAction Stop
        Write-Host "  ✅ Backend bereit!" -ForegroundColor Green
        break
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

# 3. Frontend starten
Write-Host "→ Starte Frontend..." -ForegroundColor Yellow
python frontend\veritas_app.py

# Cleanup
Write-Host "`n→ Stoppe Backend..." -ForegroundColor Yellow
Stop-Job $backendJob
Remove-Job $backendJob
Write-Host "  ✅ Fertig!`n" -ForegroundColor Green
