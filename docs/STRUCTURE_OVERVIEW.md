# VERITAS Backend v4.0.0 - Struktur-Übersicht

## 📁 Neue Ordnerstruktur (Flach & Konsolidiert)

```
backend/
│
├── backend.py                        # 🎯 HAUPT-BACKEND (385 Zeilen)
│   ├── UDS3 v2.0.0 Integration
│   ├── Intelligent Pipeline Integration
│   ├── Streaming Progress System
│   ├── QueryService Initialization
│   └── FastAPI App mit Lifespan
│
├── models/                           # 🎨 Unified Data Models
│   ├── __init__.py                  # Model Exports
│   ├── response.py                  # 🏆 UnifiedResponse (250 Zeilen)
│   │   ├── UnifiedSourceMetadata    # IEEE Citations (35+ Felder)
│   │   ├── UnifiedResponseMetadata  # Processing Details
│   │   └── UnifiedResponse          # Main Response Model
│   │
│   ├── request.py                   # Request Models (180 Zeilen)
│   │   ├── UnifiedQueryRequest      # Basis Query
│   │   ├── AgentQueryRequest        # Agent-spezifisch
│   │   ├── StreamingQueryRequest    # Streaming-spezifisch
│   │   ├── HybridSearchRequest      # Hybrid Search
│   │   └── SimpleAskRequest         # Simple Ask
│   │
│   └── enums.py                     # Shared Enums (95 Zeilen)
│       ├── QueryMode                # rag, hybrid, streaming, agent, ask
│       ├── QueryComplexity          # basic, standard, advanced, expert
│       ├── QueryDomain              # building, environmental, transport, ...
│       ├── SourceType               # document, web, database, api
│       ├── ImpactLevel              # High, Medium, Low
│       └── RelevanceLevel           # Very High, High, Medium, Low
│
├── services/                         # 🔧 Business Logic
│   └── query_service.py             # 🏭 QueryService (350 Zeilen)
│       ├── process_query()          # Main Entry Point
│       ├── _process_rag()           # RAG Processing
│       ├── _process_hybrid()        # Hybrid Search
│       ├── _process_streaming()     # Streaming Processing
│       ├── _process_agent()         # Agent Processing
│       ├── _process_ask()           # Simple Ask
│       ├── _normalize_sources()     # IEEE Normalization
│       └── _generate_mock_response() # Mock Fallback
│
├── api/                             # 🌐 API Layer (FLACH - kein v3/)
│   ├── __init__.py                  # Router Export
│   │   ├── api_router               # Haupt-Router (/api)
│   │   └── get_api_info()          # API Information
│   │
│   ├── query_router.py              # 📝 Query Endpoints (200 Zeilen)
│   │   ├── POST /query              # Unified Query (alle Modi)
│   │   ├── POST /query/ask          # Simple Ask
│   │   ├── POST /query/rag          # RAG Query
│   │   ├── POST /query/hybrid       # Hybrid Search
│   │   └── POST /query/stream       # Streaming Query
│   │
│   ├── agent_router.py              # 🤖 Agent Endpoints (80 Zeilen)
│   │   ├── GET /agent/list          # Liste Agents
│   │   ├── GET /agent/capabilities  # Agent Capabilities
│   │   └── GET /agent/status/{id}   # Agent Status
│   │
│   └── system_router.py             # ⚙️ System Endpoints (140 Zeilen)
│       ├── GET /system/health       # Health Check
│       ├── GET /system/info         # System Info
│       ├── GET /system/capabilities # System Capabilities
│       └── GET /system/modes        # Available Modes
│
├── agents/                          # 🤖 Agent System (bleibt wie ist)
│   ├── veritas_intelligent_pipeline.py
│   ├── veritas_api_agent_orchestrator.py
│   ├── veritas_api_agent_registry.py
│   ├── rag_context_service.py
│   └── ... (weitere Agents)
│
├── orchestration/                   # 🎭 (bleibt wie ist)
├── evaluation/                      # 📊 (bleibt wie ist)
├── monitoring/                      # 📈 (bleibt wie ist)
└── prompts/                         # 💬 (bleibt wie ist)
```

---

## 🔄 Datenfluss

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Streamlit/React)                                     │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ POST /api/query { query, mode, model }
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  backend/api/query_router.py                                    │
│  ├─ unified_query()                                             │
│  └─ Depends(get_query_service)                                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  backend/services/query_service.py                              │
│  ├─ QueryService.process_query(request)                         │
│  │  ├─ Route by mode:                                           │
│  │  │  ├─ rag      → _process_rag()                             │
│  │  │  ├─ hybrid   → _process_hybrid()                          │
│  │  │  ├─ streaming→ _process_streaming()                       │
│  │  │  ├─ agent    → _process_agent()                           │
│  │  │  └─ ask      → _process_ask()                             │
│  │  │                                                            │
│  │  ├─ Get results from:                                        │
│  │  │  ├─ IntelligentMultiAgentPipeline (RAG)                   │
│  │  │  ├─ HybridSearchService (Hybrid)                          │
│  │  │  ├─ StreamingService (Streaming)                          │
│  │  │  └─ Mock Fallback                                         │
│  │  │                                                            │
│  │  └─ _normalize_sources() → IEEE Standard (35+ Felder)        │
│  │                                                               │
│  └─ Return UnifiedResponse                                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  UnifiedResponse (backend/models/response.py)                   │
│  ├─ content: str (Markdown mit [1], [2], [3])                   │
│  ├─ sources: List[UnifiedSourceMetadata]                        │
│  │  └─ IEEE Citations (35+ Felder):                             │
│  │     ├─ id, title, type (Basis)                               │
│  │     ├─ authors, ieee_citation, year, publisher (IEEE)        │
│  │     ├─ similarity_score, rerank_score, quality_score (Scores)│
│  │     ├─ rechtsgebiet, behörde, aktenzeichen (Legal)           │
│  │     └─ impact, relevance (Assessment)                        │
│  ├─ metadata: UnifiedResponseMetadata                           │
│  │  ├─ model, mode, duration, tokens_used                       │
│  │  ├─ sources_count, complexity, domain                        │
│  │  ├─ agents_involved, search_method                           │
│  │  └─ quality_score, confidence                                │
│  ├─ session_id: str                                             │
│  └─ timestamp: datetime                                         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Frontend Display                                               │
│  ├─ Render content (Markdown mit Citations)                     │
│  ├─ Display sources (IEEE Citations mit allen Feldern)          │
│  │  └─ [1] Bundes-Immissionsschutzgesetz                        │
│  │     ├─ IEEE: "Deutscher Bundestag, 'BImSchG', ..."           │
│  │     ├─ Score: 0.92 | Quality: 0.90                           │
│  │     ├─ Impact: High | Relevance: Very High                   │
│  │     └─ Rechtsgebiet: Umweltrecht                             │
│  └─ Show metadata (Model, Duration, Agents)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Query-Modi

```
┌────────────┬──────────────────┬─────────────────────────────────┐
│ Mode       │ Endpoint         │ Features                        │
├────────────┼──────────────────┼─────────────────────────────────┤
│ rag        │ /api/query       │ • UDS3 Vector Search            │
│            │ /api/query/rag   │ • Intelligent Pipeline          │
│            │                  │ • Multi-Agent Orchestration     │
│            │                  │ • IEEE Citations                │
├────────────┼──────────────────┼─────────────────────────────────┤
│ hybrid     │ /api/query       │ • BM25 Keyword Search           │
│            │ /api/query/hybrid│ • Dense Vector Search           │
│            │                  │ • RRF Fusion                    │
│            │                  │ • Re-Ranking                    │
├────────────┼──────────────────┼─────────────────────────────────┤
│ streaming  │ /api/query       │ • Real-time Progress Updates    │
│            │ /api/query/stream│ • SSE (Server-Sent Events)      │
│            │                  │ • Intermediate Results          │
│            │                  │ • LLM Deep-thinking             │
├────────────┼──────────────────┼─────────────────────────────────┤
│ agent      │ /api/query       │ • Multi-Agent Pipeline          │
│            │                  │ • External APIs (EU LEX, etc.)  │
│            │                  │ • Quality Assessment            │
│            │                  │ • Agent Result Details          │
├────────────┼──────────────────┼─────────────────────────────────┤
│ ask        │ /api/query       │ • Direct LLM Call               │
│            │ /api/query/ask   │ • No RAG/Retrieval              │
│            │                  │ • Fast Response                 │
│            │                  │ • Simple Answers                │
└────────────┴──────────────────┴─────────────────────────────────┘
```

**Alle Modi → UnifiedResponse mit IEEE Citations!**

---

## 🏆 IEEE Citations (35+ Felder)

```json
{
  "id": "1",                        // ✅ Numeric ID (1, 2, 3 NOT "src_1")
  "title": "Bundes-Immissionsschutzgesetz",
  "type": "document",

  // IEEE Extended (✨ 30+ zusätzliche Felder via extra="allow")
  "authors": "Deutscher Bundestag",
  "ieee_citation": "Deutscher Bundestag, 'Bundes-Immissionsschutzgesetz', BGBl. I S. 1193, 2024.",
  "date": "2024-03-15",
  "year": 2024,
  "publisher": "Bundesanzeiger Verlag",
  "original_source": "BGBl. I",

  // Scoring
  "similarity_score": 0.92,
  "rerank_score": 0.95,
  "quality_score": 0.90,
  "score": 0.93,
  "confidence": 0.91,

  // Legal Domain
  "rechtsgebiet": "Umweltrecht",
  "behörde": "Bundesumweltministerium",
  "aktenzeichen": null,
  "gericht": null,
  "normtyp": "Gesetz",
  "fundstelle": "BGBl. I S. 1193",

  // Assessment
  "impact": "High",
  "relevance": "Very High",

  // Agent Info
  "agent": "document_retrieval",

  // ... weitere 10+ Felder möglich
}
```

---

## 📊 Komponenten-Übersicht

### Backend Core
- **backend.py** - 385 Zeilen - FastAPI App mit Lifecycle
- **Total Lines:** ~1500 (Models + Services + API)

### Models (Shared)
- **response.py** - 250 Zeilen - UnifiedResponse + IEEE Citations
- **request.py** - 180 Zeilen - Request Models
- **enums.py** - 95 Zeilen - Shared Enumerations

### Services (Business Logic)
- **query_service.py** - 350 Zeilen - Query Processing

### API (Routes)
- **query_router.py** - 200 Zeilen - 5 Endpoints
- **agent_router.py** - 80 Zeilen - 3 Endpoints
- **system_router.py** - 140 Zeilen - 4 Endpoints

---

## ✅ Erfolg-Kriterien

- [x] **Ein Backend** (`backend.py`) statt 5
- [x] **Ein Response-Model** (`UnifiedResponse`) statt 4
- [x] **Flache API-Struktur** (`backend/api/`) statt `backend/api/v3/`
- [x] **IEEE Citations** (35+ Felder) überall
- [x] **Keine Syntax-Errors** (✅ Verified)
- [ ] **Backend startet** ohne Fehler
- [ ] **Tests erfolgreich** (Health, Query, Frontend)
- [ ] **Frontend zeigt Citations** korrekt an

---

**Status:** ✅ **Phase 1 Complete - Ready for Testing!**

**Nächste Schritte:**
1. Backend starten: `python start_backend.py`
2. Health Check: `curl http://localhost:5000/api/system/health`
3. Test Query: Siehe `docs/QUICK_START.md`
