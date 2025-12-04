# ThemisDB AQL Prompt Engineering für RAG-Optimierung

**Version:** 1.0
**Datum:** 3. Dezember 2025
**Zielgruppe:** Backend-Entwickler, RAG Engineers, Data Scientists
**Zweck:** Best Practices für AQL-Query-Generierung in RAG-Pipelines

---

## Inhaltsverzeichnis

1. [Einführung](#1-einführung)
2. [AQL Grundlagen für RAG](#2-aql-grundlagen-für-rag)
3. [Query Patterns](#3-query-patterns)
4. [Performance Optimization](#4-performance-optimization)
5. [Domain-spezifische Templates](#5-domain-spezifische-templates)
6. [Error Handling & Fallbacks](#6-error-handling--fallbacks)
7. [Monitoring & Debugging](#7-monitoring--debugging)

---

## 1. Einführung

### 1.1 Was ist AQL Prompt Engineering?

AQL (Themis Query Language) Prompt Engineering ist der Prozess, natürliche Sprachanfragen in optimierte ThemisDB-Queries zu konvertieren. Im Kontext von RAG (Retrieval-Augmented Generation) bedeutet dies:

- **Input**: User-Query in natürlicher Sprache (z.B. "Finde BGB-Paragraphen zu Vertragsrecht")
- **Output**: Optimierte AQL-Query mit Vector Search, Graph Traversal, etc.
- **Ziel**: Maximale Relevanz bei minimaler Latency

### 1.2 Warum AQL für RAG?

| Feature | Vorteil für RAG |
|---------|----------------|
| **Multi-Model** | Vector + Graph + Document in einem Query |
| **Flexible Syntax** | Komplexe Filter & Aggregationen |
| **Performance** | Native Indizes (HNSW, Graph, B-Tree) |
| **Context Enrichment** | Graph Traversal für Related Docs |
| **Type Safety** | Schema-basierte Validierung |

### 1.3 Architektur-Überblick

```
┌─────────────────────────────────────────────────────────┐
│          RAG Pipeline with AQL Prompt Engineering        │
│                                                          │
│  User Query                                             │
│      │                                                   │
│      ▼                                                   │
│  ┌────────────────────────────┐                        │
│  │ Intent Detection           │                        │
│  │ (LLM / Rule-based)         │                        │
│  └────────┬───────────────────┘                        │
│           │                                              │
│           ▼                                              │
│  ┌────────────────────────────┐                        │
│  │ AQL Prompt Engineer        │                        │
│  │ • Template Selection       │                        │
│  │ • Parameter Extraction     │                        │
│  │ • Query Optimization       │                        │
│  └────────┬───────────────────┘                        │
│           │                                              │
│           ▼                                              │
│  ┌────────────────────────────┐                        │
│  │ ThemisDB Execution         │                        │
│  │ • Vector Search            │                        │
│  │ • Graph Traversal          │                        │
│  │ • Document Filter          │                        │
│  └────────┬───────────────────┘                        │
│           │                                              │
│           ▼                                              │
│  ┌────────────────────────────┐                        │
│  │ Result Post-Processing     │                        │
│  │ • Re-ranking               │                        │
│  │ • Context Assembly         │                        │
│  │ • RAG Format Transform     │                        │
│  └────────┬───────────────────┘                        │
│           │                                              │
│           ▼                                              │
│  RAG Context (for LLM)                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. AQL Grundlagen für RAG

### 2.1 Basis-Syntax

```aql
// Einfacher Vector Search
FOR doc IN documents
  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
  FILTER similarity >= 0.7
  SORT similarity DESC
  LIMIT 5
  RETURN doc

// Mit Metadaten-Filter
FOR doc IN documents
  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
  FILTER similarity >= @threshold
  FILTER doc.year >= @min_year
  FILTER doc.domain == @domain
  SORT similarity DESC
  LIMIT @limit
  RETURN {
    doc_id: doc._key,
    content: doc.content,
    score: similarity,
    metadata: doc.metadata
  }
```

### 2.2 Wichtige AQL-Funktionen für RAG

| Funktion | Beschreibung | Use Case |
|----------|--------------|----------|
| `COSINE_SIMILARITY()` | Vektor-Ähnlichkeit (0-1) | Semantische Suche |
| `EUCLIDEAN_DISTANCE()` | Euklidische Distanz | Alternative Metrik |
| `GRAPH_TRAVERSAL()` | Graph-Pfade finden | Context Enrichment |
| `FULLTEXT()` | Volltext-Suche | Keyword Matching |
| `MERGE()` | Objekte zusammenführen | Result Fusion |
| `UNION_DISTINCT()` | Listen kombinieren (unique) | Multi-Source Retrieval |

### 2.3 Query-Variablen & Bind-Parameters

```aql
// Bind Variables (@-Syntax) für Security & Performance
FOR doc IN @@collection
  FILTER doc.category IN @categories
  FILTER doc.created_at >= @start_date
  RETURN doc

// Python Beispiel
bind_vars = {
    "@collection": "legal_documents",
    "categories": ["bgb", "hgb", "zivilrecht"],
    "start_date": "2020-01-01"
}
```

**Vorteile:**
- ✅ SQL-Injection-Prevention
- ✅ Query-Caching (gleicher Query-Plan)
- ✅ Type-Safety

---

## 3. Query Patterns

### 3.1 Pattern 1: Pure Vector Search

**Use Case:** Semantische Ähnlichkeitssuche ohne Filter

```aql
FOR doc IN @@collection
  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
  FILTER similarity >= @threshold
  SORT similarity DESC
  LIMIT @limit
  RETURN {
    doc_id: doc._key,
    content: doc.content,
    score: similarity,
    metadata: doc.metadata,
    source: "vector_search"
  }
```

**Bind Variables:**
```python
{
    "@collection": "documents",
    "query_vector": [0.1, 0.2, ...],  # 768-dim embedding
    "threshold": 0.7,
    "limit": 10
}
```

**Performance:** ~50-100ms für 1M Dokumente (mit HNSW Index)

---

### 3.2 Pattern 2: Vector Search + Metadata Filter

**Use Case:** Semantische Suche mit Facetten-Filter (Jahr, Domain, etc.)

```aql
FOR doc IN @@collection
  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
  FILTER similarity >= @threshold

  // Metadata Filters
  FILTER doc.year >= @min_year AND doc.year <= @max_year
  FILTER doc.domain IN @domains
  FILTER doc.language == @language

  SORT similarity DESC
  LIMIT @limit
  RETURN {
    doc_id: doc._key,
    title: doc.title,
    content: doc.content,
    score: similarity,
    year: doc.year,
    domain: doc.domain,
    metadata: doc.metadata
  }
```

**Python Prompt Engineering:**
```python
def build_filtered_vector_search(user_query, filters):
    bind_vars = {
        "@collection": "documents",
        "query_vector": embed_text(user_query),
        "threshold": 0.65,
        "limit": 20,
        # Extract from user query or UI filters
        "min_year": filters.get("year_from", 2000),
        "max_year": filters.get("year_to", 2025),
        "domains": filters.get("domains", ["verwaltungsrecht"]),
        "language": filters.get("language", "de")
    }
    return bind_vars
```

---

### 3.3 Pattern 3: Graph-Enhanced Vector Search (Hybrid)

**Use Case:** Semantische Suche + verwandte Dokumente via Graph

```aql
// Step 1: Vector Search für Basis-Dokumente
LET base_docs = (
  FOR doc IN @@collection
    LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
    FILTER similarity >= @vector_threshold
    SORT similarity DESC
    LIMIT @vector_limit
    RETURN {doc: doc, score: similarity}
)

// Step 2: Graph Traversal für Related Docs
LET related_docs = (
  FOR base IN base_docs
    FOR v, e, p IN 1..@graph_depth ANY base.doc._id
      @edge_collection
      OPTIONS {uniqueVertices: "path", bfs: true}
      RETURN {
        doc: v,
        relation: e._from + " -> " + e._to,
        edge_type: e.type,
        path_length: LENGTH(p.edges),
        source_score: base.score
      }
)

// Step 3: Merge & Re-rank
LET all_results = UNION_DISTINCT(base_docs, related_docs)

FOR result IN all_results
  // Re-ranking: Base Score + Graph Boost
  LET final_score = (
    result.score ? result.score :
    (result.source_score * 0.7 / (result.path_length + 1))
  )

  SORT final_score DESC
  LIMIT @final_limit
  RETURN {
    doc_id: result.doc._key,
    content: result.doc.content,
    score: final_score,
    source: result.score ? "vector" : "graph",
    metadata: result.doc.metadata,
    relation: result.relation
  }
```

**Bind Variables:**
```python
{
    "@collection": "documents",
    "@edge_collection": "citations",
    "query_vector": [0.1, ...],
    "vector_threshold": 0.7,
    "vector_limit": 10,
    "graph_depth": 2,
    "final_limit": 20
}
```

**Performance:** ~200-300ms (Vector Search: 50ms + Graph: 150ms)

---

### 3.4 Pattern 4: Context-Enriched RAG Query

**Use Case:** Retrieval mit automatischem Context-Building für LLM

```aql
// Main Query: Vector Search
FOR doc IN @@collection
  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
  FILTER similarity >= @threshold
  SORT similarity DESC
  LIMIT @limit

  // Context Enrichment: Related Documents
  LET related = (
    FOR v IN 1..2 OUTBOUND doc._id
      citations
      RETURN {
        title: v.title,
        summary: v.summary,
        type: v.type
      }
  )

  // Context Enrichment: Parent Documents (Hierarchie)
  LET parent = (
    FOR v IN 1..1 INBOUND doc._id
      hierarchy
      RETURN {
        title: v.title,
        category: v.category
      }
  )

  RETURN {
    // Main Document
    doc_id: doc._key,
    title: doc.title,
    content: doc.content,
    score: similarity,

    // RAG Context
    rag_context: {
      related_documents: related,
      parent_category: parent[0],
      metadata: doc.metadata
    },

    // LLM-ready Format
    llm_input: CONCAT(
      "# ", doc.title, "\n\n",
      doc.content, "\n\n",
      "## Related: ", LENGTH(related), " documents\n",
      "## Category: ", parent[0].category
    )
  }
```

---

## 4. Performance Optimization

### 4.1 Index-Strategien

```aql
// ❌ SLOW: Full Collection Scan
FOR doc IN documents
  FILTER doc.year == 2023
  RETURN doc

// ✅ FAST: Index Usage
FOR doc IN documents
  FILTER doc.year == 2023  // Uses B-Tree index on 'year'
  RETURN doc
```

### 4.2 Query Caching

```aql
// Enable Query Caching with Hint
/* +cache */
FOR doc IN documents
  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
  FILTER similarity >= 0.7
  LIMIT 10
  RETURN doc
```

---

## 5. Domain-spezifische Templates

### 5.1 Verwaltungsrecht

```python
VERWALTUNGSRECHT_TEMPLATE = """
LET gesetze = (
  FOR doc IN verwaltungsgesetze
    LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
    FILTER similarity >= @threshold
    FILTER doc.rechtsgebiet == "verwaltungsrecht"
    FILTER doc.aktiv == true
    LIMIT 5
    RETURN {doc: doc, score: similarity, type: "gesetz"}
)

FOR result IN gesetze
  SORT result.score DESC
  LIMIT @final_limit
  RETURN result
"""
```

---

## 6. Error Handling & Fallbacks

### 6.1 Query Validation

```python
def validate_aql_query(aql_query: str, bind_vars: dict) -> bool:
    """Validiert AQL Query vor Ausführung"""

    # Check for dangerous operations
    forbidden_keywords = ["DROP", "DELETE", "CREATE", "UPDATE", "INSERT"]
    if any(keyword in aql_query.upper() for keyword in forbidden_keywords):
        raise ValueError("Write operations not allowed in RAG queries")

    return True
```

---

## 7. Monitoring & Debugging

### 7.1 Query Profiling

```aql
// Enable Query Profiling
/* +profile */
FOR doc IN documents
  LET similarity = COSINE_SIMILARITY(doc.embedding, @query_vector)
  FILTER similarity >= 0.7
  LIMIT 10
  RETURN doc
```

---

## 8. Zusammenfassung & Best Practices

### 8.1 Checkliste für optimale AQL RAG Queries

- [ ] **Vector Search** mit HNSW Index nutzen
- [ ] **Bind Variables** für alle Parameter
- [ ] **Metadaten-Filter** früh im Query (vor Sort)
- [ ] **LIMIT** immer setzen (verhindert Memory Issues)
- [ ] **Caching** aktivieren für häufige Queries
- [ ] **Timeouts** setzen (default: 30s)
- [ ] **Error Handling** mit Fallbacks
- [ ] **Monitoring** & Logging aktivieren

---

**Letzte Aktualisierung:** 3. Dezember 2025
**Version:** 1.0
**Maintainer:** VERITAS Backend Team
