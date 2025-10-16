# UDS3 API Layer Architecture

**Date:** 11. Oktober 2025  
**Purpose:** Architecture-Entscheidung für Backend-Kommunikation

---

## 🎯 Problem

**Frage:** Soll VERITAS die UDS3-Backends **direkt** ansprechen oder über die **offizielle Database API**?

**Aktueller Stand:**
- ❌ `veritas_uds3_hybrid_agent.py` nutzt `backend.execute_query()` direkt
- ❌ Bypass der UDS3 Abstraction-Layer
- ❌ Kein Error Handling, Retry Logic, Security Features

**Optionen:**
- **A) Direkt:** `strategy.graph_backend.execute_query(cypher, params)` ❌
- **B) Database API:** `from uds3.database.database_api_neo4j import Neo4jGraphBackend` ✅
- **C) UDS3 erweitern:** Neue High-Level Search APIs in `uds3_core.py` ⭐

---

## 🏗️ UDS3 Database API Architecture

### Layer 1: Backend Implementations (database/)

```
uds3/database/
├── database_api_base.py          # Abstract Base Classes
│   ├── DatabaseBackend           # Common interface
│   ├── GraphDatabaseBackend      # Neo4j abstraction
│   └── VectorDatabaseBackend     # ChromaDB abstraction
│
├── database_api_neo4j.py         # Neo4j implementation ✅
│   ├── connect() / disconnect()
│   ├── execute_query(cypher, params)  # ✅ Was wir nutzen!
│   ├── Retry Logic (3 attempts, exponential backoff)
│   ├── Error Handling (Syntax, Constraints, Deadlocks)
│   └── Connection Pool Management
│
├── database_api_chromadb_remote.py  # ChromaDB Remote ⚠️
│   ├── add_vector(vector, metadata, doc_id, collection)
│   ├── search_similar(query_vector, n_results, collection)
│   └── Remote API Wrapper
│
└── database_api_postgresql.py    # PostgreSQL implementation ⏭️
    ├── get_document(doc_id)
    ├── insert_document(data)
    └── No direct SQL query API ❌
```

### Layer 2: Unified Strategy (uds3_core.py)

```python
class UnifiedDatabaseStrategy:
    def __init__(self):
        self.graph_backend: Neo4jGraphBackend      # Layer 1
        self.vector_backend: ChromaRemoteVectorBackend
        self.relational_backend: PostgreSQLRelationalBackend
    
    # High-level APIs (missing search methods!)
    def create_document(doc_data)  # ✅ Exists
    def update_document(doc_id)    # ✅ Exists
    def delete_document(doc_id)    # ✅ Exists
    
    def search_documents(query)    # ❌ MISSING!
    def hybrid_search(query)       # ❌ MISSING!
    def vector_search(embedding)   # ❌ MISSING!
```

**Problem:** UDS3 hat **keine High-Level Search APIs**!

---

## ✅ Empfohlene Lösung: UDS3 erweitern

### Option C: High-Level Search APIs in `uds3_core.py`

**Vorteil:**
- ✅ Nutzt existierende Database API Layer (Retry, Error Handling)
- ✅ Abstrahiert Backend-Details (Neo4j, ChromaDB, PostgreSQL)
- ✅ Wiederverwendbar für andere Projekte
- ✅ Type-Safe mit Dataclasses
- ✅ Dokumentiert und getestet

**Implementation:**

```python
# uds3/uds3_search_api.py (NEW FILE)

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum

@dataclass
class SearchResult:
    """Single search result with metadata"""
    document_id: str
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str  # "vector", "graph", "relational"
    
@dataclass
class SearchQuery:
    """Search query configuration"""
    query_text: str
    top_k: int = 10
    filters: Optional[Dict] = None
    search_types: List[str] = None  # ["vector", "graph", "keyword"]
    weights: Optional[Dict[str, float]] = None  # {"vector": 0.5, "graph": 0.3, "keyword": 0.2}


class UDS3SearchAPI:
    """High-Level Search API für UnifiedDatabaseStrategy"""
    
    def __init__(self, strategy: UnifiedDatabaseStrategy):
        self.strategy = strategy
    
    async def vector_search(
        self, 
        query_embedding: List[float], 
        top_k: int = 10,
        collection: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Semantic vector search using ChromaDB
        
        Uses: strategy.vector_backend.search_similar()
        """
        backend = self.strategy.vector_backend
        
        # Delegate to Database API Layer
        raw_results = backend.search_similar(
            query_vector=query_embedding,
            n_results=top_k,
            collection=collection
        )
        
        # Normalize to SearchResult
        results = []
        for raw in raw_results:
            results.append(SearchResult(
                document_id=raw.get('id', 'unknown'),
                content=raw.get('metadata', {}).get('content', ''),
                metadata=raw.get('metadata', {}),
                score=1.0 - raw.get('distance', 0.5),  # Convert distance to similarity
                source='vector'
            ))
        
        return results
    
    async def graph_search(
        self,
        query_text: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Graph-based search using Neo4j
        
        Uses: strategy.graph_backend.execute_query()
        """
        backend = self.strategy.graph_backend
        
        # Cypher query for text search
        cypher = """
        MATCH (d:Document)
        WHERE toLower(d.content) CONTAINS toLower($query)
           OR toLower(d.name) CONTAINS toLower($query)
        OPTIONAL MATCH (d)-[r:RELATED_TO]-(related:Document)
        RETURN d, collect(related) AS related_docs
        LIMIT $top_k
        """
        
        # Delegate to Database API Layer (with retry logic!)
        raw_results = backend.execute_query(
            cypher, 
            params={'query': query_text, 'top_k': top_k}
        )
        
        # Normalize to SearchResult
        results = []
        for record in raw_results:
            doc_node = record.get('d')
            props = doc_node._properties if hasattr(doc_node, '_properties') else {}
            
            results.append(SearchResult(
                document_id=props.get('document_id', 'unknown'),
                content=props.get('content', ''),
                metadata=props,
                score=1.0,  # Default score (can be improved)
                source='graph'
            ))
        
        return results
    
    async def keyword_search(
        self,
        query_text: str,
        top_k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        Keyword search using PostgreSQL full-text search
        
        Uses: strategy.relational_backend.execute_sql() (if available)
        """
        backend = self.strategy.relational_backend
        
        # Check if SQL query API exists
        if not hasattr(backend, 'execute_sql'):
            logger.warning("PostgreSQL backend has no execute_sql() - skipping keyword search")
            return []
        
        # SQL full-text search (PostgreSQL)
        sql = """
        SELECT document_id, content, metadata, 
               ts_rank(to_tsvector('german', content), plainto_tsquery('german', %s)) AS score
        FROM documents
        WHERE to_tsvector('german', content) @@ plainto_tsquery('german', %s)
        ORDER BY score DESC
        LIMIT %s
        """
        
        # Delegate to Database API Layer
        raw_results = backend.execute_sql(sql, params=(query_text, query_text, top_k))
        
        # Normalize to SearchResult
        results = []
        for row in raw_results:
            results.append(SearchResult(
                document_id=row['document_id'],
                content=row['content'],
                metadata=row.get('metadata', {}),
                score=row['score'],
                source='keyword'
            ))
        
        return results
    
    async def hybrid_search(
        self,
        search_query: SearchQuery
    ) -> List[SearchResult]:
        """
        Hybrid search combining Vector + Graph + Keyword
        
        Weights:
        - vector: 0.5 (default)
        - graph: 0.3 (default)
        - keyword: 0.2 (default)
        """
        weights = search_query.weights or {
            "vector": 0.5,
            "graph": 0.3,
            "keyword": 0.2
        }
        
        all_results = []
        
        # 1. Vector Search (if enabled)
        if "vector" in search_query.search_types and weights.get("vector", 0) > 0:
            # Generate embedding from query_text (needs sentence-transformers)
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            embedding = model.encode(search_query.query_text).tolist()
            
            vector_results = await self.vector_search(embedding, search_query.top_k * 2)
            for result in vector_results:
                result.score *= weights["vector"]
            all_results.extend(vector_results)
        
        # 2. Graph Search (if enabled)
        if "graph" in search_query.search_types and weights.get("graph", 0) > 0:
            graph_results = await self.graph_search(search_query.query_text, search_query.top_k * 2)
            for result in graph_results:
                result.score *= weights["graph"]
            all_results.extend(graph_results)
        
        # 3. Keyword Search (if enabled)
        if "keyword" in search_query.search_types and weights.get("keyword", 0) > 0:
            keyword_results = await self.keyword_search(
                search_query.query_text, 
                search_query.top_k * 2,
                search_query.filters
            )
            for result in keyword_results:
                result.score *= weights["keyword"]
            all_results.extend(keyword_results)
        
        # 4. Merge and Re-Rank
        merged = {}
        for result in all_results:
            doc_id = result.document_id
            if doc_id in merged:
                # Combine scores
                merged[doc_id].score += result.score
            else:
                merged[doc_id] = result
        
        # Sort by final score
        final_results = sorted(merged.values(), key=lambda r: r.score, reverse=True)
        
        return final_results[:search_query.top_k]
```

---

## 🔧 Integration in VERITAS

### Before (Direct Backend Access) ❌

```python
# backend/agents/veritas_uds3_hybrid_agent.py (OLD)

async def _query_neo4j_direct(self, query, top_k):
    # Direct backend access - NO error handling!
    backend = self.strategy.graph_backend
    results = backend.execute_query(cypher, params)  # ❌ No retry, no error handling
    return results
```

### After (Database API Layer) ✅

```python
# backend/agents/veritas_uds3_hybrid_agent.py (NEW)

from uds3.uds3_search_api import UDS3SearchAPI, SearchQuery

class UDS3HybridSearchAgent:
    def __init__(self, strategy):
        self.strategy = strategy
        self.search_api = UDS3SearchAPI(strategy)  # ✅ Use UDS3 Search API
    
    async def hybrid_search(self, query, top_k=10, weights=None):
        search_query = SearchQuery(
            query_text=query,
            top_k=top_k,
            search_types=["vector", "graph", "keyword"],
            weights=weights or {"vector": 0.5, "graph": 0.3, "keyword": 0.2}
        )
        
        # Delegate to UDS3 Search API ✅
        results = await self.search_api.hybrid_search(search_query)
        
        return results
```

**Benefits:**
- ✅ Uses Database API Layer (retry logic, error handling)
- ✅ Type-safe (SearchResult dataclass)
- ✅ Reusable (other projects can use UDS3SearchAPI)
- ✅ Testable (mock UDS3SearchAPI)
- ✅ Maintainable (centralized search logic)

---

## 📊 Comparison

| Approach | Pros | Cons | Recommended |
|----------|------|------|-------------|
| **A) Direct Backend** | Fast, simple | ❌ No error handling, no retry, fragile | ❌ NO |
| **B) Database API Only** | Good error handling | ⚠️ Verbose, low-level, scattered logic | ⭐ OK |
| **C) UDS3 Search API** | Best practices, reusable, type-safe | 📝 Needs UDS3 extension | ⭐⭐⭐ YES |

---

## ✅ Decision

**Implement Option C: UDS3 Search API Extension**

### Next Steps:

1. **Create `uds3/uds3_search_api.py`** (500 LOC)
   - `UDS3SearchAPI` class
   - `vector_search()`, `graph_search()`, `keyword_search()`
   - `hybrid_search()` with weighted re-ranking
   - `SearchResult`, `SearchQuery` dataclasses

2. **Update `veritas_uds3_hybrid_agent.py`** (150 LOC)
   - Replace direct backend calls
   - Use `UDS3SearchAPI`
   - Simplified code (from 1000 LOC → 150 LOC)

3. **Create Tests** (300 LOC)
   - `test_uds3_search_api.py`
   - Mock backends
   - Integration tests

4. **Documentation** (200 LOC)
   - `docs/UDS3_SEARCH_API.md`
   - API reference
   - Usage examples

**Estimated Time:** 2-3h

---

## 🎯 Benefits

**For VERITAS:**
- ✅ Clean architecture (separation of concerns)
- ✅ Robust error handling (retry, fallback)
- ✅ Type safety (SearchResult dataclass)
- ✅ -850 LOC in veritas_uds3_hybrid_agent.py

**For UDS3:**
- ✅ Reusable Search API for other projects
- ✅ High-level abstraction over Database APIs
- ✅ Documented and tested
- ✅ Production-ready

---

**Status:** 📝 Architecture Decision Documented  
**Next:** Implement `uds3/uds3_search_api.py`
