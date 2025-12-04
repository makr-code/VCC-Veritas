# PostgreSQL & CouchDB Integration Guide

**Status:** ✅ Backends Active, ⏭️ Search API Pending
**Version:** 1.0.0
**Datum:** 11.10.2025

---

## 📊 Executive Summary

PostgreSQL und CouchDB sind **aktive Backends** im UDS3-System, aber nicht in die **UDS3 Search API** integriert:

| Backend | Status | Verwendung | Search API |
|---------|--------|------------|------------|
| **PostgreSQL** | ✅ Active | Document Metadata | ⏭️ Pending |
| **CouchDB** | ✅ Active | File Storage | ❌ Not Applicable |
| **Neo4j** | ✅ Active | Graph Search | ✅ Integrated |
| **ChromaDB** | ⚠️ Fallback | Vector Search | ⚠️ Integrated (Issue) |

---

## 🗄️ PostgreSQL Backend

### Connection Info

```yaml
Host: 192.168.178.94
Port: 5432
Database: vcc_relational_prod
Schema: public
Type: PostgreSQLRelationalBackend
```

### Schema (Aktuell)

```sql
CREATE TABLE documents (
    document_id TEXT PRIMARY KEY,
    file_path TEXT,
    classification TEXT,
    content_length BIGINT,
    legal_terms_count BIGINT,
    created_at TEXT,
    quality_score DOUBLE PRECISION,
    processing_status TEXT
);

-- Zusätzliche Tabellen
CREATE TABLE kv_store (...);        -- Key-Value Store
CREATE TABLE document_keywords (...);  -- Keyword Extraction
```

**Observations:**
- ✅ Tabelle `documents` existiert
- ❌ Keine `content` Spalte (nur Metadaten)
- ❌ Keine `metadata` JSONB Spalte
- ✅ Fokus auf **Document Metadata**, nicht Full-Text

### Available Methods

```python
backend = strategy.relational_backend

# ✅ Available
backend.get_document(document_id)
backend.get_document_count()
backend.get_document_count_by_classification()
backend.get_statistics()
backend.insert_document(...)
backend.delete_document(document_id)

# ❌ NOT Available
backend.execute_sql(query, params)  # ← Missing!
```

### Current Limitations

**Problem:** Kein `execute_sql()` API
**Impact:** Keyword Search nicht möglich
**Workaround:** Neo4j `CONTAINS` für Text-Suche

**Example (nicht möglich):**
```python
# ❌ Would be nice, but NOT available
results = backend.execute_sql("""
    SELECT * FROM documents
    WHERE content @@ to_tsquery('german', 'Photovoltaik')
    LIMIT 10
""")
```

### Integration Options

#### Option 1: Request execute_sql() API (Empfohlen ✅)

**Pros:**
- ✅ Passt in 3-Layer-Architektur
- ✅ UDS3SearchAPI.keyword_search() bereits vorbereitet
- ✅ Sauber und wartbar

**Cons:**
- ⏳ Wartezeit (UDS3 Team)

**Implementation:**
```python
# Already prepared in uds3_search_api.py
async def keyword_search(self, query_text, top_k, filters):
    if not hasattr(backend, 'execute_sql'):
        logger.warning("PostgreSQL execute_sql() not available")
        return []

    # Full-text search
    sql = """
        SELECT document_id, content, metadata,
               ts_rank(to_tsvector('german', content),
                       to_tsquery('german', %s)) AS score
        FROM documents
        WHERE to_tsvector('german', content) @@ to_tsquery('german', %s)
        ORDER BY score DESC
        LIMIT %s
    """
    results = backend.execute_sql(sql, (query_text, query_text, top_k))
    # ... convert to SearchResult
```

---

#### Option 2: Direct psycopg2 Wrapper (Quick & Dirty ⚠️)

**Pros:**
- ✅ Sofort verfügbar
- ✅ Volle SQL-Kontrolle

**Cons:**
- ❌ Bricht 3-Layer-Architektur
- ❌ Keine UDS3 Error-Handling
- ❌ Wartungsproblem

**Implementation:**
```python
# NOT recommended, but possible
import psycopg2

def direct_postgres_search(query_text, top_k=10):
    conn = psycopg2.connect(
        host='192.168.178.94',
        port=5432,
        user='postgres',
        password='postgres',
        database='vcc_relational_prod'
    )
    cursor = conn.cursor()

    # Direct SQL
    cursor.execute("""
        SELECT document_id, content, metadata
        FROM documents
        WHERE content @@ to_tsquery('german', %s)
        LIMIT %s
    """, (query_text, top_k))

    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
```

---

#### Option 3: Neo4j CONTAINS (Production-Ready ✅)

**Pros:**
- ✅ Funktioniert **JETZT** (1930 Dokumente)
- ✅ Bereits in UDS3 Search API integriert
- ✅ Gut genug für Production

**Cons:**
- ⚠️ Neo4j ist Graph-DB, nicht optimiert für Full-Text
- ⚠️ Keine PostgreSQL Full-Text-Features (ts_rank, Stemming, etc.)

**Current Implementation:**
```python
# Already working in uds3_search_api.py
async def graph_search(query_text, top_k):
    cypher = """
    MATCH (d:Document)
    WHERE toLower(d.content) CONTAINS toLower($query)
       OR toLower(d.name) CONTAINS toLower($query)
    RETURN d
    LIMIT $top_k
    """
    results = backend.execute_query(cypher, {'query': query_text, 'top_k': top_k})
    # ... working! ✅
```

**Recommendation:** **Option 3 NOW** + Request **Option 1 for Future**

---

## 📁 CouchDB Backend

### Connection Info

```yaml
Host: 192.168.178.94
Port: 32931
URL: http://couchdb:couchdb@192.168.178.94:32931
Type: CouchDBAdapter
```

### Available Methods

```python
backend = strategy.file_backend

# Document Operations
backend.create_document(doc_id, data)
backend.get_document(doc_id)
backend.update_document(doc_id, data)
backend.delete_document(doc_id)

# Asset Operations (Files)
backend.store_asset(file_id, file_data)
backend.delete_asset(file_id)

# Queries
backend.query(map_fun, reduce_fun)

# UDS3 Integration
backend.get_uds3_metadata(doc_id)
backend.validate_uds3_consistency()
```

### Use Cases

#### 1. PDF Storage

```python
# Upload PDF to CouchDB
with open('document.pdf', 'rb') as f:
    file_data = f.read()

backend.store_asset(
    file_id='doc_001_pdf',
    file_data=file_data
)

# Retrieve PDF
pdf_data = backend.get_document('doc_001_pdf')
```

#### 2. Document Metadata

```python
# Store document metadata
doc = {
    '_id': 'doc_001',
    'title': 'LBO BW § 58',
    'type': 'regulation',
    'file_ref': 'doc_001_pdf',
    'extracted_text': '...'
}

backend.create_document('doc_001', doc)
```

#### 3. Full Workflow: PDF → Search

```python
# 1. Upload PDF to CouchDB
backend.store_asset('doc_001_pdf', pdf_data)

# 2. Extract text (OCR/PDF parsing)
extracted_text = extract_text_from_pdf(pdf_data)

# 3. Store in PostgreSQL (metadata)
postgres_backend.insert_document(
    document_id='doc_001',
    file_path='couchdb://doc_001_pdf',
    classification='regulation',
    content_length=len(extracted_text)
)

# 4. Store in Neo4j (graph + text)
neo4j_backend.execute_query("""
    CREATE (d:Document {
        document_id: $doc_id,
        name: $name,
        content: $content,
        document_type: 'regulation'
    })
""", {'doc_id': 'doc_001', 'name': 'LBO BW § 58', 'content': extracted_text})

# 5. Generate embedding and store in ChromaDB
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
embedding = model.encode(extracted_text).tolist()

chromadb_backend.add_vector(
    document_id='doc_001',
    embedding=embedding,
    metadata={'title': 'LBO BW § 58'}
)

# Now searchable via UDS3 Search API! ✅
```

---

## 🔄 Integration Roadmap

### Phase 1: Current State (NOW) ✅

**Status:** Production-ready with Neo4j

```python
# Use Neo4j for text search
from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

agent = UDS3HybridSearchAgent(strategy)
results = await agent.hybrid_search(
    query="Photovoltaik",
    search_types=["graph"],  # Neo4j only
    weights={"graph": 1.0}
)
```

**Backends:**
- ✅ Neo4j: 1930 documents (text search working)
- ⚠️ ChromaDB: Fallback docs (Remote API issue)
- ⏭️ PostgreSQL: Metadata only (no content search)
- ✅ CouchDB: File storage

---

### Phase 2: PostgreSQL execute_sql() API (2-4 Wochen)

**Goal:** Enable PostgreSQL keyword search

**Tasks:**
1. Request `execute_sql()` API from UDS3 team
2. Add `content` column to documents table
3. Implement Full-Text Search indexes
4. Test UDS3SearchAPI.keyword_search()

**Expected Result:**
```python
# Full Hybrid Search
results = await agent.hybrid_search(
    query="Photovoltaik",
    search_types=["vector", "graph", "keyword"],
    weights={"vector": 0.4, "graph": 0.4, "keyword": 0.2}
)
```

---

### Phase 3: ChromaDB Remote API Fix (1-2 Wochen)

**Goal:** Fix ChromaDB fallback docs issue

**Tasks:**
1. Investigate ChromaDB Remote Backend API
2. Test with local ChromaDB (not Remote)
3. Contact UDS3 team for Remote API configuration
4. Verify vector search with real embeddings

**Expected Result:**
```python
# Vector search working
results = await agent.vector_search("Photovoltaik", top_k=10)
# Returns: Real documents, not fallback_doc_0/1/2
```

---

### Phase 4: Full Stack Integration (2-3 Wochen)

**Goal:** Complete 4-backend hybrid search

**Workflow:**
```
PDF Upload → CouchDB (file storage)
     ↓
Text Extraction → PostgreSQL (metadata + full-text)
     ↓
Embedding Generation → ChromaDB (vector search)
     ↓
Relationship Extraction → Neo4j (graph search)
     ↓
UDS3 Search API → Hybrid Results
```

**Expected Performance:**
- Latency: <500ms (all backends)
- Precision@10: >0.80 (hybrid search)
- Coverage: 100% (all document types)

---

## 🎯 Recommendations

### Immediate (Diese Woche)

1. ✅ **Use Neo4j for Production**
   - 1930 documents ready
   - Text search working
   - Deploy NOW with `search_types=["graph"]`

2. ⏭️ **Request PostgreSQL execute_sql() API**
   - Email UDS3 team
   - Specify use case (full-text search)
   - Provide SQL examples

3. 📁 **Use CouchDB for File Storage**
   - Upload PDFs
   - Store metadata
   - Reference in other backends

### Short-Term (Nächste 2 Wochen)

4. ⚠️ **Fix ChromaDB Remote API**
   - Investigate fallback docs
   - Test with local ChromaDB
   - Contact UDS3 team

5. 📊 **Document Migration (Optional)**
   - Migrate Neo4j docs to PostgreSQL
   - Add `content` column
   - Enable full-text search

### Long-Term (Nächster Monat)

6. 🔄 **Full Hybrid Search**
   - Vector + Graph + Keyword
   - 4-backend integration
   - Performance benchmarks

7. 📈 **Advanced Features**
   - Query caching (Redis)
   - Advanced re-ranking (Cross-Encoder)
   - User feedback integration

---

## 📝 Code Examples

### Current Production Setup (Neo4j-Only)

```python
from uds3.uds3_core import get_optimized_unified_strategy
from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

# Initialize
strategy = get_optimized_unified_strategy()
agent = UDS3HybridSearchAgent(strategy)

# Search (Neo4j only)
results = await agent.hybrid_search(
    query="Was regelt § 58 LBO BW?",
    top_k=10,
    search_types=["graph"],
    weights={"graph": 1.0}
)

# Results
for result in results:
    print(f"Name: {result.metadata.get('name')}")
    print(f"Type: {result.metadata.get('document_type')}")
    print(f"Content: {result.content[:200]}...")
```

### Future: Full Hybrid (After PostgreSQL API)

```python
# Full hybrid search (future)
results = await agent.hybrid_search(
    query="Photovoltaik Anforderungen",
    top_k=10,
    search_types=["vector", "graph", "keyword"],
    weights={
        "vector": 0.4,    # ChromaDB (semantic similarity)
        "graph": 0.4,     # Neo4j (relationships)
        "keyword": 0.2    # PostgreSQL (exact terms) ← Future
    }
)
```

### CouchDB File Upload

```python
from uds3.uds3_core import get_optimized_unified_strategy

strategy = get_optimized_unified_strategy()
couchdb = strategy.file_backend

# Upload PDF
with open('document.pdf', 'rb') as f:
    pdf_data = f.read()

couchdb.store_asset(
    file_id='lbo_bw_58_pdf',
    file_data=pdf_data
)

# Store metadata
doc = {
    '_id': 'lbo_bw_58',
    'title': 'LBO BW § 58 Photovoltaik',
    'type': 'regulation',
    'file_ref': 'lbo_bw_58_pdf',
    'created_at': '2025-10-11'
}

couchdb.create_document('lbo_bw_58', doc)
```

---

## 📊 Summary

| Backend | Status | Documents | Search API | Use Case |
|---------|--------|-----------|------------|----------|
| **PostgreSQL** | ✅ Active | 0 | ⏭️ Pending | Document Metadata |
| **CouchDB** | ✅ Active | N/A | ❌ N/A | File Storage (PDFs) |
| **Neo4j** | ✅ Active | 1930 | ✅ Working | Text + Graph Search |
| **ChromaDB** | ⚠️ Issue | 0 (fallback) | ⚠️ Fallback | Vector Search |

**Production Recommendation:** Deploy NOW with **Neo4j-Only Search**

**Next Steps:**
1. ✅ Deploy Neo4j-based search (production-ready)
2. ⏭️ Request PostgreSQL execute_sql() API
3. ⚠️ Fix ChromaDB Remote API
4. 📁 Use CouchDB for file storage

---

**Last Updated:** 11.10.2025
**Version:** 1.0.0
**Status:** ✅ Neo4j Production-Ready, ⏭️ PostgreSQL/ChromaDB Pending
