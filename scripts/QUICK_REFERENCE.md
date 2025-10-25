# 🚀 VERITAS Backend v4.0.0 - Quick Reference

## Schnellstart

```powershell
# Backend starten
.\scripts\start_services.ps1 -BackendOnly

# Status prüfen
.\scripts\manage_backend_v4.ps1 -Action status

# Testen
.\scripts\manage_backend_v4.ps1 -Action test
```

## Befehle

| Befehl | Aktion |
|--------|--------|
| `start_services.ps1` | Startet Backend + Frontend |
| `start_services.ps1 -BackendOnly` | Nur Backend |
| `stop_services.ps1` | Stoppt alles |
| `restart_backend_debug.ps1` | Debug-Modus |
| `manage_backend_v4.ps1 -Action start` | Backend starten |
| `manage_backend_v4.ps1 -Action stop` | Backend stoppen |
| `manage_backend_v4.ps1 -Action restart` | Backend neu starten |
| `manage_backend_v4.ps1 -Action status` | Status anzeigen |
| `manage_backend_v4.ps1 -Action test` | Tests durchführen |
| `manage_backend_v4.ps1 -Action info` | Detailinfo |

## Endpoints

```
Health:        http://localhost:5000/api/system/health
Info:          http://localhost:5000/api/system/info
Capabilities:  http://localhost:5000/api/system/capabilities
Modes:         http://localhost:5000/api/system/modes
Query:         http://localhost:5000/api/query
Docs:          http://localhost:5000/docs
```

## Health Check

```powershell
Invoke-RestMethod http://localhost:5000/api/system/health
```

## Query Test

```powershell
$body = @{
    query = "Was ist VERITAS?"
    mode = "ask"
    model = "llama3.1"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:5000/api/query -Method Post -Body $body -ContentType "application/json"
```

## Logs

```powershell
# Live-Logs
Get-Content logs/backend_v4.log -Wait -Tail 50

# Letzte Zeilen
Get-Content logs/backend_v4.log -Tail 100

# Fehler-Logs
Get-Content logs/backend_uvicorn.err.log -Tail 50
```

## Prozess-Info

```powershell
# PID anzeigen
Get-Content data/backend_v4.pid

# Prozess finden
Get-Process -Name python | Where-Object { $_.Id -eq (Get-Content data/backend_v4.pid) }

# Port prüfen
netstat -ano | findstr ":5000"
```

## Troubleshooting

```powershell
# Force Stop
Stop-Process -Id (Get-Content data/backend_v4.pid) -Force
Remove-Item data/backend_v4.pid

# Cache löschen
Get-ChildItem backend -Filter __pycache__ -Recurse -Directory | Remove-Item -Recurse -Force

# Neustart
.\scripts\manage_backend_v4.ps1 -Action restart
```

## Query Modes

- `rag` - RAG with Agent Orchestration
- `hybrid` - BM25 + Dense + RRF Fusion
- `streaming` - Streaming Response
- `agent` - Multi-Agent Pipeline
- `ask` - Direct LLM (no RAG)

## UnifiedResponse Format

```json
{
  "content": "Antwort mit [1], [2], [3] Zitaten",
  "sources": [
    {
      "id": "1",
      "title": "Dokument-Titel",
      "ieee_citation": "Author et al., 2024...",
      "similarity_score": 0.95,
      "impact": "High",
      "relevance": "Very High",
      "rechtsgebiet": "VwVfG"
    }
  ],
  "metadata": {
    "model": "llama3.1",
    "mode": "rag",
    "duration": 1.23,
    "tokens_used": 450
  }
}
```
