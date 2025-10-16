# VERITAS Service Management

Schnelle und einfache Verwaltung der VERITAS Backend- und Frontend-Services.

## 📋 Verfügbare Scripts

### Haupt-Scripts (Root-Verzeichnis)

#### `start.bat` / `stop.bat`
Einfachste Verwendung - Doppelklick oder Kommandozeile:

```batch
# Services starten
start.bat

# Services stoppen
stop.bat
```

### PowerShell Scripts (scripts/ Verzeichnis)

#### `scripts\start_services.ps1`
Startet Backend und/oder Frontend Services.

**Verwendung:**
```powershell
# Beide Services starten
.\scripts\start_services.ps1

# Nur Backend starten
.\scripts\start_services.ps1 -BackendOnly

# Nur Frontend starten
.\scripts\start_services.ps1 -FrontendOnly
```

**Was passiert:**
- ✅ Backend startet auf Port 5000
- ✅ Frontend startet mit Tkinter GUI
- ✅ Services laufen als PowerShell Background Jobs
- ✅ Automatischer Health Check
- ✅ PIDs werden gespeichert für einfaches Stoppen

#### `scripts\stop_services.ps1`
Stoppt laufende VERITAS Services.

**Verwendung:**
```powershell
# Alle Services stoppen
.\scripts\stop_services.ps1

# Nur Backend stoppen
.\scripts\stop_services.ps1 -BackendOnly

# Nur Frontend stoppen
.\scripts\stop_services.ps1 -FrontendOnly

# Erzwinge Stop (auch hartnäckige Prozesse)
.\scripts\stop_services.ps1 -Force
```

**Stop-Methoden (in dieser Reihenfolge):**
1. 📋 Gespeicherte PIDs (aus `.veritas_pids.txt`)
2. 🔌 Backend über Port 5000
3. 🐍 Python-Prozesse mit Skript-Namen
4. 💼 PowerShell Background Jobs

### Backend-Management (Root-Verzeichnis)

#### `manage_backend.ps1`
Detailliertes Backend-Management mit Status-Informationen.

**Verwendung:**
```powershell
# Backend starten
.\manage_backend.ps1 -Action start

# Backend stoppen
.\manage_backend.ps1 -Action stop

# Backend neu starten
.\manage_backend.ps1 -Action restart

# Backend-Status anzeigen
.\manage_backend.ps1 -Action status
```

**Status-Informationen:**
- ✅ Running/Stopped Status
- 📊 CPU & Speicher-Verwendung
- 🌐 Port und URL
- 🏥 Health Check Ergebnis
- ⏰ Startzeit

#### `backend.bat`
Schnellzugriff für Backend-Management:

```batch
backend.bat start
backend.bat stop
backend.bat restart
backend.bat status
```

## 🚀 Schnellstart

### Option 1: Batch-Dateien (einfachste Methode)
```batch
# Starten
start.bat

# Stoppen
stop.bat
```

### Option 2: PowerShell Scripts
```powershell
# Starten
.\scripts\start_services.ps1

# Status prüfen
.\manage_backend.ps1 -Action status

# Stoppen
.\scripts\stop_services.ps1
```

### Option 3: Nur Backend
```batch
# Starten
backend.bat start

# Status prüfen
backend.bat status

# Stoppen
backend.bat stop
```

## 📝 Log-Dateien

Alle Logs werden im `data/` Verzeichnis gespeichert:

```
data/
├── veritas_backend.log       # Backend Stdout
├── veritas_backend.log.err   # Backend Stderr
├── veritas_frontend.log      # Frontend Stdout
├── veritas_frontend.log.err  # Frontend Stderr
└── .veritas_pids.txt         # Gespeicherte Process IDs
```

**Logs anzeigen:**
```powershell
# Letzte 20 Zeilen Backend-Log
Get-Content data\veritas_backend.log -Tail 20

# Echtzeit-Monitoring
Get-Content data\veritas_backend.log -Wait

# Error-Log prüfen
Get-Content data\veritas_backend.log.err
```

## 🔍 Troubleshooting

### Backend startet nicht

**Symptom:** Backend-Start schlägt fehl oder Timeout

**Lösungen:**
```powershell
# 1. Prüfe ob Port blockiert ist
Get-NetTCPConnection -LocalPort 5000

# 2. Prüfe Error-Log
Get-Content data\veritas_backend.log.err -Tail 30

# 3. Stoppe alle Python-Prozesse und starte neu
.\scripts\stop_services.ps1 -Force
.\scripts\start_services.ps1
```

### Port bereits belegt

**Symptom:** "Port 5000 already in use"

**Lösungen:**
```powershell
# Finde Prozess auf Port 5000
Get-NetTCPConnection -LocalPort 5000 | Select-Object OwningProcess
Get-Process -Id <PID>

# Stoppe Prozess
Stop-Process -Id <PID> -Force

# Oder verwende Force-Stop
.\scripts\stop_services.ps1 -Force
```

### Services laufen nach Stop weiter

**Symptom:** Backend antwortet noch nach `stop_services.ps1`

**Lösung:**
```powershell
# Force-Stop verwendet mehrere Methoden
.\scripts\stop_services.ps1 -Force

# Manuell alle Python-Prozesse stoppen
Get-Process -Name python | Stop-Process -Force
```

### PID-Datei fehlt

**Symptom:** "PID-Datei nicht gefunden"

**Lösung:**
```powershell
# Stop-Script findet Prozesse auch ohne PID-Datei
# Verwendet Port und Skript-Namen als Fallback
.\scripts\stop_services.ps1

# Oder über Backend-Management
.\manage_backend.ps1 -Action stop
```

## 🔧 PowerShell Job Management

Falls Services als PowerShell Jobs laufen:

```powershell
# Alle Jobs anzeigen
Get-Job

# Job-Logs ansehen
Get-Job | Receive-Job -Keep

# Job manuell stoppen
Get-Job | Stop-Job
Get-Job | Remove-Job
```

## 📊 Service-URLs

Nach erfolgreichem Start:

**Backend:**
- 🏠 Base URL: http://localhost:5000
- 🏥 Health Check: http://localhost:5000/health
- 📚 API Docs: http://localhost:5000/docs
- 🔍 ReDoc: http://localhost:5000/redoc

**Frontend:**
- 🖥️ Tkinter GUI öffnet automatisch

## ⚙️ Konfiguration

### Ports ändern

In `scripts\start_services.ps1`:
```powershell
$BackendPort = 5000  # Ändern auf gewünschten Port
```

In `manage_backend.ps1`:
```powershell
$BackendPort = 5000  # Hier auch ändern
```

### Log-Verzeichnis ändern

In beiden Scripts:
```powershell
$BackendLog = Join-Path $RootDir "data\veritas_backend.log"
# Ändern auf gewünschten Pfad
```

## 🎯 Best Practices

1. **Immer `stop_services.ps1` verwenden** statt Prozesse manuell zu beenden
2. **`backend.bat status` regelmäßig prüfen** für System-Health
3. **Logs überwachen** bei unerwartetem Verhalten
4. **Force-Stop nur im Notfall** verwenden
5. **PID-Datei nicht manuell bearbeiten**

## 📖 Weitere Informationen

- [Backend API Dokumentation](../docs/VERITAS_API_BACKEND_DOCUMENTATION.md)
- [Chat-Verlauf Integration](../docs/CHAT_HISTORY_INTEGRATION.md)
- [Streaming Display Fix](../docs/STREAMING_DISPLAY_FIX.md)
