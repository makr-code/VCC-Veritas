# VERITAS Backend v3 Management

PowerShell-Script zur Verwaltung des VERITAS API v3 Backends.

## 📋 Features

- ✅ **Start**: Backend im Hintergrund starten
- ✅ **Stop**: Backend sauber beenden
- ✅ **Restart**: Backend neu starten
- ✅ **Status**: Prozess-Info und API-Health anzeigen
- ✅ **Test**: Wichtige Endpoints testen
- ✅ **PID-Management**: Automatische Prozess-Verfolgung
- ✅ **Fehlerbehandlung**: Robuste Prozess-Suche und Cleanup

## 🚀 Verwendung

### Backend starten

```powershell
.\scripts\manage_backend_v3.ps1 -Action start
```

**Output:**
```
========================================
 VERITAS Backend v3 Starten
========================================

ℹ️  Starte Backend...
ℹ️  Script: C:\VCC\veritas\start_backend.py
ℹ️  API Base: http://localhost:5000/api/v3

✅ Backend-Prozess gestartet (PID: 12345)
ℹ️  Warte 5 Sekunden auf Initialisierung...
✅ Backend läuft!

📍 API Base:       http://localhost:5000/api/v3
📖 Documentation: http://localhost:5000/docs
📊 Health Check:  http://localhost:5000/health
📝 Logs:          C:\VCC\veritas\data\veritas_api_v3.log
```

**Custom Wartezeit:**
```powershell
.\scripts\manage_backend_v3.ps1 -Action start -Wait 10
```

---

### Backend stoppen

```powershell
.\scripts\manage_backend_v3.ps1 -Action stop
```

**Output:**
```
========================================
 VERITAS Backend v3 Stoppen
========================================

ℹ️  Backend-Prozess gefunden (PID: 12345)
→ Stoppe Backend...
✅ Backend gestoppt
```

---

### Backend-Status anzeigen

```powershell
.\scripts\manage_backend_v3.ps1 -Action status
```

**Output (läuft):**
```
========================================
 VERITAS Backend v3 Status
========================================

Status:      ✅ RUNNING
PID:         12345
Memory:      256.45 MB
CPU Time:    00:05:23
Started:     2025-10-18 10:00:00

→ Teste API-Verbindung...
✅ API erreichbar
  Version:     3.0.0
  Status:      healthy
  Services:
    - UDS3:      ✅
    - Pipeline:  ✅
    - Streaming: ✅

📍 API Base:       http://localhost:5000/api/v3
📖 Documentation: http://localhost:5000/docs
📝 Logs:          C:\VCC\veritas\data\veritas_api_v3.log
```

**Output (gestoppt):**
```
========================================
 VERITAS Backend v3 Status
========================================

Status:      ❌ STOPPED
```

---

### Backend neu starten

```powershell
.\scripts\manage_backend_v3.ps1 -Action restart
```

Kombiniert `stop` und `start` in einem Befehl.

---

### Backend testen

```powershell
.\scripts\manage_backend_v3.ps1 -Action test
```

**Output:**
```
========================================
 VERITAS Backend v3 Tests
========================================

✅ Backend läuft (PID: 12345)

→ Teste: Root Endpoint... ✅
→ Teste: Health Check... ✅
→ Teste: API v3 Root... ✅
→ Teste: System Info... ✅

========================================
Ergebnis: 4/4 Tests bestanden
========================================
```

---

## 🔧 Technische Details

### Prozess-Erkennung

Das Script erkennt den Backend-Prozess über:
1. **PID-File** (`data/backend_v3.pid`) - Primär
2. **Command-Line-Scan** - Fallback (sucht nach `start_backend.py` oder `veritas_api_backend_v3`)

### Dateien

| Datei | Beschreibung |
|-------|--------------|
| `data/backend_v3.pid` | PID des laufenden Backend-Prozesses |
| `data/veritas_api_v3.log` | Backend-Logs (rotating file handler) |
| `start_backend.py` | Backend-Launcher-Script |

### API-Endpoints

Das Script testet folgende Endpoints:

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /` | Root-Endpoint (Redirect zu v3) |
| `GET /health` | Health-Check mit Service-Status |
| `GET /api/v3/` | API v3 Root-Endpoint |
| `GET /api/v3/system/info` | System-Informationen |

### Exit-Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Erfolg |
| `1` | Fehler |

---

## 📚 Beispiele

### Workflow: Backend starten und testen

```powershell
# 1. Backend starten
.\scripts\manage_backend_v3.ps1 -Action start

# 2. Status prüfen
.\scripts\manage_backend_v3.ps1 -Action status

# 3. Endpoints testen
.\scripts\manage_backend_v3.ps1 -Action test

# 4. Bei Problemen: Neustart
.\scripts\manage_backend_v3.ps1 -Action restart
```

### Automatisierung in anderen Scripts

```powershell
# In einem anderen Script
$result = & ".\scripts\manage_backend_v3.ps1" -Action start
if ($LASTEXITCODE -eq 0) {
    Write-Host "Backend erfolgreich gestartet"
} else {
    Write-Host "Backend-Start fehlgeschlagen"
    exit 1
}
```

### Scheduled Task (täglicher Neustart)

```powershell
# Task erstellen
$action = New-ScheduledTaskAction -Execute "pwsh.exe" `
    -Argument "-File C:\VCC\veritas\scripts\manage_backend_v3.ps1 -Action restart"

$trigger = New-ScheduledTaskTrigger -Daily -At "03:00"

Register-ScheduledTask -TaskName "VERITAS Backend Restart" `
    -Action $action -Trigger $trigger `
    -Description "Täglicher Neustart des VERITAS Backends"
```

---

## 🐛 Troubleshooting

### Backend startet nicht

1. **Prüfe Logs:**
   ```powershell
   Get-Content "C:\VCC\veritas\data\veritas_api_v3.log" -Tail 50
   ```

2. **Port 5000 belegt?**
   ```powershell
   Get-NetTCPConnection -LocalPort 5000
   ```

3. **Python-Umgebung aktiv?**
   ```powershell
   python --version
   pip list | Select-String "fastapi|uvicorn"
   ```

### Backend läuft, aber API antwortet nicht

1. **Warte länger auf Initialisierung:**
   ```powershell
   .\scripts\manage_backend_v3.ps1 -Action start -Wait 15
   ```

2. **Prüfe Firewall:**
   ```powershell
   Test-NetConnection -ComputerName localhost -Port 5000
   ```

### PID-File zeigt falschen Prozess

Script verwendet Fallback-Logik (Command-Line-Scan), funktioniert auch ohne korrektes PID-File.

**Manueller Cleanup:**
```powershell
Remove-Item "C:\VCC\veritas\data\backend_v3.pid" -Force
```

---

## 🔗 Siehe auch

- [API v3 Dokumentation](../docs/API_V3_COMPLETE.md)
- [Migration Report](../docs/MIGRATION_V3_REPORT.md)
- [Backend Code](../backend/api/veritas_api_backend_v3.py)

---

## 📝 Changelog

### Version 1.0.0 (2025-10-18)
- ✅ Initial Release
- ✅ Start/Stop/Restart Funktionalität
- ✅ Status-Anzeige mit API-Health-Check
- ✅ Endpoint-Tests
- ✅ Robuste Prozess-Erkennung
- ✅ PID-Management
