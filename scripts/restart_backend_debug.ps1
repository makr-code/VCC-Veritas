# VERITAS Backend Debug Restart Script
# Stoppt Backend sauber und startet mit Debug-Logs neu

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🔄 VERITAS Backend v4.0.0 - Debug Restart" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan

# 1. Finde Backend-Prozess
Write-Host "`n🔍 Suche Backend-Prozess auf Port 5000..." -ForegroundColor Yellow

$backendPort = netstat -ano | findstr ":5000" | findstr "LISTENING"
if ($backendPort) {
    $backendPid = ($backendPort -split '\s+')[-1]
    Write-Host "✓ Backend gefunden auf PID: $backendPid" -ForegroundColor Green
    
    # 2. Stoppe Backend
    Write-Host "⏹️ Stoppe Backend..." -ForegroundColor Yellow
    try {
        Stop-Process -Id $backendPid -Force
        Start-Sleep -Seconds 2
        Write-Host "✓ Backend gestoppt" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Fehler beim Stoppen: $_" -ForegroundColor Red
    }
} else {
    Write-Host "ℹ️ Kein Backend-Prozess gefunden" -ForegroundColor Yellow
}

# 3. Lösche __pycache__ für sauberen Neustart
Write-Host "`n🧹 Lösche Cache-Dateien..." -ForegroundColor Yellow
Get-ChildItem -Path "backend" -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
Write-Host "✓ Cache gelöscht" -ForegroundColor Green

# 4. Starte Backend v4.0.0 im Debug-Modus
Write-Host "`n🚀 Starte Backend v4.0.0 im Debug-Modus..." -ForegroundColor Yellow
Write-Host "📝 Logs: logs/backend_v4.log" -ForegroundColor Cyan
Write-Host "🌐 API: http://localhost:5000" -ForegroundColor Cyan
Write-Host "📚 Docs: http://localhost:5000/docs" -ForegroundColor Cyan
Write-Host "🏥 Health: http://localhost:5000/api/system/health" -ForegroundColor Cyan
Write-Host "⚠️ WICHTIG: Logs erscheinen in diesem Fenster!" -ForegroundColor Yellow
Write-Host "`n" + ("─" * 80) + "`n" -ForegroundColor DarkGray

# Starte Backend v4.0.0 mit Uvicorn direkt
& python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000 --log-level debug --reload

# Falls Fehler
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Backend konnte nicht gestartet werden (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
    Read-Host "Drücke Enter zum Beenden"
}
