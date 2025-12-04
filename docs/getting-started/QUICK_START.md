# Quickstart Guide

**Zielgruppe:** Neue Entwickler, Schneller Überblick
**Dauer:** ~30 Minuten
**Status:** ✅ Production Ready

---

## 🎯 Überblick

VERITAS ist ein **AI-gestütztes Dokumentations- und Recherche-System** mit:

- **Hybrid Search:** Vector (ChromaDB) + Keyword (BM25) + Graph (Neo4j)
- **Multi-Agent RAG:** Intelligente Dokumentenanalyse mit LLM
- **Office Integration:** Word Add-In für direkte Recherche
- **Real-time Streaming:** Server-Sent Events für Live-Responses

---

## ⚡ 5-Minuten Setup

### 1. Repository klonen
```bash
git clone https://github.com/makr-code/VCC-Veritas.git
cd veritas
```

### 2. Python Environment
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac
```

### 3. Dependencies installieren
```bash
pip install -r requirements.txt
```

### 4. Backend starten
```bash
python start_backend.py
```

Der Backend läuft dann auf `http://localhost:5000`

### 5. Testen
```bash
curl http://localhost:5000/api/system/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "3.25.0",
  "components": {
    "database": "connected",
    "llm": "ready",
    "search": "initialized"
  }
}
```

---

## 🔍 Erste Query durchführen

### Über REST API
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was wird in §15 BImSchG geregelt?",
    "mode": "ask"
  }'
```

### Response
```json
{
  "status": "success",
  "answer": "...",
  "sources": [
    {
      "title": "BImSchG §15",
      "snippet": "...",
      "relevance_score": 0.95
    }
  ]
}
```

---

## 📂 Wichtige Verzeichnisse

```
veritas/
├── backend/              # Backend-Code
│   ├── api/             # API Endpoints
│   ├── agents/          # Multi-Agent System
│   ├── services/        # Business Logic
│   └── models/          # Data Models
├── frontend/            # Frontend (React)
├── docs/                # Diese Dokumentation
├── tests/               # Test Suite
└── config/              # Konfiguration
```

---

## 🚀 Nächste Schritte

1. **Installation:** [Installation Guide](INSTALLATION.md)
2. **Erste Query:** [Erste Abfrage durchführen](FIRST_QUERY.md)
3. **Probleme?** [Troubleshooting](TROUBLESHOOTING.md)
4. **Entwicklung:** [Development Guide](../development/DEVELOPMENT.md)

---

## 📚 Dokumentation

- **[Systemübersicht](../architecture/OVERVIEW.md)** - Wie funktioniert VERITAS?
- **[Backend-Architektur](../architecture/BACKEND_ARCHITECTURE.md)** - Backend-Details
- **[API-Referenz](../api/API_REFERENCE.md)** - Alle Endpoints
- **[Deployment](../deployment/DEPLOYMENT_GUIDE.md)** - Production Setup

---

## ⚙️ Häufige Probleme

### Backend startet nicht
→ Siehe [Troubleshooting](TROUBLESHOOTING.md#backend-startet-nicht)

### ChromaDB Connection Error
→ Siehe [Troubleshooting](TROUBLESHOOTING.md#chromadb-fehler)

### LLM nicht verfügbar
→ Siehe [Troubleshooting](TROUBLESHOOTING.md#llm-nicht-verfügbar)

---

## 💡 Tipps

- **Logging aktivieren:** `export VERITAS_LOG_LEVEL=DEBUG`
- **Custom Port:** `VERITAS_API_PORT=8000 python start_backend.py`
- **Swagger UI:** http://localhost:5000/docs

---

**Bereit?** → [Installation Guide](INSTALLATION.md)
