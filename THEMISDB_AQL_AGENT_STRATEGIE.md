# ThemisDB AQL Agent Strategie für VCC-Veritas

**Version:** 1.0  
**Datum:** 3. Dezember 2025  
**Status:** 🎯 Strategisches Implementierungskonzept  
**Ziel:** Integration von ThemisDB AQL als Alternative zu UDS3 mit RAG-Fähigkeiten und Agent-getriebenem Kerndesign

---

## Executive Summary

Diese Strategie beschreibt die Integration eines ThemisDB AQL/Python Client Adapters als Alternative zum bestehenden UDS3-System, mit erweiterten RAG (Retrieval-Augmented Generation) Fähigkeiten und vollständiger Agent-Orchestrierung. Das Ziel ist es, Veritas in eine moderne, multi-modale, agent-getriebene Plattform zu transformieren.

### Strategische Ziele

1. **🔌 ThemisDB AQL Integration**: Vollständiger Adapter/Agent für ThemisDB mit AQL-Query-Unterstützung
2. **🤖 RAG-Fähigkeiten**: Erweiterte Retrieval-Augmented Generation für verbesserte Antwortqualität
3. **🎭 Agent-getriebene Architektur**: Orchestrierte, multi-modale Agent-Pipelines als Kernfunktion
4. **📊 Multi-Modell-Zugriff**: Nahtlose Integration von Vector, Graph, Document und AQL-Queries
5. **⚡ Performance**: Optimierte Query-Ausführung mit Caching und Parallelisierung

---

## 1. Architektur-Übersicht

### 1.1 Aktuelle Architektur (Ist-Zustand)

```
┌─────────────────────────────────────────────────────────────┐
│                    VCC-Veritas v3.19.0                       │
│                                                              │
│  ┌──────────────────┐                                       │
│  │  Frontend        │                                       │
│  │  (Tkinter)       │                                       │
│  └────────┬─────────┘                                       │
│           │ HTTP/REST                                        │
│  ┌────────┴─────────────────────────────────┐              │
│  │      FastAPI Backend (Monolith)          │              │
│  │                                           │              │
│  │  ┌──────────────┐  ┌──────────────────┐ │              │
│  │  │ RAG Service  │  │ Agent Registry   │ │              │
│  │  └──────┬───────┘  └──────┬───────────┘ │              │
│  │         │                  │              │              │
│  │  ┌──────┴──────────────────┴──────┐     │              │
│  │  │   Adapter Factory              │     │              │
│  │  │   (ThemisDB ⇄ UDS3 Fallback)  │     │              │
│  │  └──────┬──────────────┬──────────┘     │              │
│  └─────────┼──────────────┼────────────────┘              │
│            │              │                                 │
│    ┌───────┴────┐   ┌────┴──────────────┐                │
│    │ ThemisDB   │   │ UDS3 Polyglot     │                │
│    │ Adapter    │   │ (Neo4j/Chroma/PG) │                │
│    └────────────┘   └───────────────────┘                │
└─────────────────────────────────────────────────────────────┘

**Limitierungen:**
- ThemisDB: Nur Vector Search implementiert
- UDS3: Multi-DB, aber komplexe Konfiguration
- RAG: Fest verdrahtet mit UDS3
- Agents: Existieren, aber lose gekoppelt
- AQL: Nicht integriert in RAG-Pipeline
```

### 1.2 Ziel-Architektur (Soll-Zustand)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VCC-Veritas v4.0 (Agent-Driven)                       │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                  Agent Orchestrator (Core)                        │  │
│  │                                                                    │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │ Query Agent  │  │ RAG Agent    │  │ AQL Agent    │          │  │
│  │  │ (Intent)     │  │ (Retrieval)  │  │ (ThemisDB)   │          │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │  │
│  │         │                  │                  │                   │  │
│  │         └──────────────────┴──────────────────┘                  │  │
│  │                            ▼                                      │  │
│  │                  ┌─────────────────────┐                         │  │
│  │                  │ ThemisDB RAG Agent  │ ⭐ NEU                 │  │
│  │                  │ (Multi-Modal Query) │                         │  │
│  │                  └──────────┬──────────┘                         │  │
│  └─────────────────────────────┼────────────────────────────────────┘  │
│                                │                                        │
│  ┌─────────────────────────────┴────────────────────────────────────┐  │
│  │              ThemisDB Unified Adapter                             │  │
│  │                                                                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │  │
│  │  │ Vector     │  │ Graph      │  │ AQL Query  │  │ Document │  │  │
│  │  │ Search     │  │ Traversal  │  │ Engine     │  │ CRUD     │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                ▼                                        │
│                       ┌─────────────────┐                               │
│                       │  ThemisDB v1.x  │                               │
│                       │  (Multi-Model)  │                               │
│                       └─────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────┘

**Vorteile:**
✅ Agent-getrieben: Orchestrator als Kern
✅ Multi-Modal: Vector + Graph + AQL + Document
✅ RAG-optimiert: Prompt Engineering für AQL
✅ Fallback-fähig: UDS3 als Alternative
✅ Erweiterbar: Neue Agents einfach integrierbar
```

---

## 2. ThemisDB AQL Agent - Technische Spezifikation

### 2.1 Agent-Architektur

```python
# backend/agents/veritas_themisdb_aql_agent.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AQLQueryType(Enum):
    """ThemisDB AQL Query Types"""
    VECTOR_SEARCH = "vector_search"      # Vector similarity search
    GRAPH_TRAVERSAL = "graph_traversal"  # Graph pattern matching
    DOCUMENT_FILTER = "document_filter"  # Document filtering
    HYBRID_QUERY = "hybrid_query"        # Combined multi-model
    AGGREGATION = "aggregation"          # Statistical aggregations


@dataclass
class AQLPromptContext:
    """Context for AQL Prompt Engineering"""
    user_query: str
    query_intent: str
    query_complexity: str
    domain: str
    required_capabilities: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AQLQueryPlan:
    """Execution plan for AQL query"""
    query_type: AQLQueryType
    aql_query: str
    bind_vars: Dict[str, Any]
    estimated_cost: float
    use_cache: bool = True
    timeout_seconds: int = 30


class ThemisDBPromptEngineer:
    """
    AQL Prompt Engineering for RAG Optimization
    
    Konvertiert natürliche Sprache zu optimierten AQL-Queries
    basierend auf Query-Intent und Domain-Kontext.
    """
    
    def __init__(self):
        self.templates = self._load_aql_templates()
        self.domain_mappings = self._load_domain_mappings()
    
    def engineer_aql_query(
        self,
        context: AQLPromptContext
    ) -> AQLQueryPlan:
        """
        Generiert optimierten AQL Query Plan aus Prompt Context.
        
        Strategie:
        1. Intent Detection (Vector/Graph/Document/Hybrid)
        2. Template Selection basierend auf Domain
        3. Parameter Binding aus Kontext
        4. Query Optimization (Indizes, Limits, Caching)
        5. Cost Estimation
        
        Returns:
            AQLQueryPlan mit optimiertem Query
        """
        # 1. Detect query type
        query_type = self._detect_query_type(context)
        
        # 2. Select template
        template = self._select_template(query_type, context.domain)
        
        # 3. Extract parameters
        bind_vars = self._extract_bind_vars(context)
        
        # 4. Build AQL query
        aql_query = template.format(**bind_vars)
        
        # 5. Optimize query
        aql_query = self._optimize_query(aql_query, context)
        
        # 6. Estimate cost
        cost = self._estimate_cost(aql_query, bind_vars)
        
        return AQLQueryPlan(
            query_type=query_type,
            aql_query=aql_query,
            bind_vars=bind_vars,
            estimated_cost=cost,
            use_cache=cost < 100  # Cache low-cost queries
        )
    
    def _detect_query_type(self, context: AQLPromptContext) -> AQLQueryType:
        """Erkennt Query-Typ aus Intent und Capabilities"""
        capabilities = set(context.required_capabilities)
        
        if "vector_search" in capabilities and "graph_traversal" in capabilities:
            return AQLQueryType.HYBRID_QUERY
        elif "vector_search" in capabilities:
            return AQLQueryType.VECTOR_SEARCH
        elif "graph_traversal" in capabilities:
            return AQLQueryType.GRAPH_TRAVERSAL
        elif "aggregation" in context.query_intent.lower():
            return AQLQueryType.AGGREGATION
        else:
            return AQLQueryType.DOCUMENT_FILTER
    
    def _load_aql_templates(self) -> Dict[str, str]:
        """Lädt AQL Query Templates"""
        return {
            "vector_search": """
                FOR doc IN @@collection
                  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
                  FILTER similarity >= @threshold
                  SORT similarity DESC
                  LIMIT @limit
                  RETURN {
                    doc_id: doc._key,
                    content: doc.content,
                    score: similarity,
                    metadata: doc.metadata
                  }
            """,
            
            "graph_traversal": """
                FOR vertex, edge, path IN @min_depth..@max_depth @direction
                  @start_vertex
                  GRAPH @graph_name
                  OPTIONS {uniqueVertices: "path"}
                  RETURN {
                    vertex: vertex,
                    path: path,
                    depth: LENGTH(path.edges)
                  }
            """,
            
            "hybrid_query": """
                // 1. Vector Search (semantische Ähnlichkeit)
                LET vector_results = (
                  FOR doc IN @@collection
                    LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
                    FILTER similarity >= @vector_threshold
                    SORT similarity DESC
                    LIMIT @vector_limit
                    RETURN {doc: doc, score: similarity, source: "vector"}
                )
                
                // 2. Graph Traversal (Beziehungen)
                LET graph_results = (
                  FOR v IN vector_results
                    FOR vertex, edge IN 1..@graph_depth OUTBOUND v.doc._id
                      GRAPH @graph_name
                      RETURN {doc: vertex, edge: edge, source: "graph"}
                )
                
                // 3. Merge & Re-rank
                LET merged = UNION_DISTINCT(vector_results, graph_results)
                
                FOR result IN merged
                  SORT result.score DESC
                  LIMIT @final_limit
                  RETURN result
            """,
            
            "rag_optimized": """
                // RAG-optimierte Query mit Context Enrichment
                LET base_docs = (
                  FOR doc IN @@collection
                    LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
                    FILTER similarity >= @threshold
                    SORT similarity DESC
                    LIMIT @limit
                    RETURN doc
                )
                
                // Context Enrichment via Graph
                FOR doc IN base_docs
                  LET context = (
                    FOR v IN 1..2 OUTBOUND doc._id
                      @edge_collection
                      RETURN {
                        title: v.title,
                        summary: v.summary,
                        relation: "cites"
                      }
                  )
                  
                  RETURN {
                    doc_id: doc._key,
                    content: doc.content,
                    score: COSINE_SIMILARITY(doc.embedding, @query_vector),
                    metadata: doc.metadata,
                    context: context,
                    rag_ready: true
                  }
            """
        }
    
    def _optimize_query(self, aql_query: str, context: AQLPromptContext) -> str:
        """Optimiert AQL Query für Performance"""
        # Add index hints
        if "complexity" in context.metadata:
            if context.metadata["complexity"] == "low":
                # Use aggressive caching
                aql_query = f"/* +cache */ {aql_query}"
        
        # Add query profiling for complex queries
        if context.query_complexity == "high":
            aql_query = f"/* +profile */ {aql_query}"
        
        return aql_query.strip()


class ThemisDBRAGAgent:
    """
    ThemisDB RAG Agent mit AQL-basiertem Retrieval
    
    Capabilities:
    - Multi-Model Query Execution (Vector + Graph + Document)
    - AQL Prompt Engineering für optimale RAG-Performance
    - Intelligent Query Planning & Caching
    - Context Enrichment via Graph Traversal
    """
    
    def __init__(self, themisdb_adapter, config: Optional[Dict] = None):
        self.adapter = themisdb_adapter
        self.config = config or {}
        self.prompt_engineer = ThemisDBPromptEngineer()
        self.query_cache = {}
        
        logger.info("✅ ThemisDBRAGAgent initialisiert")
    
    async def retrieve_with_rag(
        self,
        query: str,
        top_k: int = 5,
        context_depth: int = 2,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        RAG-optimiertes Retrieval mit AQL Query Engineering.
        
        Pipeline:
        1. Prompt Engineering (Query → AQL)
        2. Query Execution (ThemisDB)
        3. Context Enrichment (Graph Traversal)
        4. Result Re-ranking
        5. RAG-Format Transformation
        
        Args:
            query: User-Query in natürlicher Sprache
            top_k: Anzahl Top-Dokumente
            context_depth: Graph-Traversal-Tiefe für Context
            
        Returns:
            RAG-optimierte Dokumente mit Context
        """
        # 1. Build prompt context
        prompt_context = AQLPromptContext(
            user_query=query,
            query_intent="information_retrieval",
            query_complexity="medium",
            domain=kwargs.get("domain", "general"),
            required_capabilities=["vector_search", "graph_traversal"]
        )
        
        # 2. Engineer AQL query
        query_plan = self.prompt_engineer.engineer_aql_query(prompt_context)
        
        # 3. Check cache
        cache_key = self._get_cache_key(query_plan)
        if query_plan.use_cache and cache_key in self.query_cache:
            logger.info(f"🎯 Cache hit for query: {query[:50]}")
            return self.query_cache[cache_key]
        
        # 4. Execute AQL query
        if query_plan.query_type == AQLQueryType.HYBRID_QUERY:
            results = await self._execute_hybrid_query(query_plan, top_k, context_depth)
        else:
            results = await self.adapter.execute_aql(
                query=query_plan.aql_query,
                bind_vars=query_plan.bind_vars
            )
        
        # 5. Transform to RAG format
        rag_results = self._transform_to_rag_format(results)
        
        # 6. Cache results
        if query_plan.use_cache:
            self.query_cache[cache_key] = rag_results
        
        return rag_results
    
    async def _execute_hybrid_query(
        self,
        query_plan: AQLQueryPlan,
        top_k: int,
        context_depth: int
    ) -> List[Dict[str, Any]]:
        """Führt Hybrid Query (Vector + Graph) aus"""
        # Update bind vars with runtime params
        bind_vars = {
            **query_plan.bind_vars,
            "vector_limit": top_k * 2,  # Over-retrieve for re-ranking
            "graph_depth": context_depth,
            "final_limit": top_k
        }
        
        results = await self.adapter.execute_aql(
            query=query_plan.aql_query,
            bind_vars=bind_vars
        )
        
        return results
    
    def _transform_to_rag_format(self, results: List[Dict]) -> List[Dict[str, Any]]:
        """Transformiert AQL-Ergebnisse zu RAG-Format"""
        rag_results = []
        
        for result in results:
            rag_doc = {
                "doc_id": result.get("doc_id", ""),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {}),
                "context": result.get("context", []),
                "source": "themisdb_aql"
            }
            rag_results.append(rag_doc)
        
        return rag_results
    
    def _get_cache_key(self, query_plan: AQLQueryPlan) -> str:
        """Generiert Cache-Key für Query"""
        import hashlib
        query_str = f"{query_plan.aql_query}:{str(query_plan.bind_vars)}"
        return hashlib.md5(query_str.encode()).hexdigest()
```

---

## 3. AQL Prompt Engineering Guidelines

### 3.1 Dokumentation: `themisdb/docs/aql/aql_prompt_engineering.md`

Diese Datei wird als separate Referenz erstellt und beschreibt:

1. **AQL Query Patterns für RAG**
   - Vector Search Patterns
   - Graph Traversal Patterns
   - Hybrid Query Patterns
   - Context Enrichment Patterns

2. **Performance Optimization**
   - Index-Nutzung
   - Query Caching
   - Parallel Execution
   - Result Pagination

3. **Domain-spezifische Templates**
   - Verwaltungsrecht
   - Technische Standards
   - Umweltrecht
   - Finanzrecht

4. **Best Practices**
   - Query Complexity Management
   - Error Handling
   - Fallback Strategies
   - Monitoring & Debugging

---

## 4. Agent-Orchestrierung & Multi-Modal Integration

### 4.1 Agent Orchestrator Erweiterung

```python
# backend/agents/veritas_themisdb_orchestrator.py

class ThemisDBAgentOrchestrator:
    """
    Orchestrator für ThemisDB-basierte Agent-Pipeline
    
    Koordiniert:
    - Query Intent Detection
    - Agent Selection (Vector/Graph/AQL/Hybrid)
    - Parallel Query Execution
    - Result Fusion & Re-ranking
    - RAG Context Assembly
    """
    
    def __init__(self):
        self.agents = {
            "themisdb_rag": ThemisDBRAGAgent(...),
            "vector_search": VectorSearchAgent(...),
            "graph_traversal": GraphTraversalAgent(...),
            "aql_query": AQLQueryAgent(...)
        }
        
        self.agent_selector = AgentSelector()
        self.result_fusion = ResultFusion()
    
    async def orchestrate_query(
        self,
        query: str,
        mode: str = "auto"
    ) -> Dict[str, Any]:
        """
        Orchestriert multi-modale Query-Verarbeitung
        
        Pipeline:
        1. Intent Detection → Welche Agents?
        2. Agent Selection → Parallel/Sequential?
        3. Query Execution → Run Agents
        4. Result Fusion → Merge & Re-rank
        5. RAG Assembly → Build Context
        """
        # 1. Detect intent
        intent = await self._detect_intent(query)
        
        # 2. Select agents
        selected_agents = self.agent_selector.select(intent, mode)
        
        # 3. Execute in parallel
        agent_results = await self._execute_agents_parallel(
            selected_agents,
            query
        )
        
        # 4. Fuse results
        fused_results = self.result_fusion.fuse(agent_results)
        
        # 5. Assemble RAG context
        rag_context = self._assemble_rag_context(fused_results)
        
        return {
            "query": query,
            "intent": intent,
            "agents_used": [a.name for a in selected_agents],
            "results": fused_results,
            "rag_context": rag_context
        }
```

### 4.2 Multi-Modal Query Execution

```python
class MultiModalQueryEngine:
    """
    Multi-Modal Query Engine für ThemisDB
    
    Unterstützt:
    - Vector Search (Semantische Suche)
    - Graph Traversal (Beziehungen)
    - Document Filter (Exakte Matches)
    - AQL Queries (Komplexe Logik)
    - Hybrid Queries (Kombination)
    """
    
    async def execute_multi_modal(
        self,
        query_spec: MultiModalQuerySpec
    ) -> MultiModalResults:
        """
        Führt multi-modale Query aus
        
        Example Query Spec:
        {
            "vector": {"query": "BGB Vertragsrecht", "top_k": 10},
            "graph": {"start": "bgb_§123", "depth": 2},
            "filter": {"year": {"$gte": 2020}},
            "fusion": "reciprocal_rank"
        }
        """
        tasks = []
        
        # Vector Search
        if "vector" in query_spec:
            tasks.append(self._vector_search(query_spec["vector"]))
        
        # Graph Traversal
        if "graph" in query_spec:
            tasks.append(self._graph_traversal(query_spec["graph"]))
        
        # Document Filter
        if "filter" in query_spec:
            tasks.append(self._document_filter(query_spec["filter"]))
        
        # Execute parallel
        results = await asyncio.gather(*tasks)
        
        # Fusion
        fusion_method = query_spec.get("fusion", "simple_concat")
        fused = self._fuse_results(results, fusion_method)
        
        return fused
```

---

## 5. Implementierungs-Roadmap

### Phase 1: Foundation (Woche 1-2) ⏱️ 16-20 Stunden

**Ziele:**
- ✅ ThemisDB Adapter erweitern (AQL Support komplett)
- ✅ AQL Prompt Engineering Dokumentation
- ✅ ThemisDBRAGAgent Grundimplementierung
- ✅ Unit Tests (Coverage 80%+)

**Deliverables:**
- `backend/agents/veritas_themisdb_aql_agent.py` (1000 LOC)
- `themisdb/docs/aql/aql_prompt_engineering.md` (800 LOC)
- `tests/agents/test_themisdb_rag_agent.py` (400 LOC)
- `backend/adapters/themisdb_adapter.py` (Update: +300 LOC)

**Tasks:**
1. [ ] ThemisDB Adapter: AQL Query Builder hinzufügen
2. [ ] AQL Prompt Templates erstellen (5-10 Domain-Templates)
3. [ ] ThemisDBPromptEngineer implementieren
4. [ ] ThemisDBRAGAgent Basis-Implementation
5. [ ] Unit Tests (AQL Generation, Query Execution)
6. [ ] Dokumentation: AQL Prompt Engineering Guide

---

### Phase 2: Agent Integration (Woche 3-4) ⏱️ 16-20 Stunden

**Ziele:**
- ✅ Agent Orchestrator Integration
- ✅ Multi-Modal Query Engine
- ✅ Result Fusion & Re-ranking
- ✅ Integration Tests

**Deliverables:**
- `backend/agents/veritas_themisdb_orchestrator.py` (800 LOC)
- `backend/agents/multi_modal_query_engine.py` (600 LOC)
- `tests/integration/test_themisdb_orchestration.py` (500 LOC)

**Tasks:**
1. [ ] Orchestrator: Agent Selection Logic
2. [ ] Multi-Modal Query Engine implementieren
3. [ ] Result Fusion Algorithmen (RRF, Score-based)
4. [ ] Parallel Execution mit asyncio
5. [ ] Integration in bestehende RAGService
6. [ ] End-to-End Integration Tests

---

### Phase 3: RAG Optimization (Woche 5-6) ⏱️ 12-16 Stunden

**Ziele:**
- ✅ Context Enrichment via Graph
- ✅ Query Caching & Performance
- ✅ Monitoring & Metrics
- ✅ Production Readiness

**Deliverables:**
- Context Enrichment Pipeline
- Query Cache System (Redis/In-Memory)
- Performance Benchmarks
- Production Deployment Guide

**Tasks:**
1. [ ] Graph-basierte Context Enrichment
2. [ ] Query Caching (Redis Integration)
3. [ ] Performance Monitoring (Prometheus Metrics)
4. [ ] Benchmark: ThemisDB vs UDS3
5. [ ] Production Deployment Testing
6. [ ] Documentation Update

---

### Phase 4: Advanced Features (Woche 7-8) ⏱️ 12-16 Stunden

**Ziele:**
- ✅ Query Optimization AI
- ✅ Adaptive Query Planning
- ✅ Multi-Tenant Support
- ✅ Advanced Analytics

**Deliverables:**
- AI-based Query Optimizer
- Adaptive Query Planner
- Multi-Tenant Configuration
- Analytics Dashboard

**Tasks:**
1. [ ] AI Query Optimizer (LLM-based AQL Generation)
2. [ ] Adaptive Query Planning (Learn from History)
3. [ ] Multi-Tenant Configuration System
4. [ ] Analytics Dashboard (Query Performance)
5. [ ] A/B Testing Framework (ThemisDB vs UDS3)
6. [ ] Final Documentation & Handover

---

## 6. Erfolgs-Metriken

### 6.1 Performance-Ziele

| Metrik | Aktuell (UDS3) | Ziel (ThemisDB) | Verbesserung |
|--------|----------------|-----------------|--------------|
| **Query Latency** | ~500ms | <200ms | 60% ↓ |
| **Throughput** | 10 q/s | 50 q/s | 400% ↑ |
| **Cache Hit Rate** | 20% | 60%+ | 200% ↑ |
| **RAG Relevance** | 0.75 | 0.85+ | 13% ↑ |
| **Context Depth** | 1 Level | 3 Levels | 200% ↑ |

### 6.2 Qualitäts-Metriken

| Metrik | Ziel | Beschreibung |
|--------|------|--------------|
| **Code Coverage** | 85%+ | Unit + Integration Tests |
| **API Uptime** | 99.9% | Production Availability |
| **Query Success Rate** | 98%+ | Erfolgreiche Queries |
| **RAG Precision** | 0.90+ | Relevanz der Retrieved Docs |
| **User Satisfaction** | 4.5/5 | User Feedback Score |

---

## 7. Risiken & Mitigation

### 7.1 Technische Risiken

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| **ThemisDB Performance** | Medium | Hoch | Benchmark frühzeitig, Fallback zu UDS3 |
| **AQL Komplexität** | Hoch | Medium | Templates + Prompt Engineering |
| **Migration Aufwand** | Medium | Hoch | Phasenweise Migration, Dual-Run |
| **Query Cache Invalidation** | Medium | Medium | TTL-basiert + Manual Purge |
| **Multi-Tenant Isolation** | Niedrig | Hoch | ThemisDB Collections pro Tenant |

### 7.2 Migrations-Strategie

```
┌─────────────────────────────────────────────────────┐
│           Migration Strategy (Dual-Run)             │
│                                                      │
│  Phase 1: Parallel Execution (2 Wochen)            │
│  ┌──────────┐         ┌──────────┐                 │
│  │ UDS3     │ ← 90%   │ ThemisDB │ ← 10%           │
│  │ (Primary)│         │ (Test)   │                 │
│  └──────────┘         └──────────┘                 │
│                                                      │
│  Phase 2: Gradual Shift (4 Wochen)                 │
│  ┌──────────┐         ┌──────────┐                 │
│  │ UDS3     │ ← 50%   │ ThemisDB │ ← 50%           │
│  │          │         │          │                 │
│  └──────────┘         └──────────┘                 │
│                                                      │
│  Phase 3: Primary Switch (2 Wochen)                │
│  ┌──────────┐         ┌──────────┐                 │
│  │ UDS3     │ ← 10%   │ ThemisDB │ ← 90%           │
│  │ (Fallback)│        │ (Primary)│                 │
│  └──────────┘         └──────────┘                 │
└─────────────────────────────────────────────────────┘
```

---

## 8. Zusammenfassung & Nächste Schritte

### 8.1 Kernpunkte

1. **ThemisDB als Primary RAG Backend**: Bessere Performance, einfachere Architektur
2. **AQL Prompt Engineering**: Optimierte Queries für RAG-Szenarien
3. **Agent-getriebene Architektur**: Orchestrierte Multi-Modal-Queries
4. **Graduelle Migration**: Dual-Run mit UDS3 Fallback

### 8.2 Sofort-Maßnahmen (Diese Woche)

- [ ] **Tag 1-2**: AQL Prompt Engineering Dokumentation erstellen
- [ ] **Tag 3-4**: ThemisDBRAGAgent Basis-Implementation
- [ ] **Tag 5**: Unit Tests & Integration Tests
- [ ] **Tag 6-7**: Code Review & Dokumentation

### 8.3 Ressourcen-Bedarf

- **Entwickler**: 1-2 Senior Backend Engineers
- **Zeit**: 8 Wochen (Vollzeit) oder 16 Wochen (50% Allocation)
- **Budget**: Primär interne Ressourcen
- **External Dependencies**: Keine (ThemisDB bereits vorhanden)

---

## 9. Referenzen

- **ThemisDB Documentation**: [Internal Wiki]
- **AQL Language Reference**: `themisdb/docs/aql/language_reference.md`
- **VERITAS Agent Framework**: `backend/agents/INTEGRATION_README.md`
- **UDS3 Architecture**: `uds3/README.md`
- **RAG Best Practices**: [Research Papers on RAG Optimization]

---

**Nächste Schritte:**
1. Review dieser Strategie mit Team
2. Priorisierung der Phasen
3. Start Phase 1: AQL Prompt Engineering Dokumentation
4. Wöchentliche Progress Reviews

**Fragen & Feedback:**
- Technische Fragen → VERITAS Backend Team
- Architektur-Entscheidungen → Tech Lead
- Timeline & Ressourcen → Projekt-Manager
