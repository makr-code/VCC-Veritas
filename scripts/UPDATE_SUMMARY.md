# ✅ PowerShell Skripte - Update auf Backend v4.0.0

## Durchgeführte Änderungen

### 📝 Aktualisierte Dateien

#### 1. `scripts/start_services.ps1`
**Änderungen**:
- ✅ Uvicorn-Befehl aktualisiert: `backend.app:app` (statt `backend.api.veritas_api_backend_v3:app`)
- ✅ Health-Endpoint aktualisiert: `/api/system/health` (statt `/health`)
- ✅ Erweiterte Health-Response mit Components (UDS3, Pipeline, Agents)
- ✅ Neue Endpoint-Dokumentation in Status-Ausgabe
- ✅ Version-Label: "Backend v4.0.0"

**Endpoints angezeigt**:
```
http://127.0.0.1:5000/api/system/health
http://127.0.0.1:5000/api/system/info
http://127.0.0.1:5000/docs
http://127.0.0.1:5000/api/query
```

#### 2. `scripts/stop_services.ps1`
**Änderungen**:
- ✅ Health-Endpoint aktualisiert: `/api/system/health`
- ✅ Version-Label: "Backend v4.0.0"

#### 3. `scripts/restart_backend_debug.ps1`
**Änderungen**:
- ✅ Uvicorn-Befehl aktualisiert: `backend.app:app`
- ✅ Log-Pfad aktualisiert: `logs/backend_v4.log`
- ✅ Neue Endpoints in Header angezeigt:
  - API: `http://localhost:5000`
  - Docs: `http://localhost:5000/docs`
  - Health: `http://localhost:5000/api/system/health`
- ✅ `--reload` Flag für Auto-Reload
- ✅ Version-Label: "Backend v4.0.0"

### 🆕 Neue Dateien

#### 4. `scripts/manage_backend_v4.ps1` (NEU!)
**Vollständiges Management-Skript mit 6 Aktionen**:

##### Actions:
1. **start** - Startet Backend v4.0.0
   - Mit Health Check
   - Mit Component-Status
   - Optional: Debug-Modus (`-Debug`)

2. **stop** - Stoppt Backend v4.0.0
   - Graceful Shutdown
   - PID-Cleanup

3. **restart** - Neustart
   - Stop + Wait + Start

4. **status** - Detaillierter Status
   - Prozess-Info (PID, CPU, Memory, Threads)
   - API-Status (Health, Components)
   - Endpoint-Liste

5. **test** - Umfassende Tests
   - Health Check
   - System Info
   - Capabilities
   - Query Modes
   - Beispiel-Query

6. **info** - Backend-Informationen
   - Version & Architektur
   - Components & Features
   - Capabilities (Query Modes, Agent Types, Vector DBs)

##### Features:
- ✅ PID-Management (`data/backend_v4.pid`)
- ✅ Log-Management (`logs/backend_v4.log`)
- ✅ Log-Rotation (`.log` → `.log.old`)
- ✅ Event-basiertes Logging
- ✅ Health Check mit Retry (10 Versuche)
- ✅ Component-Status-Anzeige
- ✅ Umfassende Error-Handling

##### Endpoints (v4.0.0 Flat Structure):
```powershell
$ENDPOINTS = @{
    health = "http://localhost:5000/api/system/health"
    info = "http://localhost:5000/api/system/info"
    capabilities = "http://localhost:5000/api/system/capabilities"
    modes = "http://localhost:5000/api/system/modes"
    query = "http://localhost:5000/api/query"
    docs = "http://localhost:5000/docs"
}
```

#### 5. `scripts/README_BACKEND_V4.md` (NEU!)
**Umfassende Dokumentation**:
- ✅ Skript-Übersicht mit Verwendungszwecken
- ✅ Quick Start Guide
- ✅ Detaillierte Befehls-Referenz
- ✅ Endpoint-Dokumentation (Flat Structure)
- ✅ Troubleshooting-Guide
- ✅ Migration Guide (v3 → v4)
- ✅ Best Practices (Entwicklung, Produktion, Testing)
- ✅ Umgebungsvariablen
- ✅ Log-Dateien Übersicht

#### 6. `scripts/QUICK_REFERENCE.md` (NEU!)
**Schnellreferenz-Karte**:
- ✅ Häufigste Befehle
- ✅ Endpoint-Liste
- ✅ Health Check Beispiele
- ✅ Query Test Beispiele
- ✅ Log-Befehle
- ✅ Prozess-Management
- ✅ Troubleshooting-Snippets
- ✅ UnifiedResponse Format

## 📊 Zusammenfassung

### Dateien
- **Aktualisiert**: 3 Skripte
- **Neu erstellt**: 3 Dateien (1 Skript + 2 Docs)
- **Gesamt**: 6 Dateien

### Änderungen im Detail

#### Backend-Modul
```diff
- backend.api.veritas_api_backend_v3:app
+ backend.app:app
```

#### Endpoints (Flat Structure)
```diff
- /health
+ /api/system/health

- /v2/query
+ /api/query

- /ask
+ /api/query/ask

+ /api/system/info          (NEU)
+ /api/system/capabilities  (NEU)
+ /api/system/modes         (NEU)
```

#### PID-Dateien
```diff
- data/.veritas_backend.pid
+ data/backend_v4.pid
```

#### Log-Dateien
```diff
- logs/backend_uvicorn.log
+ logs/backend_v4.log
```

## 🚀 Verwendung

### Standard-Betrieb
```powershell
# Start
.\scripts\start_services.ps1

# Stop
.\scripts\stop_services.ps1
```

### Management
```powershell
# Status
.\scripts\manage_backend_v4.ps1 -Action status

# Test
.\scripts\manage_backend_v4.ps1 -Action test

# Info
.\scripts\manage_backend_v4.ps1 -Action info

# Restart
.\scripts\manage_backend_v4.ps1 -Action restart
```

### Entwicklung
```powershell
# Debug-Modus mit Auto-Reload
.\scripts\restart_backend_debug.ps1

# Oder mit Management-Skript
.\scripts\manage_backend_v4.ps1 -Action start -Debug
```

## 🔍 Testing

### Quick Test
```powershell
# 1. Backend starten
.\scripts\manage_backend_v4.ps1 -Action start

# 2. Tests durchführen
.\scripts\manage_backend_v4.ps1 -Action test

# Erwartete Output:
# ✅ Health: healthy
# ✅ Backend Version: 4.0.0
# ✅ Features: [unified_response, ieee_citations, ...]
# ✅ Modi: [rag, hybrid, streaming, agent, ask]
# ✅ Query erfolgreich (Mock-Modus)
```

### Manual Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/system/health"

# Erwartete Response:
# {
#   "status": "healthy",
#   "version": "4.0.0",
#   "components": {
#     "uds3": false,      # Normal im Mock-Modus
#     "pipeline": false,  # Normal im Mock-Modus
#     "agents": false     # Optional
#   }
# }
```

## 📚 Dokumentation

Alle Details in:
- `scripts/README_BACKEND_V4.md` - Vollständige Dokumentation
- `scripts/QUICK_REFERENCE.md` - Schnellreferenz
- `docs/BACKEND_REFACTORING.md` - Backend-Architektur
- `docs/QUICK_START.md` - Quick Start Guide

## ✅ Migration Checklist

- [x] start_services.ps1 aktualisiert
- [x] stop_services.ps1 aktualisiert
- [x] restart_backend_debug.ps1 aktualisiert
- [x] manage_backend_v4.ps1 erstellt
- [x] README_BACKEND_V4.md erstellt
- [x] QUICK_REFERENCE.md erstellt
- [x] Flat Structure (kein /api/v3/)
- [x] Neue Health-Endpoint (/api/system/health)
- [x] UnifiedResponse Support
- [x] IEEE Citations Support
- [x] Component-Status Anzeige
- [x] Umfassende Tests
- [x] Debug-Modus Support
- [x] Log-Rotation
- [x] Error-Handling

## 🎯 Next Steps

1. **Backend testen**:
   ```powershell
   .\scripts\manage_backend_v4.ps1 -Action start
   .\scripts\manage_backend_v4.ps1 -Action test
   ```

2. **Frontend migrieren** (siehe `frontend/migration_example.py`)

3. **Integration testen**:
   ```powershell
   .\scripts\start_services.ps1  # Backend + Frontend
   ```

4. **Optional**: Alte Skripte backup-en
   ```powershell
   Move-Item scripts/manage_backend_v3.ps1 backup/
   ```
