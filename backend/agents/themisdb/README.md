# ThemisDB Agent Framework - OOP Best-Practice Implementation

**Version:** 2.0  
**Datum:** 3. Dezember 2025  
**Status:** ✅ Production-Ready

---

## Übersicht

Dieses Framework implementiert einen **RAG (Retrieval-Augmented Generation) Agent** mit **austauschbaren Database-Adaptern** nach OOP Best-Practices.

### Hauptfeatures

✅ **Austauschbare Adapter**: ThemisDB ⇄ UDS3 Polyglot  
✅ **SOLID Principles**: Klare Verantwortlichkeiten, erweiterbar  
✅ **Design Patterns**: Adapter, Factory, Strategy, Dependency Injection  
✅ **Type-Safe**: Vollständige Type-Hints, Protocols, Generics  
✅ **Performance**: Query Caching, Optimierung, Monitoring  
✅ **Testbar**: Dependency Injection, Mocking-freundlich  

---

## Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                   ThemisDB RAG Agent                         │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            Facade: ThemisDBRAGAgent                   │  │
│  │  - retrieve()                                         │  │
│  │  - retrieve_with_context()                           │  │
│  │  - hybrid_search()                                    │  │
│  └────────┬──────────────────────────────────┬──────────┘  │
│           │                                   │              │
│           ▼                                   ▼              │
│  ┌────────────────┐                 ┌────────────────┐     │
│  │ Query Planner  │                 │ Query Strategy │     │
│  │ (AQLPlanner)   │                 │ (Standard)     │     │
│  └────────┬───────┘                 └────────┬───────┘     │
│           │                                   │              │
│           └──────────────┬────────────────────┘              │
│                          ▼                                   │
│              ┌───────────────────────┐                      │
│              │  IDatabaseAdapter     │  ← Interface        │
│              │  (Abstract)           │                      │
│              └───────────┬───────────┘                      │
│                          │                                   │
│           ┌──────────────┴──────────────┐                  │
│           ▼                              ▼                   │
│  ┌─────────────────┐          ┌─────────────────┐          │
│  │ ThemisDBAdapter │          │  UDS3Adapter    │          │
│  │ - vector_search │          │ - vector_search │          │
│  │ - graph_traverse│          │ - graph_traverse│          │
│  │ - execute_aql   │          │ - (multi-db)    │          │
│  └─────────────────┘          └─────────────────┘          │
│           │                              │                   │
│           ▼                              ▼                   │
│    ┌──────────┐                  ┌──────────┐              │
│    │ ThemisDB │                  │   UDS3   │              │
│    │ (v1.x)   │                  │ Polyglot │              │
│    └──────────┘                  └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Installation

```python
# Kein pip install notwendig - Framework ist Teil von VERITAS
from backend.agents.themisdb import create_rag_agent
```

### 2. Einfache Verwendung (Auto-Select)

```python
import asyncio
from backend.agents.themisdb import create_rag_agent

async def main():
    # Automatische Adapter-Auswahl (ThemisDB → UDS3 Fallback)
    agent = await create_rag_agent()
    
    # Dokumente abrufen
    results = await agent.retrieve(
        query="BGB Vertragsrecht Minderjährige",
        top_k=5,
        domain="verwaltungsrecht"
    )
    
    for doc in results:
        print(f"{doc.doc_id}: {doc.score:.3f} - {doc.content[:100]}")

asyncio.run(main())
```

### 3. Spezifischen Adapter wählen

```python
from backend.agents.themisdb import (
    create_rag_agent,
    create_themisdb_agent,
    create_uds3_agent,
    DatabaseType
)

# Option 1: ThemisDB explizit
agent = await create_rag_agent(adapter_type=DatabaseType.THEMIS)

# Option 2: UDS3 explizit
agent = await create_rag_agent(adapter_type=DatabaseType.UDS3)

# Option 3: Factory-Funktionen
themis_agent = await create_themisdb_agent()
uds3_agent = await create_uds3_agent()
```

### 4. Erweiterte Verwendung

```python
# Hybrid Search (Vector + Graph)
results = await agent.hybrid_search(
    query="Immissionsschutz TA Luft",
    top_k=10
)

# Context-Enriched Retrieval
results = await agent.retrieve_with_context(
    query="DIN EN Normen Brandschutz",
    top_k=5,
    context_depth=2  # Graph-Tiefe
)

# Custom Options
results = await agent.retrieve(
    query="Datenschutz DSGVO",
    top_k=10,
    domain="verwaltungsrecht",
    threshold=0.75,
    collection="legal_documents",
    filters={"year": 2023, "language": "de"}
)
```

---

## SOLID Principles

### Single Responsibility Principle ✅

Jede Klasse hat **eine klar definierte Aufgabe**:

```python
# ✅ Gut: Klare Verantwortung
class VectorSearchTemplate(QueryTemplate):
    """Nur für Vector Search Queries"""
    pass

class HybridQueryTemplate(QueryTemplate):
    """Nur für Hybrid Queries"""
    pass

# ❌ Schlecht: Zu viele Verantwortlichkeiten
class AllInOneTemplate:
    """Macht Vector, Graph, Document, Cache, Logging, ..."""
    pass
```

### Open/Closed Principle ✅

**Erweiterbar ohne Modifikation**:

```python
# Neuen Query-Typ hinzufügen OHNE bestehenden Code zu ändern
class CustomTemplate(QueryTemplate):
    def build_query(self, context):
        return "CUSTOM AQL QUERY"

# Registrieren
QueryTemplateFactory.register_template(
    QueryType.CUSTOM,
    CustomTemplate
)

# Neuen Adapter hinzufügen
class PostgreSQLAdapter(IDatabaseAdapter):
    # Implementierung...
    pass

DatabaseAdapterFactory.register_adapter(
    DatabaseType.POSTGRESQL,
    PostgreSQLAdapter
)
```

### Liskov Substitution Principle ✅

**Adapter sind austauschbar**:

```python
# Code funktioniert mit BEIDEN Adaptern ohne Änderung
async def process_query(adapter: IDatabaseAdapter, query: str):
    results = await adapter.vector_search(query, SearchOptions(top_k=5))
    return results

# Funktioniert mit ThemisDB
themis_adapter = ThemisDBAdapter(config)
results = await process_query(themis_adapter, "test")

# Funktioniert mit UDS3
uds3_adapter = UDS3Adapter(config)
results = await process_query(uds3_adapter, "test")
```

### Interface Segregation Principle ✅

**Fokussierte Interfaces statt monolithischer**:

```python
# ✅ Gut: Kleine, fokussierte Protocols
class EmbeddingProvider(Protocol):
    async def embed_text(self, text: str) -> List[float]: ...

class CacheProvider(Protocol):
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...

# ❌ Schlecht: Monolithisches Interface
class GodInterface(Protocol):
    def embed(self): ...
    def cache(self): ...
    def query(self): ...
    def validate(self): ...
    # ... 20 weitere Methoden
```

### Dependency Inversion Principle ✅

**Code gegen Abstraktion, nicht Implementierung**:

```python
# ✅ Gut: Dependency Injection mit Interface
class ThemisDBRAGAgent:
    def __init__(
        self,
        adapter: IDatabaseAdapter,  # ← Interface!
        planner: QueryPlanner,      # ← Interface!
        cache: CacheProvider        # ← Interface!
    ):
        self._adapter = adapter
        self._planner = planner
        self._cache = cache

# ❌ Schlecht: Konkrete Abhängigkeiten
class BadAgent:
    def __init__(self):
        self.adapter = ThemisDBAdapter()  # ← Konkret!
        self.planner = AQLQueryPlanner()  # ← Konkret!
```

---

## Design Patterns

### Adapter Pattern

**Problem**: ThemisDB und UDS3 haben unterschiedliche APIs  
**Lösung**: Gemeinsames Interface `IDatabaseAdapter`

```python
# Gemeinsames Interface
class IDatabaseAdapter(abc.ABC):
    @abc.abstractmethod
    async def vector_search(self, query, options): ...

# ThemisDB implementiert Interface
class ThemisDBAdapter(IDatabaseAdapter):
    async def vector_search(self, query, options):
        # ThemisDB-spezifische Implementierung
        response = await self.client.post("/api/vector/search", ...)
        return self._transform_results(response)

# UDS3 implementiert Interface
class UDS3Adapter(IDatabaseAdapter):
    async def vector_search(self, query, options):
        # UDS3-spezifische Implementierung
        results = await self.uds3.query_across_databases(...)
        return self._transform_results(results)
```

### Factory Pattern

**Problem**: Komplexe Adapter-Erstellung  
**Lösung**: Factory übernimmt Erstellung

```python
# Factory
adapter = await DatabaseAdapterFactory.create(config)

# Automatische Auswahl
adapter = await AdapterSelector.select_best_adapter()
```

### Strategy Pattern

**Problem**: Unterschiedliche Query-Strategien  
**Lösung**: Austauschbare Strategy-Klassen

```python
class StandardQueryStrategy(QueryStrategy):
    async def execute(self, plan, context):
        # Standard-Ausführung mit Caching
        ...

class OptimizedQueryStrategy(QueryStrategy):
    async def execute(self, plan, context):
        # Optimierte Ausführung mit Parallelisierung
        ...

# Austauschbar
agent = ThemisDBRAGAgent(
    adapter=adapter,
    strategy=OptimizedQueryStrategy(...)
)
```

### Template Method Pattern

**Problem**: Query-Building-Logik wiederholt sich  
**Lösung**: Template mit überschreibbaren Methoden

```python
class QueryTemplate(abc.ABC):
    @abc.abstractmethod
    def build_query(self, context): pass
    
    @abc.abstractmethod
    def extract_bind_vars(self, context): pass
    
    # Template Method mit Default-Implementierung
    def optimize_query(self, query, context):
        if context.complexity == QueryComplexity.LOW:
            query = f"/* +cache */\n{query}"
        return query
```

---

## Erweiterbarkeit

### Neuen Adapter hinzufügen

```python
# 1. Interface implementieren
class MongoDBAdapter(IDatabaseAdapter):
    async def connect(self): ...
    async def vector_search(self, query, options): ...
    async def graph_traverse(self, ...): ...
    # ... weitere Methoden

# 2. Registrieren
DatabaseAdapterFactory.register_adapter(
    DatabaseType.MONGODB,
    MongoDBAdapter
)

# 3. Verwenden
agent = await create_rag_agent(adapter_type=DatabaseType.MONGODB)
```

### Neue Query-Template hinzufügen

```python
# 1. Template implementieren
class FullTextSearchTemplate(QueryTemplate):
    def build_query(self, context):
        return "FOR doc IN @@collection FILTER FULLTEXT(...) RETURN doc"
    
    def extract_bind_vars(self, context):
        return {"@collection": context.metadata["collection"]}

# 2. Registrieren
QueryTemplateFactory.register_template(
    QueryType.FULL_TEXT,
    FullTextSearchTemplate
)
```

---

## Testing

### Unit Tests mit Mocks

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_vector_search():
    # Mock Adapter
    mock_adapter = MagicMock(spec=IDatabaseAdapter)
    mock_adapter.vector_search = AsyncMock(return_value=[
        DocumentResult(
            doc_id="doc1",
            content="Test content",
            score=0.95,
            metadata={},
            source="themisdb"
        )
    ])
    
    # Test Agent
    agent = ThemisDBRAGAgent(adapter=mock_adapter)
    results = await agent.retrieve("test query", top_k=5)
    
    assert len(results) == 1
    assert results[0].doc_id == "doc1"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_themisdb_integration():
    # Echter ThemisDB Adapter (Testumgebung)
    config = DatabaseConfig(
        db_type=DatabaseType.THEMIS,
        host="localhost",
        port=8765
    )
    adapter = await DatabaseAdapterFactory.create(config)
    agent = ThemisDBRAGAgent(adapter)
    
    # Integration Test
    results = await agent.retrieve("test", top_k=5)
    assert len(results) > 0
    
    await adapter.disconnect()
```

---

## Performance

### Caching

```python
# Automatisches Caching für low-cost Queries
results = await agent.retrieve("query")  # ← Cache miss
results = await agent.retrieve("query")  # ← Cache hit 🎯

# Cache leeren
agent.clear_cache()
```

### Monitoring

```python
# Agent-Statistiken
stats = agent.get_stats()
print(stats)
# {
#   "total_queries": 100,
#   "successful_queries": 95,
#   "cache_hit_rate": 0.45,
#   "avg_latency_ms": 87.3
# }

# Backend-Info
info = agent.get_backend_info()
print(info)
# {
#   "type": "themisdb",
#   "connected": True,
#   "features": ["vector_search", "graph_traversal", ...]
# }
```

---

## Zusammenfassung

### Vorteile der OOP-Implementierung

✅ **Wartbar**: Klare Struktur, Single Responsibility  
✅ **Erweiterbar**: Neue Adapter/Templates ohne Code-Änderung  
✅ **Testbar**: Dependency Injection, Mocking-freundlich  
✅ **Type-Safe**: Vollständige Type-Hints, IDE-Support  
✅ **Performance**: Caching, Optimierung, Monitoring  
✅ **Dokumentiert**: Klare Interfaces, Beispiele  

### Migration von v1.0 → v2.0

```python
# Alt (v1.0)
from backend.agents.veritas_themisdb_rag_agent import (
    ThemisDBRAGAgent
)
adapter = ThemisDBAdapter(config)
agent = ThemisDBRAGAgent(adapter, config)

# Neu (v2.0)
from backend.agents.themisdb import create_rag_agent
agent = await create_rag_agent()  # Auto-select
```

---

**Fragen?**  
→ Backend Team  
→ Dokumentation: `themisdb/docs/`  
→ Tests: `tests/agents/test_themisdb_rag_agent.py`
