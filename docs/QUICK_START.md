# VERITAS Unified Backend - Quick Start
## 🚀 Schnellstart für v4.0.0

---

## Start Backend

### Option 1: Via Start-Skript (Empfohlen)

```powershell
python start_backend.py
```

### Option 2: Direkt

```powershell
python backend/app.py
```

### Option 3: Mit Reload (Development)

```powershell
cd backend
python backend.py
# Oder mit uvicorn:
uvicorn backend:app --reload --host 0.0.0.0 --port 5000
```

---

## Endpoints

### Root

```bash
GET http://localhost:5000/
```

**Response:**
```json
{
  "service": "VERITAS Unified Backend",
  "version": "4.0.0",
  "api": {"base": "/api", "version": "4.0.0"},
  "documentation": {"swagger": "/docs", "redoc": "/redoc"},
  "features": {
    "unified_response": true,
    "ieee_citations": true,
    "multi_mode": true
  }
}
```

---

### Health Check

```bash
GET http://localhost:5000/api/system/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-19T14:30:00",
  "components": {
    "uds3": true,
    "pipeline": true,
    "streaming": false
  }
}
```

---

### System Info

```bash
GET http://localhost:5000/api/system/info
```

---

## Query Endpoints

### 1. Unified Query (Alle Modi)

```bash
POST http://localhost:5000/api/query
Content-Type: application/json

{
  "query": "Was regelt das BImSchG?",
  "mode": "rag",
  "model": "llama3.2",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Modi:**
- `"rag"` - RAG Query (Standard)
- `"hybrid"` - Hybrid Search
- `"streaming"` - Streaming Query
- `"agent"` - Agent Query
- `"ask"` - Simple Ask

---

### 2. RAG Query

```bash
POST http://localhost:5000/api/query/rag
Content-Type: application/json

{
  "query": "BImSchG Genehmigungsverfahren",
  "model": "llama3.2"
}
```

---

### 3. Simple Ask

```bash
POST http://localhost:5000/api/query/ask
Content-Type: application/json

{
  "query": "Erkläre mir das BImSchG",
  "model": "llama3.2"
}
```

---

### 4. Hybrid Search

```bash
POST http://localhost:5000/api/query/hybrid
Content-Type: application/json

{
  "query": "Immissionsschutz Anlagen",
  "top_k": 10,
  "bm25_weight": 0.5,
  "dense_weight": 0.5,
  "enable_reranking": true
}
```

---

## Response Format

**Alle Endpoints geben UnifiedResponse zurück:**

```json
{
  "content": "Das BImSchG regelt... [1]\n\nGenehmigung... [2]",
  "sources": [
    {
      "id": "1",
      "title": "Bundes-Immissionsschutzgesetz",
      "type": "document",
      "authors": "Deutscher Bundestag",
      "ieee_citation": "Deutscher Bundestag, 'Bundes-Immissionsschutzgesetz', BGBl. I S. 1193, 2024.",
      "year": 2024,
      "publisher": "Bundesanzeiger Verlag",
      "similarity_score": 0.92,
      "rerank_score": 0.95,
      "quality_score": 0.90,
      "impact": "High",
      "relevance": "Very High",
      "rechtsgebiet": "Umweltrecht"
    },
    {
      "id": "2",
      "title": "4. BImSchV",
      "similarity_score": 0.88
    }
  ],
  "metadata": {
    "model": "llama3.2",
    "mode": "rag",
    "duration": 2.34,
    "tokens_used": 456,
    "sources_count": 2,
    "agents_involved": ["document_retrieval", "legal_framework"]
  },
  "session_id": "sess_abc123",
  "timestamp": "2025-10-19T14:30:00"
}
```

---

## Agent Endpoints

### Liste Agents

```bash
GET http://localhost:5000/api/agent/list
```

### Agent Capabilities

```bash
GET http://localhost:5000/api/agent/capabilities
```

---

## PowerShell Testing

### Test Script

```powershell
# Health Check
Invoke-RestMethod -Uri "http://localhost:5000/api/system/health" -Method Get

# RAG Query
$body = @{
    query = "Was regelt das BImSchG?"
    mode = "rag"
    model = "llama3.2"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5000/api/query" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

---

## cURL Testing

```bash
# Health
curl http://localhost:5000/api/system/health

# Query
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was regelt das BImSchG?",
    "mode": "rag",
    "model": "llama3.2"
  }'
```

---

## Frontend Integration

### JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:5000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Was regelt das BImSchG?',
    mode: 'rag',
    model: 'llama3.2'
  })
});

const data: UnifiedResponse = await response.json();

// Content mit Citations
console.log(data.content);  // "Das BImSchG... [1]"

// IEEE Citations (35+ Felder)
data.sources.forEach((source, idx) => {
  console.log(`[${source.id}] ${source.title}`);
  console.log(`   IEEE: ${source.ieee_citation}`);
  console.log(`   Score: ${source.similarity_score}`);
  console.log(`   Impact: ${source.impact}`);
});

// Metadata
console.log(`Mode: ${data.metadata.mode}`);
console.log(`Duration: ${data.metadata.duration}s`);
console.log(`Agents: ${data.metadata.agents_involved}`);
```

---

## Environment Variables

```bash
# Optional Configuration
VERITAS_LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
VERITAS_API_HOST=0.0.0.0        # Bind address
VERITAS_API_PORT=5000           # Port
VERITAS_API_RELOAD=false        # Auto-reload on code changes
```

---

## Troubleshooting

### Backend startet nicht

```powershell
# Check Python Version
python --version  # Should be 3.10+

# Check Dependencies
pip install fastapi uvicorn pydantic

# Check Port
netstat -ano | findstr :5000  # Port frei?
```

### UDS3 nicht verfügbar

**Normal!** Backend läuft im **Demo Mode** mit Mock-Responses.

```
⚠️  UDS3 Demo Mode - Keine echten Datenbanken
⚠️  Intelligent Pipeline Demo Mode
```

Mock-Responses enthalten trotzdem IEEE-konforme Sources (35+ Felder).

### Keine Sources

**Check:**
1. UDS3 verfügbar? `GET /api/system/health`
2. ChromaDB populated? Siehe UDS3 Docs
3. Mock-Fallback aktiv? Logs checken

---

## Documentation

- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc
- **Health:** http://localhost:5000/api/system/health
- **Capabilities:** http://localhost:5000/api/system/capabilities

---

## Next Steps

1. ✅ Backend starten
2. ✅ Health Check erfolgreich
3. ✅ Test Query durchführen
4. ✅ Response-Format verifizieren
5. ⏳ Frontend anpassen
6. ⏳ ChromaDB mit Dokumenten füllen
7. ⏳ Production Deployment

---

**Status:** ✅ **Ready to Use!**
