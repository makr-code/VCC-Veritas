# VERITAS RAG Workflow - Vollständige Analyse
## Retrieval-Augmented Generation Ablauf

**Dokument-Version**: 1.0
**Erstellt**: 2025-12-03
**Status**: ✅ Produktionsbereit

---

## 🎯 Executive Summary

Dieses Dokument analysiert den vollständigen Workflow einer Benutzeranfrage im VERITAS System - vom HTTP-Endpoint bis zur finalen Antwort. Es beschreibt alle beteiligten Komponenten, Datenflüsse, Entscheidungspunkte und Qualitätssicherungsmechanismen.

**Kernprinzip**: Eine Benutzeranfrage durchläuft ein **orchestriertes Multi-Agent-System** mit **intelligenter Pipeline**, **polyglotter Datenbank** (UDS3) und **iterativer Qualitätsprüfung**.

---

## 📋 Inhaltsverzeichnis

1. [Architektur-Überblick](#1-architektur-überblick)
2. [Workflow-Phasen](#2-workflow-phasen)
3. [Komponenten-Details](#3-komponenten-details)
4. [Datenfluss-Diagramm](#4-datenfluss-diagramm)
5. [Qualitätssicherung](#5-qualitätssicherung)
6. [Performance-Optimierung](#6-performance-optimierung)
7. [Fehlerbehandlung](#7-fehlerbehandlung)
8. [Beispiel-Ablauf](#8-beispiel-ablauf)

---

## 1. Architektur-Überblick

### 1.1 System-Layer

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER                              │
│  (Frontend, Office Add-in, API-Client, Postman)             │
└─────────────────────────────────────────────────────────────┘
                           │ HTTP POST
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                 │
│  FastAPI Endpoint → Router → Middleware                     │
│  • /api/query (unified)                                      │
│  • /api/query/rag                                           │
│  • /api/query/hybrid                                        │
│  • /api/query/stream                                        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 SERVICE LAYER                                │
│  QueryService → Intelligente Routing-Logik                  │
│  • Mode-Erkennung (RAG, Hybrid, Agent, Ask)                │
│  • Request-Validierung                                       │
│  • Response-Normalisierung (UnifiedResponse)                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              ORCHESTRATION LAYER                             │
│  IntelligentMultiAgentPipeline                              │
│  • Query-Analyse (Complexity, Domain)                       │
│  • Agent-Selektion (bis zu 14 Spezial-Agenten)            │
│  • Parallel Execution (max 5 gleichzeitig)                  │
│  • Result Aggregation                                        │
│  • LLM Commentary (Real-time Fortschritt)                   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  DATA LAYER                                  │
│  UDS3 PolyglotManager (v2.0.0)                              │
│  ┌──────────┬──────────┬────────────┬──────────┐          │
│  │ ChromaDB │  Neo4j   │ PostgreSQL │ CouchDB  │          │
│  │ (Vector) │ (Graph)  │(Relational)│  (File)  │          │
│  │ Semantic │Knowledge │ Structured │ Original │          │
│  │  Search  │   Graph  │    Data    │   Docs   │          │
│  └──────────┴──────────┴────────────┴──────────┘          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   LLM LAYER                                  │
│  • Ollama (llama3.1:8b, mistral, qwen2.5)                  │
│  • vLLM (Production-optimiert)                              │
│  • OpenAI API (optional)                                     │
│  • Answer Generation, Re-Ranking, Commentary                │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Design Patterns

| Pattern | Komponente | Zweck |
|---------|-----------|-------|
| **Facade** | QueryService | Vereinfachte API für komplexes Subsystem |
| **Strategy** | Query Mode Router | Austauschbare Algorithmen (RAG, Hybrid, Agent) |
| **Observer** | Streaming Progress | Event-basierte Progress-Updates |
| **Builder** | Pipeline Request | Fluent API für komplexe Objekte |
| **Adapter** | UDS3 Wrapper | Einheitliche Schnittstelle zu Polyglot-DB |
| **Template Method** | Agent Execution | Fester Ablauf, variable Schritte |
| **Chain of Responsibility** | Agent Pipeline | Sequentielle Verarbeitung |
| **Factory** | Agent Creation | Dynamische Agenten-Instanziierung |

---

## 2. Workflow-Phasen

### Phase 1: Request Reception (API Layer)

**Eintrittspunkt**: `backend/app.py` → FastAPI Application

```python
# 1. HTTP Request kommt an
POST /api/query HTTP/1.1
Content-Type: application/json

{
  "query": "Was sind die Anforderungen für einen Bauantrag im Außenbereich?",
  "mode": "rag",
  "model": "llama3.1:8b",
  "temperature": 0.1,
  "top_k": 10
}
```

**Beteiligte Komponenten**:
- **FastAPI App** (`backend/app.py`)
- **CORS Middleware** (Cross-Origin Request Handling)
- **TLS Middleware** (HTTPS Enforcement, optional)
- **Query Router** (`backend/api/query_router.py`)

**Ablauf**:
```python
1. FastAPI empfängt POST /api/query
2. CORS Middleware prüft Origin
3. Pydantic validiert Request (UnifiedQueryRequest)
4. Router leitet an unified_query() weiter
5. Dependency Injection: get_query_service(request)
   → Holt QueryService aus app.state
```

**Datenübergabe**:
- **Input**: HTTP JSON Body
- **Output**: `UnifiedQueryRequest` (Pydantic Model)

---

### Phase 2: Request Processing (Service Layer)

**Komponente**: `backend/services/query_service.py` → `QueryService`

**Ablauf**:
```python
async def process_query(request: UnifiedQueryRequest) -> UnifiedResponse:
    # 1. Session-ID generieren (falls nicht vorhanden)
    session_id = request.session_id or uuid.uuid4()

    # 2. Mode-basiertes Routing
    if request.mode == QueryMode.RAG:
        result = await self._process_rag(request)
    elif request.mode == QueryMode.HYBRID:
        result = await self._process_hybrid(request)
    elif request.mode == QueryMode.AGENT:
        result = await self._process_agent(request)
    elif request.mode == QueryMode.ASK:
        result = await self._process_ask(request)

    # 3. Normalisierung zu UnifiedResponse
    response = UnifiedResponse(
        content=result["content"],
        sources=self._normalize_sources(result["sources"]),
        metadata=UnifiedResponseMetadata(...)
    )

    return response
```

**Entscheidungslogik**:

| Mode | Methode | Beschreibung |
|------|---------|--------------|
| `RAG` | `_process_rag()` | UDS3 Retrieval + Pipeline + LLM |
| `HYBRID` | `_process_hybrid()` | Multi-DB Fusion (Vector + Graph + Relational) |
| `AGENT` | `_process_agent()` | Multi-Agent Pipeline |
| `ASK` | `_process_ask()` | Direct LLM (ohne Retrieval) |
| `STREAMING` | `_process_streaming()` | Real-time Progress Updates |

**Datenübergabe**:
- **Input**: `UnifiedQueryRequest`
- **Output**: `UnifiedResponse` (IEEE-Standard, 35+ Metadaten-Felder)

---

### Phase 3: Intelligent Pipeline Execution (Orchestration Layer)

**Komponente**: `backend/core/pipeline/intelligent_pipeline.py` → `IntelligentMultiAgentPipeline`

#### 3.1 Query Analysis

```python
# Schritt 1: Komplexität analysieren
complexity = self._analyze_complexity(query_text)
# → SIMPLE, MEDIUM, COMPLEX, EXPERT

# Schritt 2: Domain erkennen
domain = self._detect_domain(query_text)
# → BAURECHT, UMWELTRECHT, VERKEHR, GENERAL, etc.

# Schritt 3: Intent klassifizieren
intent = self._classify_intent(query_text)
# → INFORMATION, ANALYSIS, COMPARISON, LEGAL_ADVICE
```

**Algorithmen**:
- **Complexity**: Keyword-Analyse (BauGB, BImSchG → COMPLEX)
- **Domain**: Pattern Matching + Entity Recognition
- **Intent**: LLM-basierte Klassifikation (Few-Shot)

#### 3.2 Agent Selection

```python
# Dynamische Agent-Auswahl basierend auf Query-Eigenschaften
selected_agents = self._select_agents(
    complexity=complexity,
    domain=domain,
    intent=intent
)

# Beispiel-Output:
# {
#   "primary": ["rechtsrecherche", "baurecht"],
#   "secondary": ["environmental", "database"],
#   "optional": ["wikipedia", "weather"]
# }
```

**Verfügbare Agenten** (14 Spezial-Agenten):

| Agent | Domain | Capabilities |
|-------|--------|--------------|
| `rechtsrecherche` | Legal | BauGB, BImSchG, VwVfG Recherche |
| `environmental` | Environment | Umweltdaten-APIs (Wetter, Emissionen) |
| `baurecht` | Construction | Baugenehmigungsverfahren |
| `immissionsschutz` | Emissions | Immissionsschutz-Recht |
| `naturschutz` | Nature | Naturschutzgebiete, FFH |
| `verkehr` | Traffic | Verkehrsplanung, Lärmschutz |
| `database` | Data | SQL-Abfragen auf PostgreSQL |
| `financial` | Finance | Kosten-Nutzen-Analysen |
| `social` | Social | Bürgerbeteiligung |
| `wikipedia` | General | Allgemeinwissen |
| `dwd_weather` | Weather | DWD Wetterdaten |
| `technical_standards` | Standards | DIN, VDI, TA Luft |
| `verwaltungsprozess` | Admin | Verwaltungsverfahren |
| `genehmigung` | Approval | Genehmigungsverfahren |

#### 3.3 RAG Context Retrieval

```python
# UDS3 Polyglot Retrieval (parallel)
rag_context = await self.rag_service.get_context(
    query=query_text,
    options=RAGQueryOptions(
        top_k=10,
        enable_vector=True,
        enable_graph=True,
        enable_relational=True
    )
)

# Result Structure:
# {
#   "vector_results": [...],  # ChromaDB Semantic Search
#   "graph_results": [...],   # Neo4j Knowledge Graph
#   "relational_results": [...],  # PostgreSQL Structured Data
#   "combined_sources": [...]  # RRF Fusion
# }
```

**Retrieval-Strategien**:

1. **Vector Search (ChromaDB)**:
   - Embedding: `sentence-transformers/all-MiniLM-L6-v2`
   - Similarity: Cosine Distance
   - Index: HNSW (Hierarchical Navigable Small World)

2. **Graph Traversal (Neo4j)**:
   - Cypher Queries für Entity-Relationships
   - Beispiel: `MATCH (p:Paragraph)-[:REFERENCES]->(l:Law)`

3. **Relational Queries (PostgreSQL)**:
   - Metadata-Filter (Datum, Autor, Quelle)
   - Fulltext-Search (GIN Index)

#### 3.4 Parallel Agent Execution

```python
# Parallele Ausführung (max 5 gleichzeitig)
agent_tasks = []
for agent_type in selected_agents["primary"]:
    task = self._execute_agent(
        agent_type=agent_type,
        query=query_text,
        rag_context=rag_context
    )
    agent_tasks.append(task)

# Await all mit Timeout (60s default)
agent_results = await asyncio.gather(*agent_tasks, return_exceptions=True)
```

**Agent-Execution-Flow**:

```
┌────────────────────────────────────────────────────────┐
│              PARALLEL AGENT EXECUTION                  │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Rechts-      │  │ Bau-         │  │ Database    │ │
│  │ recherche    │  │ recht        │  │ Agent       │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘ │
│         │                  │                 │        │
│         │    ┌─────────────┴─────┐          │        │
│         │    │  Environmental    │          │        │
│         │    │  Agent            │          │        │
│         │    └─────────┬─────────┘          │        │
│         │              │                    │        │
│         └──────────────┴────────────────────┘        │
│                        │                              │
│                   AGGREGATOR                          │
│                        │                              │
└────────────────────────┼──────────────────────────────┘
                         ▼
                   Combined Result
```

**LLM Commentary** (Real-time Updates):

```python
# Während Ausführung: Streaming Progress
await streaming.emit_progress(
    session_id=session_id,
    stage="agent_execution",
    message="🔍 Rechtsrecherche-Agent durchsucht BauGB §35...",
    progress=0.3
)
```

#### 3.5 Result Aggregation

```python
# LLM-basierte Synthese (llama3.1:8b)
final_response = await self._synthesize_results(
    query=query_text,
    agent_results=agent_results,
    rag_context=rag_context,
    model=request.model
)

# Prompt Template:
# """
# Du bist ein Experte für Verwaltungsrecht. Synthes synthesiere die folgenden
# Agent-Ergebnisse zu einer kohärenten Antwort:
#
# QUERY: {query}
#
# RECHTSRECHERCHE-AGENT:
# {rechtsrecherche_result}
#
# BAURECHT-AGENT:
# {baurecht_result}
#
# ENVIRONMENTAL-AGENT:
# {environmental_result}
#
# Erstelle eine präzise, strukturierte Antwort mit:
# 1. Zusammenfassung
# 2. Rechtsgrundlagen (mit IEEE-Citations)
# 3. Praktische Hinweise
# 4. Nächste Schritte
# """
```

**Aggregation-Strategien**:

| Strategie | Beschreibung | Use Case |
|-----------|--------------|----------|
| **Weighted Voting** | Gewichtete Abstimmung nach Agent-Priority | Widersprüchliche Ergebnisse |
| **Consensus** | Nur übereinstimmende Fakten | Hohe Sicherheit |
| **Priority-based** | Höchst-priorisierter Agent gewinnt | Klare Hierarchie |
| **LLM Synthesis** | LLM generiert kohärente Antwort | Komplexe Queries (Default) |

---

### Phase 4: Quality Assurance

**Komponenten**:
- **Citation Extractor** (`backend/utils/json_extractor.py`)
- **Reranking Service** (`backend/services/reranker_service.py`)
- **Quality Gate** (Pipeline-integriert)

#### 4.1 Citation Extraction

```python
# IEEE-Standard Citations extrahieren
citations = self._extract_citations(final_response)

# Format:
# {
#   "document_id": "bauGB_35",
#   "title": "§ 35 BauGB - Bauen im Außenbereich",
#   "authors": ["Gesetzgeber"],
#   "publication_date": "2023-01-01",
#   "source_type": "legal_code",
#   "url": "https://...",
#   "page_range": "35-38",
#   "relevance_score": 0.92,
#   "confidence": 0.95,
#   ... // 30+ weitere IEEE-Felder
# }
```

#### 4.2 Semantic Re-Ranking

```python
# LLM-basiertes Re-Ranking der Sources
reranked_sources = await self.reranker_service.rerank(
    query=query_text,
    sources=rag_context["combined_sources"],
    scoring_mode=ScoringMode.COMBINED  # Relevance + Informativeness
)

# Scoring:
# - Relevance: Wie gut passt Source zur Query? (0-1)
# - Informativeness: Wie informativ ist die Source? (0-1)
# - Combined: (Relevance + Informativeness) / 2
```

#### 4.3 Quality Gate

```python
# Qualitätsprüfung der finalen Antwort
quality_check = {
    "has_sources": len(sources) > 0,
    "has_citations": len(citations) > 0,
    "min_confidence": confidence >= 0.7,
    "response_length": len(final_response) >= 100,
    "coherence_score": self._check_coherence(final_response)
}

if not all(quality_check.values()):
    # Fallback: Retry mit höherer Temperature
    # oder vereinfachter Query
    ...
```

---

### Phase 5: Response Normalization

**Komponente**: `backend/models/response.py` → `UnifiedResponse`

```python
# Finale Response-Struktur (IEEE-Standard)
response = UnifiedResponse(
    content=final_response,  # LLM-generierte Antwort
    sources=[
        UnifiedSourceMetadata(
            document_id="bauGB_35",
            title="§ 35 BauGB - Bauen im Außenbereich",
            content="(1) Im Außenbereich ist ein Vorhaben nur zulässig...",
            metadata={
                # 35+ IEEE-Standard Felder
                "authors": ["Gesetzgeber"],
                "publication_date": "2023-01-01",
                "source_type": "legal_code",
                "relevance_score": 0.92,
                "rerank_score": 0.95,
                "search_method": "hybrid",
                "ranking_strategy": "reciprocal_rank_fusion",
                "vector_rank": 1,
                "graph_rank": 2,
                "relational_rank": 1,
                "rrf_score": 0.0486,
                ...
            }
        ),
        ...
    ],
    metadata=UnifiedResponseMetadata(
        model="llama3.1:8b",
        mode="rag",
        duration=5.42,
        tokens_used=1523,
        sources_count=8,
        complexity="COMPLEX",
        domain="BAURECHT",
        agents_involved=["rechtsrecherche", "baurecht", "database"],
        search_method="hybrid",
        rerank_applied=True,
        quality_score=0.89,
        confidence=0.92
    ),
    session_id="uuid-...",
    agent_results={
        "rechtsrecherche": {...},
        "baurecht": {...},
        "database": {...}
    },
    quality_metrics={
        "coherence": 0.91,
        "completeness": 0.88,
        "accuracy": 0.93
    }
)
```

---

### Phase 6: Response Delivery

**Komponente**: `backend/api/query_router.py`

```python
# FastAPI serialisiert zu JSON
return response  # Pydantic Model → JSON

# HTTP Response:
HTTP/1.1 200 OK
Content-Type: application/json

{
  "content": "Ein Bauantrag im Außenbereich nach § 35 BauGB...",
  "sources": [...],
  "metadata": {...},
  "session_id": "uuid-...",
  "agent_results": {...},
  "quality_metrics": {...}
}
```

---

## 3. Komponenten-Details

### 3.1 UDS3 PolyglotManager (Data Layer)

**Datei**: `uds3/core.py`

**Funktion**: Einheitliche Schnittstelle zu 4 Datenbank-Backends

**Initialisierung**:
```python
# In backend/app.py (Startup)
uds3 = UDS3PolyglotManager(
    backend_config={
        "vector": {"enabled": True},      # ChromaDB
        "graph": {"enabled": True},       # Neo4j
        "relational": {"enabled": True},  # PostgreSQL
        "file": {"enabled": True}         # CouchDB
    },
    enable_rag=True
)
```

**Methoden**:

| Methode | Backend | Beschreibung |
|---------|---------|--------------|
| `vector_search()` | ChromaDB | Semantic Search via Embeddings |
| `graph_query()` | Neo4j | Cypher Query für Graph |
| `sql_query()` | PostgreSQL | SQL Query für Relational |
| `get_document()` | CouchDB | Original Document Retrieval |
| `hybrid_search()` | All | RRF Fusion über alle Backends |

**Connection Pooling**:
- ChromaDB: HTTP Client (persistent)
- Neo4j: Driver Pool (max 50 connections)
- PostgreSQL: psycopg2 Pool (max 20 connections)
- CouchDB: HTTP Client (persistent)

---

### 3.2 IntelligentMultiAgentPipeline (Orchestration)

**Datei**: `backend/core/pipeline/intelligent_pipeline.py`

**Kernfunktion**: Orchestrierung von Multi-Agent-Execution

**Lifecycle**:

```python
# 1. Initialisierung (Startup)
pipeline = await get_intelligent_pipeline()

# 2. Query Execution
request = IntelligentPipelineRequest(
    query_id=str(uuid.uuid4()),
    query_text=query,
    enable_llm_commentary=True
)

response = await pipeline.execute(request)

# 3. Shutdown (optional)
await pipeline.shutdown()
```

**Execution Flow**:

```python
async def execute(self, request: IntelligentPipelineRequest):
    # 1. Query Analysis
    analysis = await self._analyze_query(request.query_text)

    # 2. Agent Selection
    agents = self._select_agents(analysis)

    # 3. RAG Context
    rag_context = await self._get_rag_context(request.query_text)

    # 4. Parallel Execution
    results = await self._execute_agents_parallel(agents, rag_context)

    # 5. Aggregation
    final_response = await self._aggregate_results(results)

    # 6. Quality Check
    validated = await self._validate_response(final_response)

    return IntelligentPipelineResponse(...)
```

---

### 3.3 RAGContextService (RAG Layer)

**Datei**: `backend/agents/rag_context_service.py`

**Funktion**: RAG-Context-Retrieval aus UDS3

```python
async def get_context(
    query: str,
    options: RAGQueryOptions
) -> Dict[str, Any]:
    # 1. Embedding generieren
    query_embedding = await self.embedding_model.embed(query)

    # 2. Vector Search
    vector_results = await self.uds3.vector_search(
        embedding=query_embedding,
        top_k=options.top_k
    )

    # 3. Graph Traversal (optional)
    graph_results = []
    if options.enable_graph:
        graph_results = await self.uds3.graph_query(
            query=query,
            limit=options.top_k
        )

    # 4. Relational Query (optional)
    relational_results = []
    if options.enable_relational:
        relational_results = await self.uds3.sql_query(
            query=self._build_sql_query(query),
            limit=options.top_k
        )

    # 5. RRF Fusion
    combined = self._reciprocal_rank_fusion(
        vector_results,
        graph_results,
        relational_results,
        k=60
    )

    return {
        "vector_results": vector_results,
        "graph_results": graph_results,
        "relational_results": relational_results,
        "combined_sources": combined
    }
```

**Reciprocal Rank Fusion (RRF)**:

```python
def _reciprocal_rank_fusion(results_lists, k=60):
    """
    RRF Formula: score(d) = Σ(1 / (k + rank_i(d)))

    - k: Parameter (default 60, aus Lit.)
    - rank_i(d): Rang von Dokument d in Liste i
    """
    scores = defaultdict(float)

    for rank, doc in enumerate(results_list, start=1):
        scores[doc.id] += 1 / (k + rank)

    # Sortiere nach Score (descending)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

---

### 3.4 RerankerService (Quality Layer)

**Datei**: `backend/services/reranker_service.py`

**Funktion**: LLM-basiertes Re-Ranking von Search Results

```python
async def rerank(
    query: str,
    sources: List[Dict],
    scoring_mode: ScoringMode = ScoringMode.COMBINED
) -> List[RerankingResult]:
    """
    LLM-Scoring mit zwei Dimensionen:
    - Relevance: Wie relevant ist die Source für die Query?
    - Informativeness: Wie informativ ist die Source?
    """

    reranked = []
    for source in sources:
        # LLM Prompt
        prompt = f"""
        Query: {query}

        Document:
        {source['content'][:500]}

        Rate this document on two scales (0.0-1.0):
        1. Relevance: How relevant is it to the query?
        2. Informativeness: How informative is it?

        Respond in JSON:
        {{
            "relevance": 0.0-1.0,
            "informativeness": 0.0-1.0,
            "reasoning": "Brief explanation"
        }}
        """

        # LLM Call
        llm_response = await self.ollama_client.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature
        )

        # Parse JSON
        scores = json.loads(llm_response["message"]["content"])

        # Combine Scores
        if scoring_mode == ScoringMode.COMBINED:
            final_score = (scores["relevance"] + scores["informativeness"]) / 2
        elif scoring_mode == ScoringMode.RELEVANCE:
            final_score = scores["relevance"]
        else:
            final_score = scores["informativeness"]

        reranked.append(RerankingResult(
            source=source,
            original_score=source.get("score", 0.0),
            rerank_score=final_score,
            relevance=scores["relevance"],
            informativeness=scores["informativeness"],
            reasoning=scores["reasoning"]
        ))

    # Sort by rerank_score
    return sorted(reranked, key=lambda x: x.rerank_score, reverse=True)
```

---

## 4. Datenfluss-Diagramm

### 4.1 Vollständiger End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                                 │
│  "Was sind die Anforderungen für einen Bauantrag im Außenbereich?"  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      1. API LAYER (FastAPI)                          │
│  POST /api/query → Router → Dependency Injection                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ UnifiedQueryRequest:                                         │  │
│  │ {                                                            │  │
│  │   query: "Was sind...",                                      │  │
│  │   mode: "rag",                                               │  │
│  │   model: "llama3.1:8b",                                      │  │
│  │   top_k: 10                                                  │  │
│  │ }                                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   2. SERVICE LAYER (QueryService)                    │
│  Mode Detection: RAG → _process_rag()                               │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Pipeline Request:                                            │  │
│  │ {                                                            │  │
│  │   query_id: "uuid-...",                                      │  │
│  │   query_text: "Was sind...",                                 │  │
│  │   enable_llm_commentary: true                                │  │
│  │ }                                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│            3. ORCHESTRATION (IntelligentMultiAgentPipeline)         │
│  ┌──────────────────┬──────────────────┬──────────────────────┐   │
│  │ 3.1 Analysis     │ 3.2 Selection    │ 3.3 RAG Context      │   │
│  │ ─────────────    │ ──────────────   │ ──────────────────   │   │
│  │ Complexity:      │ Primary:         │ Vector Search:       │   │
│  │ COMPLEX          │ - rechtsrecherche│ ChromaDB (top 10)    │   │
│  │                  │ - baurecht       │                      │   │
│  │ Domain:          │                  │ Graph Traversal:     │   │
│  │ BAURECHT         │ Secondary:       │ Neo4j (top 10)       │   │
│  │                  │ - database       │                      │   │
│  │ Intent:          │                  │ Relational:          │   │
│  │ LEGAL_ADVICE     │ Optional:        │ PostgreSQL (top 10)  │   │
│  │                  │ - environmental  │                      │   │
│  │                  │                  │ RRF Fusion:          │   │
│  │                  │                  │ Combined (top 10)    │   │
│  └──────────────────┴──────────────────┴──────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   4. DATA LAYER (UDS3 PolyglotManager)              │
│  ┌──────────────┬───────────────┬────────────────┬──────────────┐ │
│  │ ChromaDB     │ Neo4j         │ PostgreSQL     │ CouchDB      │ │
│  │ ──────────   │ ─────────     │ ────────────   │ ──────────   │ │
│  │ Embedding:   │ Cypher:       │ SQL:           │ Doc ID:      │ │
│  │ [0.12, ...]  │ MATCH (p:Para)│ SELECT * FROM  │ "bauGB_35"   │ │
│  │              │ -[:REF]->     │ dokumente      │              │ │
│  │ Results:     │ (l:Law)       │                │ Content:     │ │
│  │ 10 docs      │               │ Results:       │ Full PDF     │ │
│  │              │ Results:      │ 10 rows        │              │ │
│  │              │ 10 nodes      │                │              │ │
│  └──────────────┴───────────────┴────────────────┴──────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                5. AGENT EXECUTION (Parallel)                         │
│  ┌──────────────────┬──────────────────┬──────────────────────┐   │
│  │ Rechtsrecherche  │ Baurecht         │ Database             │   │
│  │ ──────────────── │ ────────────     │ ──────────────────   │   │
│  │ + RAG Context    │ + RAG Context    │ + RAG Context        │   │
│  │ + LLM Analysis   │ + LLM Analysis   │ + SQL Query          │   │
│  │                  │                  │                      │   │
│  │ Output:          │ Output:          │ Output:              │   │
│  │ "§ 35 BauGB..."  │ "Baugenehmi..."  │ [SQL Results]        │   │
│  └──────────────────┴──────────────────┴──────────────────────┘   │
│                             │                                       │
│                             ▼                                       │
│                      AGGREGATION                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ LLM Synthesis (llama3.1:8b):                                 │ │
│  │ "Ein Bauantrag im Außenbereich nach § 35 BauGB erfordert..." │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    6. QUALITY ASSURANCE                              │
│  ┌──────────────────┬──────────────────┬──────────────────────┐   │
│  │ Citation Extract │ Re-Ranking       │ Quality Gate         │   │
│  │ ──────────────── │ ──────────────   │ ──────────────────   │   │
│  │ IEEE Standard    │ LLM Scoring:     │ Checks:              │   │
│  │ 35+ Fields       │ - Relevance      │ ✓ Has Sources        │   │
│  │                  │ - Informative    │ ✓ Has Citations      │   │
│  │ [BauGB §35,...]  │                  │ ✓ Confidence > 0.7   │   │
│  │                  │ Reranked: [...]  │ ✓ Length > 100       │   │
│  └──────────────────┴──────────────────┴──────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  7. RESPONSE NORMALIZATION                           │
│  UnifiedResponse (IEEE Standard):                                   │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ {                                                            │  │
│  │   content: "Ein Bauantrag im Außenbereich...",              │  │
│  │   sources: [                                                 │  │
│  │     {                                                        │  │
│  │       document_id: "bauGB_35",                               │  │
│  │       title: "§ 35 BauGB - Bauen im Außenbereich",          │  │
│  │       relevance_score: 0.92,                                 │  │
│  │       rerank_score: 0.95,                                    │  │
│  │       ... // 33 weitere Felder                               │  │
│  │     }                                                        │  │
│  │   ],                                                         │  │
│  │   metadata: {                                                │  │
│  │     model: "llama3.1:8b",                                    │  │
│  │     mode: "rag",                                             │  │
│  │     duration: 5.42,                                          │  │
│  │     agents_involved: ["rechtsrecherche", "baurecht"],        │  │
│  │     quality_score: 0.89                                      │  │
│  │   }                                                          │  │
│  │ }                                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       8. HTTP RESPONSE                               │
│  HTTP/1.1 200 OK                                                    │
│  Content-Type: application/json                                     │
│  X-Response-Time: 5420ms                                            │
│                                                                     │
│  { "content": "...", "sources": [...], ... }                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Qualitätssicherung

### 5.1 Multi-Level Quality Gates

| Level | Component | Checks |
|-------|-----------|--------|
| **L1: Input Validation** | Pydantic | Schema-Validierung, Type-Safety |
| **L2: RAG Quality** | UDS3 | Min. Similarity Score (>0.6) |
| **L3: Agent Quality** | Pipeline | Agent Success Rate (>80%) |
| **L4: Re-Ranking** | Reranker | LLM Relevance Score (>0.7) |
| **L5: Output Validation** | QueryService | Citation Count, Response Length |
| **L6: Monitoring** | Logging | Latency, Error Rate, Token Usage |

### 5.2 Qualitätsmetriken

**Definitionen**:

```python
quality_metrics = {
    "coherence": float,      # Wie kohärent ist die Antwort? (0-1)
    "completeness": float,   # Beantwortet sie die Frage vollständig? (0-1)
    "accuracy": float,       # Sind die Fakten korrekt? (0-1)
    "relevance": float,      # Sind die Sources relevant? (0-1)
    "informativeness": float # Ist die Antwort informativ? (0-1)
}
```

**Berechnung**:

```python
def calculate_quality_metrics(response, sources, query):
    # Coherence: LLM-basiert
    coherence = await llm_evaluate_coherence(response)

    # Completeness: Keyword-Analyse
    completeness = check_query_terms_coverage(query, response)

    # Accuracy: Fact-Checking via Cross-References
    accuracy = await verify_facts(response, sources)

    # Relevance: Average Source Relevance
    relevance = np.mean([s.relevance_score for s in sources])

    # Informativeness: Information Density
    informativeness = calculate_information_density(response)

    return {
        "coherence": coherence,
        "completeness": completeness,
        "accuracy": accuracy,
        "relevance": relevance,
        "informativeness": informativeness
    }
```

### 5.3 Fallback-Strategien

**Bei niedriger Qualität** (`quality_score < 0.7`):

```python
if quality_score < 0.7:
    # Strategy 1: Retry mit höherer Temperature
    response = await retry_with_higher_temperature(query, temperature=0.5)

    if quality_score < 0.7:
        # Strategy 2: Vereinfachte Query
        simplified_query = simplify_query(query)
        response = await process_query(simplified_query)

        if quality_score < 0.7:
            # Strategy 3: Fallback zu Direct LLM (Ask Mode)
            response = await direct_llm_ask(query)
```

---

## 6. Performance-Optimierung

### 6.1 Caching-Strategie

**Mehrstufiges Caching**:

| Layer | Technology | TTL | Hit Rate |
|-------|-----------|-----|----------|
| **L1: In-Memory** | Python Dict | 5 min | 40% |
| **L2: Redis** | Redis | 1 hour | 30% |
| **L3: Database** | PostgreSQL | 24 hours | 20% |

**Cache-Keys**:

```python
def generate_cache_key(query, mode, model, top_k):
    # SHA256 Hash aus normalisierten Parametern
    params = {
        "query": query.lower().strip(),
        "mode": mode,
        "model": model,
        "top_k": top_k
    }
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()
```

### 6.2 Parallel Execution

**Async/Await Pattern**:

```python
# Parallel Agent Execution
agent_tasks = [
    execute_agent("rechtsrecherche"),
    execute_agent("baurecht"),
    execute_agent("database")
]

# Gather with Timeout
results = await asyncio.wait_for(
    asyncio.gather(*agent_tasks, return_exceptions=True),
    timeout=60.0
)
```

**Performance-Vergleich**:

| Mode | Sequential | Parallel | Speedup |
|------|-----------|----------|---------|
| 3 Agents | 15s | 5s | **3x** |
| 5 Agents | 25s | 8s | **3.1x** |
| 10 Agents | 50s | 15s | **3.3x** |

### 6.3 Database Connection Pooling

**PostgreSQL** (psycopg2):
```python
pool = psycopg2.pool.SimpleConnectionPool(
    minconn=5,
    maxconn=20,
    host="postgres",
    database="veritas"
)
```

**Neo4j** (neo4j-driver):
```python
driver = GraphDatabase.driver(
    "bolt://neo4j:7687",
    auth=("neo4j", "password"),
    max_connection_pool_size=50
)
```

---

## 7. Fehlerbehandlung

### 7.1 Error Hierarchy

```
Exception
├── VeritasException (Base)
│   ├── QueryException
│   │   ├── InvalidQueryException
│   │   ├── TimeoutException
│   │   └── RateLimitException
│   ├── AgentException
│   │   ├── AgentNotFoundExclusion
│   │   ├── AgentExecutionException
│   │   └── AgentTimeoutException
│   ├── DatabaseException
│   │   ├── ConnectionException
│   │   ├── QueryExecutionException
│   │   └── DataNotFoundException
│   └── LLMException
│       ├── ModelNotFoundException
│       ├── TokenLimitException
│       └── GenerationException
```

### 7.2 Error Recovery

**Try-Except-Fallback Pattern**:

```python
async def execute_with_fallback(primary_fn, fallback_fn, *args):
    try:
        return await primary_fn(*args)
    except TimeoutException:
        logger.warning("Timeout - using fallback")
        return await fallback_fn(*args)
    except Exception as e:
        logger.error(f"Error: {e} - using fallback")
        return await fallback_fn(*args)

# Usage:
result = await execute_with_fallback(
    primary_fn=rag_query,
    fallback_fn=direct_llm_ask,
    query_text
)
```

### 7.3 Graceful Degradation

**Bei Ausfall einzelner Komponenten**:

| Component Failed | Degraded Functionality |
|-----------------|------------------------|
| ChromaDB (Vector) | Fallback to BM25 (PostgreSQL Fulltext) |
| Neo4j (Graph) | Skip Graph Traversal, Vector Only |
| PostgreSQL (Relational) | Skip Structured Data, Vector + Graph |
| Ollama (LLM) | Use OpenAI API (fallback) |
| Agent X | Remove from Pipeline, Continue with Others |

---

## 8. Beispiel-Ablauf

### Komplette Query: "Was sind die Anforderungen für einen Bauantrag im Außenbereich?"

#### Timeline:

```
T=0ms      Client sendet POST /api/query
T=10ms     FastAPI validiert Request (Pydantic)
T=15ms     QueryService.process_query() startet
T=20ms     Mode=RAG erkannt → _process_rag()
T=25ms     Pipeline.execute() gestartet
T=30ms     Query Analysis:
           - Complexity: COMPLEX (BauGB, Außenbereich)
           - Domain: BAURECHT
           - Intent: LEGAL_ADVICE
T=50ms     Agent Selection:
           - Primary: rechtsrecherche, baurecht
           - Secondary: database
T=100ms    RAG Context Retrieval (parallel):
           - ChromaDB Vector Search: 10 results (40ms)
           - Neo4j Graph Traversal: 8 results (45ms)
           - PostgreSQL Fulltext: 12 results (35ms)
           - RRF Fusion: 10 combined results (15ms)
T=150ms    Parallel Agent Execution startet:
           - Rechtsrecherche-Agent (Thread 1)
           - Baurecht-Agent (Thread 2)
           - Database-Agent (Thread 3)
T=2000ms   Rechtsrecherche-Agent fertig:
           "§ 35 BauGB regelt das Bauen im Außenbereich..."
T=2200ms   Baurecht-Agent fertig:
           "Ein Bauantrag erfordert folgende Unterlagen..."
T=2500ms   Database-Agent fertig:
           [SQL Results: Verwaltungsvorschriften]
T=2600ms   Aggregation (LLM Synthesis):
           Prompt: "Synthetisiere die 3 Agent-Ergebnisse..."
T=4800ms   LLM Response:
           "Ein Bauantrag im Außenbereich nach § 35 BauGB..."
T=5000ms   Re-Ranking (LLM Scoring):
           - Source 1: Relevance 0.95, Informativeness 0.92
           - Source 2: Relevance 0.88, Informativeness 0.85
           - ...
T=5200ms   Quality Check:
           - Has Sources: ✓ (10)
           - Has Citations: ✓ (5)
           - Confidence: ✓ (0.89)
           - Quality Score: ✓ (0.91)
T=5300ms   Response Normalization (UnifiedResponse)
T=5400ms   FastAPI serialisiert zu JSON
T=5420ms   HTTP Response 200 OK

TOTAL: 5420ms (5.42s)
```

#### Metriken:

```json
{
  "duration": 5.42,
  "tokens_used": 1523,
  "sources_count": 10,
  "agents_involved": ["rechtsrecherche", "baurecht", "database"],
  "quality_score": 0.91,
  "confidence": 0.89,
  "cache_hit": false,
  "database_queries": {
    "chromadb": 1,
    "neo4j": 1,
    "postgresql": 1
  },
  "agent_execution_times": {
    "rechtsrecherche": 1.85,
    "baurecht": 2.05,
    "database": 2.35
  },
  "llm_calls": {
    "synthesis": 1,
    "reranking": 10
  }
}
```

---

## 9. Zusammenfassung

### 9.1 Kernerkenntnisse

1. **Orchestriertes Multi-Agent-System**: Nicht ein monolithischer Ansatz, sondern koordinierte Spezial-Agenten
2. **Polyglotte Datenbank (UDS3)**: Verschiedene DB-Typen für verschiedene Anforderungen
3. **Iterative Qualitätssicherung**: Mehrere Quality Gates auf verschiedenen Ebenen
4. **LLM als "Klebstoff"**: Synthesis, Re-Ranking, Commentary
5. **Parallelisierung**: 3x Speedup durch async Agent Execution

### 9.2 Bewertung der Antwort

**Wie wird bewertet, ob die Antwort ausreicht?**

Multi-dimensionale Bewertung:

1. **Quality Metrics** (automatisch):
   - Coherence (LLM-basiert)
   - Completeness (Keyword-Coverage)
   - Accuracy (Fact-Checking)
   - Relevance (Source Scores)
   - Informativeness (Information Density)

2. **Quality Gate** (automatisch):
   - Hat die Antwort Sources? (Ja/Nein)
   - Hat die Antwort Citations? (Ja/Nein)
   - Ist Confidence > 0.7? (Ja/Nein)
   - Ist Response-Length > 100? (Ja/Nein)

3. **User Feedback** (optional):
   - Thumbs Up/Down
   - Textual Feedback
   - Follow-up Questions (implizites Signal)

**Fallback bei unzureichender Qualität**:

```
Quality Score < 0.7
    ↓
Retry mit höherer Temperature (0.5 statt 0.1)
    ↓ (wenn immer noch < 0.7)
Vereinfachte Query
    ↓ (wenn immer noch < 0.7)
Fallback zu Direct LLM (Ask Mode, ohne RAG)
    ↓ (wenn immer noch < 0.7)
Error Response mit Hinweis für User
```

### 9.3 Stärken des Systems

✅ **Modular**: Komponenten unabhängig austauschbar
✅ **Skalierbar**: Parallel Execution, Connection Pooling
✅ **Robust**: Multi-Level Error Handling, Graceful Degradation
✅ **Transparent**: LLM Commentary, Processing Metadata
✅ **Qualitätsgesichert**: Multi-Level Quality Gates
✅ **Flexibel**: Verschiedene Modi (RAG, Hybrid, Agent, Ask)

### 9.4 Optimierungspotenzial

🔧 **Caching erweitern**: Semantic Caching (ähnliche Queries)
🔧 **Agent-Priorisierung**: Dynamische Agent-Auswahl basierend auf Past Performance
🔧 **Adaptive Timeouts**: Längere Timeouts für komplexe Queries
🔧 **Query Rewriting**: Automatische Query-Verbesserung
🔧 **Feedback Loop**: User-Feedback zurück in Agent-Selektion

---

## 10. Weiterführende Dokumentation

- **API-Dokumentation**: `/docs` (Swagger UI)
- **UDS3 Integration**: `docs/UDS3_INTEGRATION.md`
- **Agent Framework**: `docs/AGENT_FRAMEWORK_QUICKSTART.md`
- **Hybrid Search**: `docs/HYBRID_SEARCH_DEVELOPER_GUIDE.md`
- **Polyglot Execution Plan**: `docs/POLYGLOT_EXECUTION_PLAN_ANALYSIS.md`
- **OOP Architecture**: `BACKEND_OOP_STRUCTURE_GUIDE.md`

---

**Erstellt von**: VERITAS Development Team
**Letzte Aktualisierung**: 2025-12-03
**Version**: 1.0
**Status**: ✅ Produktionsbereit
