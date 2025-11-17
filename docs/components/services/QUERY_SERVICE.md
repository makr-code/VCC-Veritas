# Query Service

**Version:** 1.0  
**Status:** ✅ STABLE  
**Zuletzt aktualisiert:** 17. November 2025  
**Quellcode:** `backend/services/query_service.py` (726 LOC)

---

## 📋 Übersicht

Der **QueryService** ist die zentrale Business-Logic-Komponente für Query-Processing in VERITAS. Er orchestriert alle Query-Typen (RAG, Hybrid Search, Streaming, Agent, Ask) und liefert konsistent strukturierte UnifiedResponse-Objekte mit IEEE-konformen Citations.

**Zweck:** Einheitliche Query-Processing-Pipeline für alle Anfrage-Modi mit automatischer Mode-Erkennung, Multi-Service-Orchestrierung und standardisierten Responses.

**Kernfunktionen:**
- **Unified Query Processing:** Eine Methode für alle Query-Typen
- **Multi-Mode Support:** RAG, Hybrid, Streaming, Agent, Ask
- **Service-Orchestrierung:** Koordiniert RAG, Reranker, Pipeline, UDS3
- **IEEE Citations:** Automatische Citation-Generierung (35+ Felder)
- **Source-Normalisierung:** Einheitliche Source-Metadaten
- **Error-Handling:** Graceful Degradation mit Error-Responses
- **Performance-Tracking:** Duration, Token-Usage, Quality-Metrics
- **Streaming-Support:** Progressive Query-Updates
- **Confidence-Scoring:** Automatic Confidence-Berechnung
- **JSON-Metadata-Extraction:** Next-Steps, Related-Topics

---

## 🏗️ Architektur

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│                    QueryService                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Mode Router    │  │ RAG Service    │  │ Reranker     │  │
│  │                │  │ (Hybrid)       │  │ Service      │  │
│  │ - RAG          │  │                │  │              │  │
│  │ - Hybrid       │  │ - BM25         │  │ - Semantic   │  │
│  │ - Streaming    │  │ - Dense        │  │ - Combined   │  │
│  │ - Agent        │  │ - RRF          │  │              │  │
│  │ - Ask          │  │                │  │              │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                              │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │ Pipeline       │  │ UDS3           │  │ Streaming    │  │
│  │ (Multi-Agent)  │  │ (PolyglotMgr)  │  │ Service      │  │
│  └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Response Builder                          │    │
│  │  - Source Normalization (IEEE)                      │    │
│  │  - Metadata Aggregation                             │    │
│  │  - Citation Generation                              │    │
│  │  - Confidence Calculation                           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Query Processing Flow

```
1. Receive UnifiedQueryRequest
   ↓
2. Route by Mode
   │
   ├─ RAG → Intelligent Pipeline
   ├─ HYBRID → RAG Service (BM25+Dense+RRF)
   ├─ STREAMING → Streaming Service + Pipeline
   ├─ AGENT → Multi-Agent Pipeline
   └─ ASK → Direct LLM (fallback to RAG)
   ↓
3. Service Processing
   │
   ├─ Document Retrieval (UDS3)
   ├─ Re-Ranking (RerankerService)
   ├─ LLM Response Generation
   └─ Agent Orchestration
   ↓
4. Response Building
   │
   ├─ Normalize Sources (IEEE-Standard)
   ├─ Build Citations
   ├─ Calculate Confidence
   ├─ Extract JSON Metadata
   └─ Aggregate Metrics
   ↓
5. Return UnifiedResponse
```

### Mode-Routing-Logik

```python
QueryMode.RAG       → _process_rag()      → IntelligentPipeline
QueryMode.HYBRID    → _process_hybrid()   → RAGService (BM25+Dense+RRF)
QueryMode.STREAMING → _process_streaming() → StreamingService
QueryMode.AGENT     → _process_agent()    → Multi-Agent Pipeline
QueryMode.ASK       → _process_ask()      → Direct LLM
```

---

## 📚 API-Referenz

### Hauptklasse: `QueryService`

#### Konstruktor

```python
def __init__(
    self,
    uds3=None,
    pipeline=None,
    streaming=None
)
```

**Parameter:**
- `uds3` (Optional): UDS3 PolyglotManager (v2.0.0)
- `pipeline` (Optional): IntelligentMultiAgentPipeline
- `streaming` (Optional): StreamingService

**Initialisierung:**
```python
from backend.services.query_service import QueryService

# Mit allen Services
query_service = QueryService(
    uds3=polyglot_manager,
    pipeline=intelligent_pipeline,
    streaming=streaming_service
)

# Minimal (Mock-Mode)
query_service = QueryService()
```

**Auto-Initialisierung:**
Der QueryService initialisiert automatisch:
- `RAGService` (wenn UDS3 verfügbar)
- `RerankerService` (immer, mit Fallback)

#### Haupt-Methode

##### `async process_query(request) -> UnifiedResponse`

🎯 **EINE Methode für ALLE Query-Typen**

Verarbeitet jede Query und liefert konsistente UnifiedResponse.

**Parameter:**
- `request` (UnifiedQueryRequest): Query-Request mit:
  - `query` (str): Query-Text
  - `mode` (QueryMode): RAG, HYBRID, STREAMING, AGENT, ASK
  - `model` (str): LLM-Model (z.B. "llama3.1:8b")
  - `temperature` (float): LLM-Temperature
  - `max_tokens` (int): Max Response-Tokens
  - `session_id` (Optional[str]): Session-ID
  - Weitere mode-spezifische Parameter

**Returns:** `UnifiedResponse` mit:
- `content` (str): Antwort-Text
- `sources` (List[UnifiedSourceMetadata]): IEEE-Citations
- `metadata` (UnifiedResponseMetadata): Metrics, Timing, etc.
- `session_id` (str): Session-Tracking
- `agent_results` (Optional): Agent-Ergebnisse
- `external_data` (Optional): Externe Daten
- `quality_metrics` (Optional): Qualitäts-Metriken
- `processing_details` (Dict): Verarbeitungs-Details

**Beispiel:**
```python
from backend.models.request import UnifiedQueryRequest
from backend.models.enums import QueryMode

# RAG Query
request = UnifiedQueryRequest(
    query="Was sind die Immissionsschutz-Grenzwerte?",
    mode=QueryMode.RAG,
    model="llama3.1:8b",
    temperature=0.7,
    max_tokens=1000
)

response = await query_service.process_query(request)

print(f"Content: {response.content}")
print(f"Sources: {len(response.sources)}")
print(f"Duration: {response.metadata.duration:.2f}s")
```

#### Query-Modes

##### RAG Mode

**Verwendung:** Standard-Retrieval-Augmented-Generation

**Processing:** IntelligentPipeline mit Multi-Agent-Orchestration

**Beispiel:**
```python
request = UnifiedQueryRequest(
    query="Bauantrag-Verfahren",
    mode=QueryMode.RAG,
    model="llama3.1:8b"
)

response = await query_service.process_query(request)
```

##### Hybrid Mode

**Verwendung:** Advanced Search mit BM25 + Dense + RRF

**Processing:** RAGService mit Multi-Method-Search und Re-Ranking

**Features:**
- BM25 (Keyword-Search)
- Dense (Vector-Search)
- RRF (Reciprocal Rank Fusion)
- Semantic Re-Ranking

**Beispiel:**
```python
request = UnifiedQueryRequest(
    query="Grenzwerte Luftqualität",
    mode=QueryMode.HYBRID,
    model="llama3.1:8b",
    # Hybrid-spezifisch:
    top_k=20,
    rerank_top_n=10
)

response = await query_service.process_query(request)
print(f"Search Method: {response.metadata.search_method}")
print(f"Rerank Applied: {response.metadata.rerank_applied}")
```

##### Streaming Mode

**Verwendung:** Progressive Response-Updates

**Processing:** StreamingService mit Real-Time-Updates

**Beispiel:**
```python
request = UnifiedQueryRequest(
    query="Komplexe Analyse",
    mode=QueryMode.STREAMING,
    model="llama3.1:8b",
    session_id="session_123"
)

response = await query_service.process_query(request)
# StreamingService emittiert Events während Processing
```

##### Agent Mode

**Verwendung:** Multi-Agent-Pipeline mit Spezialisierung

**Processing:** Full Multi-Agent-Orchestration

**Beispiel:**
```python
request = UnifiedQueryRequest(
    query="Technische Analyse",
    mode=QueryMode.AGENT,
    model="llama3.1:8b"
)

response = await query_service.process_query(request)
print(f"Agents: {response.metadata.agents_involved}")
```

##### Ask Mode

**Verwendung:** Direct LLM (kein RAG)

**Processing:** Fallback zu RAG-Mode (mit Pipeline)

**Beispiel:**
```python
request = UnifiedQueryRequest(
    query="Erkläre ein Konzept",
    mode=QueryMode.ASK,
    model="llama3.1:8b"
)

response = await query_service.process_query(request)
```

#### Interne Methoden

##### `_normalize_sources(sources) -> List[UnifiedSourceMetadata]`

Normalisiert Sources auf IEEE-Standard (35+ Felder).

**Features:**
- Funktioniert für RAG, Hybrid, Agent, Mock
- Generiert fehlende IDs, Titles, Types
- Extra="allow" für Custom-Fields

**Beispiel:**
```python
sources = [
    {"title": "Dokument 1", "content": "...", "score": 0.95},
    {"title": "Dokument 2", "url": "https://...", "score": 0.87}
]

normalized = query_service._normalize_sources(sources)
# → List[UnifiedSourceMetadata] mit IEEE-Standard-Feldern
```

##### `_build_ieee_citation(metadata) -> str`

Generiert IEEE-konforme Citation.

**Format:** `[ID] Titel, Jahr. URL`

**Beispiel:**
```python
citation = query_service._build_ieee_citation(source_metadata)
# → "[1] Bauantrag-Verfahren, 2025. https://..."
```

##### `_calculate_confidence(hybrid_result) -> float`

Berechnet Confidence-Score (0.0-1.0) aus Hybrid-Search-Results.

**Faktoren:**
- RRF-Scores
- Source-Count
- Score-Verteilung

**Beispiel:**
```python
confidence = query_service._calculate_confidence(hybrid_result)
# → 0.87 (High confidence)
```

##### `_generate_session_id() -> str`

Generiert eindeutige Session-ID.

**Format:** UUID4

**Beispiel:**
```python
session_id = query_service._generate_session_id()
# → "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

---

## ⚙️ Konfiguration

### Service-Dependencies

**Erforderlich:**
- `UnifiedQueryRequest`, `UnifiedResponse` Models

**Optional (mit Fallback):**
- `UDS3 PolyglotManager` - Für Document-Retrieval (Fallback: Mock)
- `IntelligentPipeline` - Für Multi-Agent (Fallback: Mock)
- `StreamingService` - Für Progressive-Updates (Fallback: Disabled)
- `RAGService` - Für Hybrid-Search (Auto-Init, Fallback: RAG-Mode)
- `RerankerService` - Für Semantic-Reranking (Auto-Init, Fallback: No-Rerank)

### Auto-Initialization

```python
# QueryService initialisiert automatisch:
if uds3:
    self.rag_service = RAGService()  # Auto
    
self.reranker_service = RerankerService(
    model_name="llama3.1:8b",
    scoring_mode=ScoringMode.COMBINED,
    temperature=0.1
)  # Immer
```

### Configuration-Pattern

```python
# Minimal (Mock-Mode - für Testing)
query_service = QueryService()

# Standard (mit UDS3)
query_service = QueryService(uds3=polyglot_manager)

# Full-Featured (mit allen Services)
query_service = QueryService(
    uds3=polyglot_manager,
    pipeline=intelligent_pipeline,
    streaming=streaming_service
)
```

---

## 💡 Verwendungsbeispiele

### Beispiel 1: Simple RAG Query

```python
from backend.services.query_service import QueryService
from backend.models.request import UnifiedQueryRequest
from backend.models.enums import QueryMode

# Setup
query_service = QueryService(uds3=uds3_manager, pipeline=pipeline)

# RAG Query
request = UnifiedQueryRequest(
    query="Was ist ein Bauantrag?",
    mode=QueryMode.RAG,
    model="llama3.1:8b",
    temperature=0.7,
    max_tokens=500
)

response = await query_service.process_query(request)

print(f"Antwort: {response.content}")
print(f"Quellen: {len(response.sources)}")
print(f"Dauer: {response.metadata.duration:.2f}s")
print(f"Tokens: {response.metadata.tokens_used}")

# Citations
for src in response.sources:
    print(f"  [{src.id}] {src.title}")
```

### Beispiel 2: Hybrid Search mit Re-Ranking

```python
# Hybrid Query (BM25 + Dense + RRF)
request = UnifiedQueryRequest(
    query="Immissionsschutz Grenzwerte Luftqualität",
    mode=QueryMode.HYBRID,
    model="llama3.1:8b",
    top_k=20,  # Retrieve 20 documents
    temperature=0.5
)

response = await query_service.process_query(request)

print(f"Search Method: {response.metadata.search_method}")
# → "HYBRID_BM25_DENSE_RRF"

print(f"Reranked: {response.metadata.rerank_applied}")
# → True

print(f"Confidence: {response.metadata.confidence:.2f}")
# → 0.89

# Top Sources (re-ranked)
for src in response.sources[:5]:
    print(f"[{src.id}] {src.title} (Score: {src.relevance_score:.3f})")
```

### Beispiel 3: Streaming Query mit Progress-Updates

```python
import asyncio

# Setup Streaming Callback
def on_progress(event):
    print(f"[{event.event_type}] {event.message}")

streaming_service = StreamingService(callback=on_progress)

query_service = QueryService(
    uds3=uds3_manager,
    pipeline=pipeline,
    streaming=streaming_service
)

# Streaming Query
request = UnifiedQueryRequest(
    query="Komplexe Verwaltungsanalyse",
    mode=QueryMode.STREAMING,
    model="llama3.1:8b",
    session_id="session_123"
)

response = await query_service.process_query(request)

# Output während Processing:
# [PLAN_STARTED] Starting process...
# [STEP_STARTED] Step 1: Document Search
# [STEP_PROGRESS] Searching... 50%
# [STEP_COMPLETED] Step 1 complete
# [PLAN_COMPLETED] Process complete

print(f"Final Response: {response.content}")
```

### Beispiel 4: Agent Mode mit Multi-Agent-Pipeline

```python
# Agent Query (Multi-Agent-Orchestration)
request = UnifiedQueryRequest(
    query="Technische Standards für Emissionen",
    mode=QueryMode.AGENT,
    model="llama3.1:8b",
    max_tokens=1500
)

response = await query_service.process_query(request)

print(f"Agents verwendet: {response.metadata.agents_involved}")
# → ["RAGAgent", "TechnicalAgent", "ComplianceAgent"]

# Agent-Results
if response.agent_results:
    for agent_id, result in response.agent_results.items():
        print(f"\n{agent_id}:")
        print(f"  Status: {result.get('status')}")
        print(f"  Output: {result.get('output')[:100]}...")
```

### Beispiel 5: Error Handling

```python
# Query mit Error-Handling
request = UnifiedQueryRequest(
    query="Test Query",
    mode=QueryMode.RAG,
    model="llama3.1:8b"
)

try:
    response = await query_service.process_query(request)
    
    if response.metadata.quality_score and response.metadata.quality_score < 0.5:
        print("⚠️ Low quality response")
    
    print(f"Success: {response.content}")
    
except Exception as e:
    print(f"Error: {e}")
    # QueryService returns error as UnifiedResponse
    # (nicht als Exception, außer kritische Fehler)
```

### Beispiel 6: Batch Processing

```python
# Multiple Queries verarbeiten
queries = [
    "Was ist ein Bauantrag?",
    "Immissionsschutz Grenzwerte",
    "Technische Standards"
]

responses = []

for query_text in queries:
    request = UnifiedQueryRequest(
        query=query_text,
        mode=QueryMode.HYBRID,
        model="llama3.1:8b"
    )
    
    response = await query_service.process_query(request)
    responses.append(response)
    
    print(f"Query: {query_text}")
    print(f"  Sources: {len(response.sources)}")
    print(f"  Duration: {response.metadata.duration:.2f}s")
```

---

## 🔧 Troubleshooting

### Problem 1: "RAGService not available"

**Symptom:** Warning-Log beim Start

**Ursache:** UDS3 nicht übergeben oder RAGService-Init fehlgeschlagen

**Lösung:**
```python
# 1. UDS3 übergeben
from backend.uds3.uds3_polyglot_manager import UDS3PolyglotManager

uds3 = UDS3PolyglotManager()
query_service = QueryService(uds3=uds3)

# 2. Falls nicht verfügbar: Fallback zu RAG-Mode
# HYBRID-Queries werden automatisch zu RAG geroutet
```

### Problem 2: Hybrid Search gibt wenig Results

**Symptom:** `len(response.sources) < erwartete Anzahl`

**Ursache:** 
- `top_k` zu klein
- Keine passenden Dokumente
- Re-Ranking filtert zu viele

**Lösung:**
```python
# 1. top_k erhöhen
request = UnifiedQueryRequest(
    query="...",
    mode=QueryMode.HYBRID,
    top_k=50  # statt 20
)

# 2. Re-Ranking-Threshold anpassen
# (erfordert Modification in RAGService)

# 3. Fallback zu RAG wenn Hybrid wenig Results
if len(response.sources) < 5:
    # Retry mit RAG
    request.mode = QueryMode.RAG
    response = await query_service.process_query(request)
```

### Problem 3: Streaming funktioniert nicht

**Symptom:** Keine Progress-Events

**Ursache:**
- StreamingService nicht übergeben
- Callback nicht registriert

**Lösung:**
```python
# 1. StreamingService mit Callback erstellen
def on_progress(event):
    print(f"{event.message}")

streaming = StreamingService(callback=on_progress)

# 2. An QueryService übergeben
query_service = QueryService(
    uds3=uds3,
    pipeline=pipeline,
    streaming=streaming  # Wichtig!
)

# 3. STREAMING-Mode verwenden
request.mode = QueryMode.STREAMING
```

### Problem 4: Low Quality Score

**Symptom:** `response.metadata.quality_score < 0.5`

**Ursache:**
- Wenig relevante Dokumente
- LLM-Hallucination
- Query zu unspezifisch

**Lösung:**
```python
# 1. Query reformulieren
if response.metadata.quality_score < 0.5:
    # Retry mit verbesserter Query
    improved_query = f"Detaillierte Erklärung: {original_query}"
    request.query = improved_query
    response = await query_service.process_query(request)

# 2. Temperature anpassen
request.temperature = 0.3  # Weniger kreativ, mehr faktisch

# 3. Mehr Dokumente abrufen
request.top_k = 30
```

### Problem 5: Langsame Response-Zeit

**Symptom:** `response.metadata.duration > 30s`

**Ursachen:**
- Zu viele Dokumente
- Re-Ranking langsam
- LLM-Response langsam

**Lösung:**
```python
# 1. top_k reduzieren
request.top_k = 10  # statt 20

# 2. max_tokens reduzieren
request.max_tokens = 500  # statt 1500

# 3. Re-Ranking deaktivieren (wenn möglich)
# (erfordert RAGService-Konfiguration)

# 4. Timeout setzen
import asyncio

try:
    response = await asyncio.wait_for(
        query_service.process_query(request),
        timeout=10.0
    )
except asyncio.TimeoutError:
    print("Query timeout!")
```

---

## 🔗 Verwandte Dokumentation

### Dependencies

- **UnifiedResponse Models:** `backend/models/response.py`
- **UnifiedQueryRequest:** `backend/models/request.py`
- **QueryMode Enum:** `backend/models/enums.py`

### Verwandte Services

- **RAGService:** `backend/services/rag_service.py`
  - Dokumentation: `docs/PHASE4_RAG_INTEGRATION.md` (zu konsolidieren)

- **RerankerService:** `backend/services/reranker_service.py`
  - Dokumentation: `docs/HYBRID_SEARCH_RRF_RERANKING_REPORT.md`

- **IntelligentPipeline:** `backend/agents/veritas_intelligent_pipeline.py`
  - Dokumentation: (TODO) `docs/components/agents/INTELLIGENT_PIPELINE.md`

- **Process Executor:** `backend/services/process_executor.py`
  - Dokumentation: `docs/components/services/PROCESS_EXECUTOR.md` ✅

### Architektur-Dokumente

- **UDS3 Integration:** `docs/UDS3_INTEGRATION_COMPLETE.md`
- **Structured Responses:** `docs/STRUCTURED_RESPONSE_ARCHITECTURE.md`
- **API v3:** `docs/API_V3_COMPLETE.md`

---

## 📊 Performance-Charakteristiken

### Response-Time

**Typische Response-Times:**
- RAG (Simple): 3-8 Sekunden
- RAG (Complex): 10-20 Sekunden
- Hybrid (10 docs): 5-10 Sekunden
- Hybrid (50 docs): 15-30 Sekunden
- Streaming: Variable (Progressive)
- Agent: 15-40 Sekunden

**Faktoren:**
- Document-Count (top_k)
- LLM-Model-Größe
- Re-Ranking (ja/nein)
- Agent-Count
- Query-Komplexität

### Token-Usage

**Geschätzte Token-Nutzung:**
- Input-Tokens: 500-2000 (Query + Context)
- Output-Tokens: 200-1500 (Response)
- **Total:** 700-3500 tokens pro Query

**Abhängig von:**
- max_tokens Setting
- Document-Count
- Context-Window-Größe

### Memory-Usage

**Geschätzte Memory-Nutzung:**
- Base QueryService: ~50 MB
- RAGService: ~200 MB
- RerankerService: ~300 MB
- Pipeline (mit Agents): ~500 MB
- **Total (typical):** ~1-1.5 GB

---

## 🧪 Testing

### Unit Tests

```python
# tests/test_query_service.py
import pytest
from backend.services.query_service import QueryService
from backend.models.request import UnifiedQueryRequest
from backend.models.enums import QueryMode

@pytest.mark.asyncio
async def test_rag_query():
    query_service = QueryService()  # Mock-Mode
    
    request = UnifiedQueryRequest(
        query="Test Query",
        mode=QueryMode.RAG,
        model="llama3.1:8b"
    )
    
    response = await query_service.process_query(request)
    
    assert response.content is not None
    assert len(response.sources) >= 0
    assert response.metadata.duration > 0

@pytest.mark.asyncio
async def test_source_normalization():
    query_service = QueryService()
    
    sources = [
        {"title": "Doc 1", "content": "..."},
        {"title": "Doc 2", "url": "https://..."}
    ]
    
    normalized = query_service._normalize_sources(sources)
    
    assert len(normalized) == 2
    assert normalized[0].id is not None
    assert normalized[0].title == "Doc 1"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_hybrid_search_integration():
    # Mit echten Services
    uds3 = UDS3PolyglotManager()
    query_service = QueryService(uds3=uds3)
    
    request = UnifiedQueryRequest(
        query="Immissionsschutz",
        mode=QueryMode.HYBRID,
        model="llama3.1:8b",
        top_k=10
    )
    
    response = await query_service.process_query(request)
    
    assert response.metadata.search_method == "HYBRID"
    assert len(response.sources) > 0
    assert response.metadata.confidence is not None
```

---

## 📝 Changelog

### Version 1.0 (Aktuell)
- Unified Query Processing für alle Modi
- IEEE-Citation-Support (35+ Felder)
- Auto-Initialization (RAG, Reranker)
- Hybrid-Search-Integration
- Streaming-Support
- Confidence-Scoring
- JSON-Metadata-Extraction
- Error-Handling mit Graceful Degradation

---

**Maintainer:** VERITAS Development Team  
**Last Review:** 17. November 2025  
**Next Review:** Q1 2026
