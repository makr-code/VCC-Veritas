# VERITAS Backend Refactoring
## Von Multiple Backends → Unified Backend

**Datum:** 19. Oktober 2025  
**Version:** 4.0.0  
**Status:** ✅ Phase 1 Complete

---

## 🎯 Ziel

Konsolidierung von **5 verschiedenen Backend-Dateien** in **EINE zentrale** `backend/app.py`:

### Vorher (Chaos):
```
backend/api/
├── veritas_api_backend.py            # Legacy mit UDS3 v1.x
├── veritas_api_backend_v3.py         # Clean v3 mit UDS3 v2.0.0
├── veritas_api_backend_streaming.py  # Streaming Features
├── veritas_api_backend_fixed.py      # Agent Pipeline
└── veritas_api_backend_pre_v3_...    # Backup
```

### Nachher (Konsolidiert):
```
backend/
├── backend.py                        # 🎯 HAUPT-BACKEND (konsolidiert)
├── models/                           # Unified Data Models
│   ├── response.py                  # UnifiedResponse (IEEE Citations)
│   ├── request.py                   # Request Models
│   └── enums.py                     # Shared Enums
├── services/                         # Business Logic
│   └── query_service.py             # Query Processing
└── api/                             # API Layer (FLACH - kein v3/)
    ├── query_router.py              # Query Endpoints
    ├── agent_router.py              # Agent Endpoints
    └── system_router.py             # System Endpoints
```

---

## 🚀 Neue Struktur

### 1. **Unified Response Model** (`backend/models/response.py`)

**Ein Response-Format für ALLE Query-Typen:**

```python
class UnifiedResponse(BaseModel):
    content: str                              # Markdown mit [1], [2], [3]
    sources: List[UnifiedSourceMetadata]      # IEEE Citations (35+ Felder)
    metadata: UnifiedResponseMetadata         # Processing Details
    session_id: str
    timestamp: datetime
    
    # Optional Advanced Features
    agent_results: Optional[List[Dict]]
    external_data: Optional[List[Dict]]
    quality_metrics: Optional[Dict]
```

**IEEE-Standard Sources (35+ Felder):**
- Basis: `id`, `title`, `type`
- IEEE: `authors`, `ieee_citation`, `year`, `publisher`, `date`
- Scoring: `similarity_score`, `rerank_score`, `quality_score`
- Legal: `rechtsgebiet`, `behörde`, `aktenzeichen`, `gericht`
- Assessment: `impact`, `relevance`

**Gilt für:**
- ✅ RAG Queries
- ✅ Hybrid Search
- ✅ Streaming Queries
- ✅ Agent Queries
- ✅ Simple Ask

---

### 2. **Query Service** (`backend/services/query_service.py`)

**Zentrale Business Logic:**

```python
class QueryService:
    async def process_query(
        self,
        request: UnifiedQueryRequest
    ) -> UnifiedResponse:
        
        # Route based on mode
        if mode == "rag":
            result = await self._process_rag(request)
        elif mode == "hybrid":
            result = await self._process_hybrid(request)
        elif mode == "streaming":
            result = await self._process_streaming(request)
        elif mode == "agent":
            result = await self._process_agent(request)
        else:
            result = await self._process_ask(request)
        
        # Return unified response
        return UnifiedResponse(...)
```

**Vorteile:**
- Konsistente Normalisierung von Sources
- IEEE-Standard überall
- Mock-Fallback wenn UDS3/Pipeline nicht verfügbar

---

### 3. **API Router** (Flach - kein v3/)

```
backend/api/
├── __init__.py          # Router Export
├── query_router.py      # POST /api/query, /api/query/rag, etc.
├── agent_router.py      # GET /api/agent/list, etc.
└── system_router.py     # GET /api/system/health, etc.
```

**Endpoints:**

```python
# Query Endpoints
POST /api/query           # Unified (alle Modi)
POST /api/query/ask       # Simple Ask
POST /api/query/rag       # RAG Query
POST /api/query/hybrid    # Hybrid Search
POST /api/query/stream    # Streaming Query

# Agent Endpoints
GET /api/agent/list
GET /api/agent/capabilities
GET /api/agent/status/{id}

# System Endpoints
GET /api/system/health
GET /api/system/info
GET /api/system/capabilities
```

---

### 4. **Haupt-Backend** (`backend/app.py`)

```python
from backend.services.query_service import QueryService
from backend.api import api_router

app = FastAPI(
    title="VERITAS Unified Backend",
    version="4.0.0",
    lifespan=lifespan
)

# Mount API Router
app.include_router(api_router)
```

**Features:**
- UDS3 v2.0.0 Integration
- Intelligent Pipeline
- Streaming Progress
- Unified Response Model
- IEEE Citations (35+ Felder)

---

## 📦 Vorteile

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| **Backend-Dateien** | 5 verschiedene | 1 konsolidierte |
| **Response-Formate** | 3-4 unterschiedliche | 1 Unified Model |
| **Source-Felder** | 5-10 Felder | 35+ IEEE-Felder |
| **Frontend-Parsing** | 4 verschiedene Strukturen | 1 einheitliche |
| **API-Ordner** | Verschachtelt (`v3/`) | Flach |
| **Dateinamen** | Lang (`veritas_api_agent_...`) | Kurz (`orchestrator.py`) |

---

## 🔄 Migration Status

### ✅ Phase 1: Strukturieren (COMPLETE)

- [x] `backend/models/response.py` - UnifiedResponse
- [x] `backend/models/request.py` - Request Models
- [x] `backend/models/enums.py` - Shared Enums
- [x] `backend/services/query_service.py` - Business Logic
- [x] `backend/api/query_router.py` - Query Endpoints
- [x] `backend/api/agent_router.py` - Agent Endpoints
- [x] `backend/api/system_router.py` - System Endpoints
- [x] `backend/api/__init__.py` - Router Export
- [x] `backend/app.py` - Konsolidiertes Backend

### ⏳ Phase 2: Testen (TODO)

- [ ] Backend starten: `python backend/app.py`
- [ ] Health Check: `GET /api/system/health`
- [ ] Test Query: `POST /api/query` (mode="rag")
- [ ] Frontend-Integration testen
- [ ] IEEE Citations im UI verifizieren

### ⏳ Phase 3: Cleanup (TODO)

- [ ] Alte Backend-Dateien nach `backup/` verschieben
- [ ] Agent-Dateien umbenennen (kürzen)
- [ ] `start_backend.py` anpassen
- [ ] Dokumentation aktualisieren

---

## 🧪 Testing

### Backend starten:

```powershell
# Direkt
python backend/app.py

# Oder via start_backend.py (nach Anpassung)
python start_backend.py
```

### Test Endpoints:

```bash
# Health Check
curl http://localhost:5000/api/system/health

# System Info
curl http://localhost:5000/api/system/info

# RAG Query
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was regelt das BImSchG?",
    "mode": "rag",
    "model": "llama3.2"
  }'
```

### Expected Response:

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
      "similarity_score": 0.92,
      "rerank_score": 0.95,
      "impact": "High",
      "relevance": "Very High",
      "rechtsgebiet": "Umweltrecht"
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

## 📝 Nächste Schritte

1. **Backend testen:**
   ```powershell
   python backend/app.py
   ```

2. **API testen:**
   ```powershell
   curl http://localhost:5000/api/system/health
   ```

3. **Frontend anpassen:**
   - Nur noch `/api/query` verwenden
   - UnifiedResponse-Format parsen
   - IEEE Citations (35+ Felder) anzeigen

4. **Alte Dateien aufräumen:**
   ```powershell
   # Backup erstellen
   New-Item -ItemType Directory -Path "backup_20251019"
   Move-Item backend/api/veritas_api_backend*.py backup_20251019/
   ```

5. **Agents umbenennen:**
   - `veritas_api_agent_orchestrator.py` → `orchestrator.py`
   - `veritas_api_agent_registry.py` → `registry.py`
   - `veritas_intelligent_pipeline.py` → `pipeline.py`

---

## 🎯 Erfolg-Kriterien

- [x] **Ein Backend** statt 5 verschiedene
- [x] **Ein Response-Format** statt 4 verschiedene
- [x] **IEEE Citations** mit 35+ Feldern
- [ ] **Frontend** zeigt Citations korrekt an
- [ ] **Alle Modi** funktionieren (RAG, Hybrid, Streaming, Agent, Ask)
- [ ] **Mock-Fallback** funktioniert ohne UDS3
- [ ] **Tests** erfolgreich

---

## 📚 Dokumentation

- **API Docs:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc
- **Health:** http://localhost:5000/api/system/health
- **Info:** http://localhost:5000/api/system/info

---

**Status:** ✅ **Phase 1 Complete - Ready for Testing!**
