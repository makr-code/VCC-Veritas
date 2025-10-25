# VERITAS Backend v4.0.0 - PowerShell Skripte

Verwaltungsskripte für VERITAS Backend v4.0.0 (Unified Architecture)

## 📋 Übersicht

| Skript | Beschreibung | Verwendung |
|--------|--------------|------------|
| `start_services.ps1` | Startet Backend + Frontend | Produktiv-Start |
| `stop_services.ps1` | Stoppt Backend + Frontend | Sauberes Herunterfahren |
| `restart_backend_debug.ps1` | Debug-Restart mit Live-Logs | Entwicklung |
| `manage_backend_v4.ps1` | Vollständiges Management | Alle Operationen |

## 🚀 Quick Start

### Backend + Frontend starten
```powershell
.\scripts\start_services.ps1
```

### Nur Backend starten
```powershell
.\scripts\start_services.ps1 -BackendOnly
```

### Backend stoppen
```powershell
.\scripts\stop_services.ps1 -BackendOnly
```

### Debug-Restart
```powershell
.\scripts\restart_backend_debug.ps1
```

## 🔧 Manage Backend v4.0.0

Das neue `manage_backend_v4.ps1` Skript bietet vollständige Kontrolle:

### Start
```powershell
.\scripts\manage_backend_v4.ps1 -Action start
```

Mit Debug-Logging:
```powershell
.\scripts\manage_backend_v4.ps1 -Action start -Debug
```

### Stop
```powershell
.\scripts\manage_backend_v4.ps1 -Action stop
```

### Restart
```powershell
.\scripts\manage_backend_v4.ps1 -Action restart
```

### Status
```powershell
.\scripts\manage_backend_v4.ps1 -Action status
```

Zeigt:
- Prozess-Info (PID, CPU, Memory, Threads)
- API-Status (Health, Components)
- Verfügbare Endpoints

### Test
```powershell
.\scripts\manage_backend_v4.ps1 -Action test
```

Führt aus:
1. Health Check
2. System Info
3. Capabilities
4. Query Modes
5. Beispiel-Query

### Info
```powershell
.\scripts\manage_backend_v4.ps1 -Action info
```

Zeigt:
- Version & Architektur
- Components & Features
- Capabilities (Query Modes, Agent Types, Vector DBs, Embeddings)

## 📊 Backend v4.0.0 Endpoints

### System Endpoints (Flat Structure)
- **Health**: `http://localhost:5000/api/system/health`
- **Info**: `http://localhost:5000/api/system/info`
- **Capabilities**: `http://localhost:5000/api/system/capabilities`
- **Modes**: `http://localhost:5000/api/system/modes`

### Query Endpoints
- **Unified Query**: `http://localhost:5000/api/query`
  - POST mit mode parameter (rag, hybrid, streaming, agent, ask)
- **Simple Ask**: `http://localhost:5000/api/query/ask`
- **RAG Query**: `http://localhost:5000/api/query/rag`
- **Hybrid Search**: `http://localhost:5000/api/query/hybrid`
- **Streaming**: `http://localhost:5000/api/query/stream`

### Agent Endpoints
- **List Agents**: `http://localhost:5000/api/agent/list`
- **Capabilities**: `http://localhost:5000/api/agent/capabilities`
- **Agent Status**: `http://localhost:5000/api/agent/status/{id}`

### Dokumentation
- **OpenAPI Docs**: `http://localhost:5000/docs`
- **ReDoc**: `http://localhost:5000/redoc`

## 🔍 Troubleshooting

### Backend startet nicht

1. **Check PID-Datei**:
   ```powershell
   Get-Content data/backend_v4.pid
   ```

2. **Check Logs**:
   ```powershell
   Get-Content logs/backend_v4.log -Tail 50
   ```

3. **Check Port**:
   ```powershell
   netstat -ano | findstr ":5000"
   ```

4. **Force Stop**:
   ```powershell
   .\scripts\manage_backend_v4.ps1 -Action stop
   Remove-Item data/backend_v4.pid -Force
   ```

### Health Check fehlschlägt

**Mögliche Ursachen**:
- UDS3 nicht verfügbar (normal, Backend funktioniert trotzdem)
- Pipeline nicht initialisiert (normal im Mock-Modus)
- Agents nicht geladen (optional)

**Prüfe Components**:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/system/health" | ConvertTo-Json -Depth 10
```

Erwartete Antwort (Mock-Modus):
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "components": {
    "uds3": false,
    "pipeline": false,
    "agents": false
  }
}
```

### Debug-Logs aktivieren

**Methode 1: Über Management-Skript**:
```powershell
.\scripts\manage_backend_v4.ps1 -Action start -Debug
```

**Methode 2: Direkter Start**:
```powershell
python -m uvicorn backend.app:app --host 0.0.0.0 --port 5000 --log-level debug --reload
```

**Methode 3: Debug-Restart-Skript**:
```powershell
.\scripts\restart_backend_debug.ps1
```

## 📝 Log-Dateien

| Log-Datei | Beschreibung | Verwendung |
|-----------|--------------|------------|
| `logs/backend_v4.log` | Standard Backend-Logs | Produktiv |
| `logs/backend_uvicorn.log` | Uvicorn Access-Logs | HTTP-Requests |
| `logs/backend_uvicorn.err.log` | Uvicorn Error-Logs | Fehler |
| `data/veritas_auto_server.log` | Auto-Server-Logs | Legacy |

**Log-Rotation**: Beim Start werden alte Logs zu `.log.old` verschoben

## 🔄 Migration von v3 zu v4

### Änderungen in Skripten

**Alt (v3)**:
```powershell
# Backend v3 verwendete verschachtelte Struktur
python -m uvicorn backend.api.veritas_api_backend_v3:app
```

**Neu (v4)**:
```powershell
# Backend v4 verwendet flache Struktur
python -m uvicorn backend.app:app
```

### Endpoint-Änderungen

**Alt (v3)**:
- `/health` → `/api/system/health`
- `/v2/query` → `/api/query`
- `/ask` → `/api/query/ask`

**Neu (v4)**:
- Alle Endpoints unter `/api/` (flache Struktur)
- Einheitliches UnifiedResponse-Format
- IEEE Citations mit 35+ Feldern

## 🎯 Best Practices

### Entwicklung
```powershell
# 1. Backend mit Auto-Reload starten
.\scripts\restart_backend_debug.ps1

# 2. Frontend in separatem Terminal
python frontend/veritas_app.py

# 3. Logs überwachen
Get-Content logs/backend_v4.log -Wait
```

### Produktion
```powershell
# 1. Services starten
.\scripts\start_services.ps1

# 2. Status prüfen
.\scripts\manage_backend_v4.ps1 -Action status

# 3. Test durchführen
.\scripts\manage_backend_v4.ps1 -Action test
```

### Testing
```powershell
# 1. Backend starten
.\scripts\manage_backend_v4.ps1 -Action start

# 2. Tests ausführen
pytest tests/

# 3. Backend stoppen
.\scripts\manage_backend_v4.ps1 -Action stop
```

## ⚙️ Umgebungsvariablen

Das Backend v4.0.0 unterstützt folgende Umgebungsvariablen:

```powershell
$env:VERITAS_ENV = "production"         # production, development, test
$env:VERITAS_LOG_LEVEL = "INFO"         # DEBUG, INFO, WARNING, ERROR
$env:VERITAS_PORT = "5000"              # Backend Port
$env:VERITAS_HOST = "0.0.0.0"           # Backend Host
$env:UDS3_PATH = "C:\VCC\uds3"          # UDS3 Pfad (optional)
```

## 🆘 Support

Bei Problemen:

1. **Logs prüfen**: `Get-Content logs/backend_v4.log -Tail 100`
2. **Status prüfen**: `.\scripts\manage_backend_v4.ps1 -Action status`
3. **Neustart**: `.\scripts\manage_backend_v4.ps1 -Action restart`
4. **Test**: `.\scripts\manage_backend_v4.ps1 -Action test`

## 📚 Weitere Dokumentation

- [Backend Refactoring](../docs/BACKEND_REFACTORING.md)
- [Frontend Integration](../docs/FRONTEND_INTEGRATION.md)
- [Quick Start](../docs/QUICK_START.md)
- [Migration Checklist](../docs/MIGRATION_CHECKLIST.md)
