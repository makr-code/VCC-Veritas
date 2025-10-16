# VERITAS Backend Debug Restart Script
# Stoppt Backend sauber und startet mit Debug-Logs neu

Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "🔄 VERITAS Backend - Debug Restart" -ForegroundColor Cyan
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

# 4. Starte Backend im Debug-Modus
Write-Host "`n🚀 Starte Backend im Debug-Modus..." -ForegroundColor Yellow
Write-Host "📝 Logs: data/backend_debug.log" -ForegroundColor Cyan
Write-Host "🌐 API: http://localhost:5000" -ForegroundColor Cyan
Write-Host "⚠️ WICHTIG: Logs erscheinen in diesem Fenster!" -ForegroundColor Yellow
Write-Host "`n" + ("─" * 80) + "`n" -ForegroundColor DarkGray

# Starte Python direkt (nicht im Hintergrund)
& python start_backend_debug.py

# Falls Fehler
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Backend konnte nicht gestartet werden (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
    Read-Host "Drücke Enter zum Beenden"
}
