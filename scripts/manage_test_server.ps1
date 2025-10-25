# Immissionsschutz Test-Server Management Script
# Verwaltet eigenständigen FastAPI Server (Port 5001)

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("start", "stop", "restart", "status", "test")]
    [string]$Action = "status"
)

# Konfiguration
$ServerName = "Immissionsschutz Test-Server"
$ServerScript = "data\test_databases\immissionsschutz_test_server.py"
$ServerPort = 5001
$PidFile = "data\test_databases\immissionsschutz_server.pid"
$LogFile = "data\test_databases\immissionsschutz_server.log"

# Farben
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error-Custom { Write-Host $args -ForegroundColor Red }

# Banner
function Show-Banner {
    Write-Host ""
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host "  $ServerName Management" -ForegroundColor Cyan
    Write-Host "=" * 70 -ForegroundColor Cyan
    Write-Host ""
}

# PID Funktionen
function Get-ServerPid {
    if (Test-Path $PidFile) {
        return Get-Content $PidFile
    }
    return $null
}

function Set-ServerPid {
    param($Pid)
    $Pid | Out-File -FilePath $PidFile -Encoding utf8
}

function Remove-ServerPid {
    if (Test-Path $PidFile) {
        Remove-Item $PidFile -Force
    }
}

# Server-Prozess finden
function Find-ServerProcess {
    $processes = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*immissionsschutz_test_server.py*"
    }
    
    if ($processes) {
        return $processes[0]
    }
    
    # Alternative: Port prüfen
    $connections = Get-NetTCPConnection -LocalPort $ServerPort -ErrorAction SilentlyContinue
    if ($connections) {
        $pid = $connections[0].OwningProcess
        return Get-Process -Id $pid -ErrorAction SilentlyContinue
    }
    
    return $null
}

# Health Check
function Test-ServerHealth {
    param([int]$MaxRetries = 5)
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/health" -TimeoutSec 2
            if ($response.status -eq "healthy") {
                return $true
            }
        }
        catch {
            if ($i -lt $MaxRetries) {
                Write-Info "  Warte auf Server... ($i/$MaxRetries)"
                Start-Sleep -Seconds 2
            }
        }
    }
    return $false
}

# Start Server
function Start-Server {
    Show-Banner
    Write-Info "🚀 Starte $ServerName..."
    Write-Host ""
    
    # Prüfe ob bereits läuft
    $existingProcess = Find-ServerProcess
    if ($existingProcess) {
        Write-Warning "⚠️  Server läuft bereits (PID: $($existingProcess.Id))"
        return
    }
    
    # Prüfe ob Script existiert
    if (-not (Test-Path $ServerScript)) {
        Write-Error-Custom "❌ Server-Script nicht gefunden: $ServerScript"
        return
    }
    
    # Starte im Hintergrund
    Write-Info "📦 Starte Python-Prozess..."
    
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = "python"
    $startInfo.Arguments = $ServerScript
    $startInfo.UseShellExecute = $false
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $startInfo
    
    # Log-Handler
    $outHandler = {
        if (-not [string]::IsNullOrWhiteSpace($EventArgs.Data)) {
            Add-Content -Path $LogFile -Value "[OUT] $($EventArgs.Data)"
        }
    }
    $errHandler = {
        if (-not [string]::IsNullOrWhiteSpace($EventArgs.Data)) {
            Add-Content -Path $LogFile -Value "[ERR] $($EventArgs.Data)"
        }
    }
    
    Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action $outHandler | Out-Null
    Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action $errHandler | Out-Null
    
    $success = $process.Start()
    
    if ($success) {
        $process.BeginOutputReadLine()
        $process.BeginErrorReadLine()
        
        Set-ServerPid -Pid $process.Id
        
        Write-Success "✅ Prozess gestartet (PID: $($process.Id))"
        Write-Info "📝 Log-Datei: $LogFile"
        Write-Host ""
        
        Write-Info "🔍 Warte auf Server-Bereitschaft..."
        Start-Sleep -Seconds 3
        
        if (Test-ServerHealth) {
            Write-Host ""
            Write-Success "="*70
            Write-Success "✅ $ServerName erfolgreich gestartet!"
            Write-Success "="*70
            Write-Info "📍 API Base: http://localhost:$ServerPort"
            Write-Info "📖 Docs: http://localhost:$ServerPort/docs"
            Write-Info "💓 Health: http://localhost:$ServerPort/health"
            Write-Info "🆔 PID: $($process.Id)"
            Write-Success "="*70
        }
        else {
            Write-Warning "⚠️  Server gestartet, aber Health-Check fehlgeschlagen"
            Write-Info "Prüfe Log-Datei: $LogFile"
        }
    }
    else {
        Write-Error-Custom "❌ Fehler beim Starten des Servers"
    }
    
    Write-Host ""
}

# Stop Server
function Stop-Server {
    Show-Banner
    Write-Info "🛑 Stoppe $ServerName..."
    Write-Host ""
    
    $process = Find-ServerProcess
    
    if (-not $process) {
        Write-Warning "⚠️  Server läuft nicht"
        Remove-ServerPid
        return
    }
    
    Write-Info "🔍 Gefundener Prozess: PID $($process.Id)"
    Write-Info "📋 Versuche graceful shutdown..."
    
    try {
        $process.CloseMainWindow() | Out-Null
        Start-Sleep -Seconds 2
        
        if (-not $process.HasExited) {
            Write-Warning "⚠️  Graceful shutdown fehlgeschlagen, erzwinge Beendigung..."
            $process.Kill()
            Start-Sleep -Seconds 1
        }
        
        Write-Success "✅ Server erfolgreich gestoppt"
    }
    catch {
        Write-Warning "⚠️  Fehler beim Stoppen: $_"
        Write-Info "Versuche Force-Kill..."
        
        try {
            Stop-Process -Id $process.Id -Force
            Write-Success "✅ Server erzwungen gestoppt"
        }
        catch {
            Write-Error-Custom "❌ Konnte Prozess nicht stoppen: $_"
        }
    }
    
    Remove-ServerPid
    Write-Host ""
}

# Restart Server
function Restart-Server {
    Show-Banner
    Write-Info "🔄 Starte $ServerName neu..."
    Write-Host ""
    
    Stop-Server
    Start-Sleep -Seconds 2
    Start-Server
}

# Status
function Get-ServerStatus {
    Show-Banner
    Write-Info "📊 Server Status"
    Write-Host ""
    
    $process = Find-ServerProcess
    
    if ($process) {
        Write-Success "✅ Server läuft"
        Write-Host ""
        Write-Info "Prozess-Details:"
        Write-Host "  PID:              $($process.Id)"
        Write-Host "  Name:             $($process.ProcessName)"
        Write-Host "  CPU:              $([math]::Round($process.CPU, 2))s"
        Write-Host "  Memory:           $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB"
        Write-Host "  Start Time:       $($process.StartTime)"
        
        $uptime = (Get-Date) - $process.StartTime
        Write-Host "  Uptime:           $($uptime.Days)d $($uptime.Hours)h $($uptime.Minutes)m"
        
        Write-Host ""
        Write-Info "🔍 Health-Check..."
        
        if (Test-ServerHealth -MaxRetries 1) {
            try {
                $health = Invoke-RestMethod -Uri "http://localhost:$ServerPort/health" -TimeoutSec 2
                Write-Success "✅ Server healthy"
                Write-Host ""
                Write-Info "Datenbank-Status:"
                foreach ($db in $health.databases.PSObject.Properties) {
                    $status = if ($db.Value -eq "ok") { "✅" } else { "❌" }
                    Write-Host "  $status $($db.Name): $($db.Value)"
                }
                
                # Statistik abrufen
                Write-Host ""
                Write-Info "📊 Statistik:"
                try {
                    $stats = Invoke-RestMethod -Uri "http://localhost:$ServerPort/statistik/overview" -TimeoutSec 2
                    Write-Host "  Verfahren:        $($stats.statistics.verfahren.total) (Genehmigt: $($stats.statistics.verfahren.genehmigt))"
                    Write-Host "  Messungen:        $($stats.statistics.messungen.total) (Überschreitungen: $($stats.statistics.messungen.ueberschreitungen))"
                    Write-Host "  Überwachungen:    $($stats.statistics.ueberwachung.total) (Mit Mängeln: $($stats.statistics.ueberwachung.mit_maengeln))"
                    Write-Host "  Mängel:           $($stats.statistics.maengel.total) (Offen: $($stats.statistics.maengel.offen), Kritisch: $($stats.statistics.maengel.kritisch))"
                }
                catch {
                    Write-Warning "  ⚠️  Konnte Statistik nicht abrufen"
                }
            }
            catch {
                Write-Warning "⚠️  Health-Check fehlgeschlagen: $_"
            }
        }
        else {
            Write-Warning "⚠️  Server läuft, aber antwortet nicht"
        }
        
        Write-Host ""
        Write-Info "Endpoints:"
        Write-Host "  📍 Base:          http://localhost:$ServerPort"
        Write-Host "  📖 Docs:          http://localhost:$ServerPort/docs"
        Write-Host "  💓 Health:        http://localhost:$ServerPort/health"
        Write-Host "  📊 Statistik:     http://localhost:$ServerPort/statistik/overview"
    }
    else {
        Write-Warning "⚠️  Server läuft nicht"
        
        # Prüfe PID-Datei
        $pidFromFile = Get-ServerPid
        if ($pidFromFile) {
            Write-Warning "⚠️  Verwaiste PID-Datei gefunden (PID: $pidFromFile)"
            Write-Info "Bereinige PID-Datei..."
            Remove-ServerPid
        }
    }
    
    Write-Host ""
}

# Test
function Test-Server {
    Show-Banner
    Write-Info "🧪 Teste $ServerName"
    Write-Host ""
    
    $process = Find-ServerProcess
    if (-not $process) {
        Write-Error-Custom "❌ Server läuft nicht. Starte mit: -Action start"
        return
    }
    
    $testResults = @()
    
    # Test 1: Health
    Write-Info "Test 1/6: Health Check..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/health" -TimeoutSec 5
        if ($response.status -eq "healthy") {
            Write-Success "  ✅ Health Check erfolgreich"
            $testResults += $true
        }
        else {
            Write-Error-Custom "  ❌ Server nicht healthy: $($response.status)"
            $testResults += $false
        }
    }
    catch {
        Write-Error-Custom "  ❌ Fehler: $_"
        $testResults += $false
    }
    
    # Test 2: Datenbanken Liste
    Write-Info "Test 2/6: Datenbanken Liste..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/databases" -TimeoutSec 5
        if ($response.Count -eq 3) {
            Write-Success "  ✅ 3 Datenbanken gefunden"
            $testResults += $true
        }
        else {
            Write-Error-Custom "  ❌ Erwartete 3 Datenbanken, gefunden: $($response.Count)"
            $testResults += $false
        }
    }
    catch {
        Write-Error-Custom "  ❌ Fehler: $_"
        $testResults += $false
    }
    
    # Test 3: Anlagen Suche
    Write-Info "Test 3/6: Anlagen Suche..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/anlagen/search?db=bimschg&limit=10" -TimeoutSec 5
        if ($response.count -gt 0) {
            Write-Success "  ✅ $($response.count) Anlagen gefunden"
            $testResults += $true
        }
        else {
            Write-Error-Custom "  ❌ Keine Anlagen gefunden"
            $testResults += $false
        }
    }
    catch {
        Write-Error-Custom "  ❌ Fehler: $_"
        $testResults += $false
    }
    
    # Test 4: Verfahren Suche
    Write-Info "Test 4/6: Verfahren Suche..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/verfahren/search?limit=10" -TimeoutSec 5
        if ($response.Count -gt 0) {
            Write-Success "  ✅ $($response.Count) Verfahren gefunden"
            $testResults += $true
        }
        else {
            Write-Error-Custom "  ❌ Keine Verfahren gefunden"
            $testResults += $false
        }
    }
    catch {
        Write-Error-Custom "  ❌ Fehler: $_"
        $testResults += $false
    }
    
    # Test 5: Messungen Suche
    Write-Info "Test 5/6: Messungen Suche..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/messungen/search?limit=10" -TimeoutSec 5
        if ($response.Count -gt 0) {
            Write-Success "  ✅ $($response.Count) Messungen gefunden"
            $testResults += $true
        }
        else {
            Write-Error-Custom "  ❌ Keine Messungen gefunden"
            $testResults += $false
        }
    }
    catch {
        Write-Error-Custom "  ❌ Fehler: $_"
        $testResults += $false
    }
    
    # Test 6: Statistik
    Write-Info "Test 6/6: Statistik..."
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:$ServerPort/statistik/overview" -TimeoutSec 5
        if ($response.statistics) {
            Write-Success "  ✅ Statistik abgerufen"
            $testResults += $true
        }
        else {
            Write-Error-Custom "  ❌ Keine Statistik-Daten"
            $testResults += $false
        }
    }
    catch {
        Write-Error-Custom "  ❌ Fehler: $_"
        $testResults += $false
    }
    
    # Ergebnis
    Write-Host ""
    Write-Host "="*70 -ForegroundColor Cyan
    $passed = ($testResults | Where-Object { $_ -eq $true }).Count
    $total = $testResults.Count
    
    if ($passed -eq $total) {
        Write-Success "✅ Alle Tests bestanden ($passed/$total)"
    }
    else {
        Write-Warning "⚠️  $passed/$total Tests bestanden"
    }
    Write-Host "="*70 -ForegroundColor Cyan
    Write-Host ""
}

# Hauptlogik
switch ($Action) {
    "start" { Start-Server }
    "stop" { Stop-Server }
    "restart" { Restart-Server }
    "status" { Get-ServerStatus }
    "test" { Test-Server }
}
