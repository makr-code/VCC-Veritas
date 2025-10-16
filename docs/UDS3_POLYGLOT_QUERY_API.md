# UDS3 PolyglotQuery API Reference

## Quick Start

```python
from uds3.uds3_core import get_optimized_unified_strategy
from uds3.uds3_polyglot_query import create_polyglot_query, JoinStrategy, ExecutionMode

# Get UDS3 strategy (singleton)
strategy = get_optimized_unified_strategy()

# Create polyglot query
query = create_polyglot_query(strategy, ExecutionMode.PARALLEL)

# Build multi-database query (fluent API)
query.graph().by_relationship("CITES", direction="OUTGOING").with_depth(2)
query.relational().from_table("documents_metadata").where("status", "=", "active").limit(100)

# Execute with UNION join (combine all results)
result = query.join_strategy(JoinStrategy.UNION).execute()

# Access results
print(f"Found {result.joined_count} documents")
print(f"Databases queried: {result.databases_queried}")
print(f"Success: {result.success}")
```

---

## API Structure

### 1. Factory Function

```python
from uds3.uds3_polyglot_query import create_polyglot_query, ExecutionMode

query = create_polyglot_query(
    unified_strategy,                    # UnifiedDatabaseStrategy instance
    execution_mode=ExecutionMode.SMART   # PARALLEL, SEQUENTIAL, or SMART
)
```

**ExecutionMode:**
- `PARALLEL` - Execute all database queries in parallel (fastest, higher resource usage)
- `SEQUENTIAL` - Execute database queries one by one (slower, lower resource usage)
- `SMART` - Auto-determine based on query complexity (recommended)

---

### 2. Graph Query Builder

**Purpose:** Query Neo4j graph database for relationships

```python
query.graph()
    .by_relationship(
        relationship_type="CITES",     # e.g., "CITES", "RELATED_TO", "SUPERSEDES"
        direction="OUTGOING"            # "OUTGOING", "INCOMING", or "BOTH"
    )
    .with_depth(2)                     # Maximum traversal depth (optional)
```

**Returns:** `PolyglotQuery` for chaining

**Example:**
```python
# Find documents that cite § 58 LBO BW (outgoing CITES)
query.graph().by_relationship("CITES", direction="OUTGOING").with_depth(1)

# Find documents cited by § 58 LBO BW (incoming CITES)
query.graph().by_relationship("CITES", direction="INCOMING").with_depth(1)

# Find all related documents (both directions, up to 2 hops)
query.graph().by_relationship("RELATED_TO", direction="BOTH").with_depth(2)
```

---

### 3. Relational Query Builder

**Purpose:** Query PostgreSQL for metadata and keyword searches

```python
query.relational()
    .from_table("documents_metadata")      # Table name (optional, defaults to "documents_metadata")
    .where("status", "=", "active")        # WHERE condition
    .where("document_type", "=", "regulation")  # Multiple WHERE conditions (AND logic)
    .limit(100)                            # Result limit (finalizes query)
```

**Returns:** `PolyglotQuery` for chaining

**Operators:**
- `"="` - Equals
- `"!="` - Not equals
- `">"`, `">="` - Greater than (or equal)
- `"<"`, `"<="` - Less than (or equal)
- `"LIKE"` - Pattern matching (use `%` wildcard)
- `"IN"` - Value in list

**Example:**
```python
# Find active building regulations
query.relational()
    .from_table("documents_metadata")
    .where("status", "=", "active")
    .where("document_type", "=", "regulation")
    .where("category", "LIKE", "%Baurecht%")
    .limit(50)

# Find documents by ID list
query.relational()
    .where("document_id", "IN", ["doc1", "doc2", "doc3"])
    .limit(10)
```

**Note:** Vector search (by_similarity) requires embedding generation - not yet implemented.

---

### 4. Join Strategies

**Purpose:** Define how to combine results from multiple databases

```python
query.join_strategy(JoinStrategy.INTERSECTION)  # AND logic
query.join_strategy(JoinStrategy.UNION)         # OR logic
query.join_strategy(JoinStrategy.SEQUENTIAL)    # First non-empty result
```

**JoinStrategy.INTERSECTION (AND logic):**
- Returns documents present in **ALL** queried databases
- Example: Vector AND Graph AND Relational
- Use case: High-precision queries (only return documents matching all criteria)

**JoinStrategy.UNION (OR logic):**
- Returns documents present in **ANY** queried database
- Example: Vector OR Graph OR Relational
- Use case: Broad searches (return all potentially relevant documents)

**JoinStrategy.SEQUENTIAL:**
- Returns first non-empty result set
- Query order: Vector → Graph → Relational → FileStorage
- Use case: Fallback strategy (try Vector first, then Graph if empty, etc.)

**Example:**
```python
# High-precision search (must match ALL criteria)
query.graph().by_relationship("CITES", "OUTGOING")
query.relational().where("status", "=", "active")
result = query.join_strategy(JoinStrategy.INTERSECTION).execute()
# Returns: Documents that (cite others) AND (are active)

# Broad search (match ANY criteria)
query.graph().by_relationship("CITES", "OUTGOING")
query.relational().where("status", "=", "active")
result = query.join_strategy(JoinStrategy.UNION).execute()
# Returns: Documents that (cite others) OR (are active)
```

---

### 5. Query Execution

```python
result = query.execute()  # Execute all configured queries and join results
```

**Returns:** `PolyglotQueryResult` object

---

### 6. Result Object

```python
class PolyglotQueryResult:
    success: bool                                    # Overall success status
    join_strategy: JoinStrategy                      # Join strategy used
    execution_mode: ExecutionMode                    # Execution mode used
    database_results: Dict[DatabaseType, QueryResult]  # Individual database results
    joined_document_ids: Set[str]                    # Final joined document IDs
    joined_results: List[Dict[str, Any]]             # Full result objects
    joined_count: int                                # Number of joined results
    total_execution_time_ms: float                   # Total query time
    database_execution_times: Dict[DatabaseType, float]  # Per-database execution times
    databases_queried: List[DatabaseType]            # Which databases were queried
    databases_succeeded: List[DatabaseType]          # Which databases succeeded
    databases_failed: List[DatabaseType]             # Which databases failed
    error: Optional[str]                             # Error message if failed
```

**Example:**
```python
result = query.execute()

if result.success:
    print(f"✅ Found {result.joined_count} documents")
    print(f"Databases queried: {result.databases_queried}")
    print(f"Total time: {result.total_execution_time_ms:.2f}ms")
    
    for db, time_ms in result.database_execution_times.items():
        print(f"  {db.value}: {time_ms:.2f}ms")
    
    # Access individual documents
    for doc in result.joined_results[:10]:  # Top 10
        doc_id = doc.get("document_id")
        print(f"Document: {doc_id}")
else:
    print(f"❌ Query failed: {result.error}")
```

---

## Complete Example: Hybrid Search

```python
from uds3.uds3_core import get_optimized_unified_strategy
from uds3.uds3_polyglot_query import create_polyglot_query, JoinStrategy, ExecutionMode

# Initialize UDS3
strategy = get_optimized_unified_strategy()

# Create query
query = create_polyglot_query(strategy, ExecutionMode.PARALLEL)

# Add graph query (find documents citing § 58 LBO BW)
query.graph().by_relationship(
    relationship_type="CITES",
    direction="OUTGOING"
).with_depth(2)

# Add relational query (find active building regulations)
query.relational().from_table("documents_metadata").where(
    "document_type", "=", "regulation"
).where(
    "status", "=", "active"
).where(
    "category", "LIKE", "%Baurecht%"
).limit(100)

# Execute with UNION join (combine all results)
result = query.join_strategy(JoinStrategy.UNION).execute()

# Process results
if result.success:
    print(f"✅ Found {result.joined_count} documents")
    print(f"Query time: {result.total_execution_time_ms:.2f}ms")
    
    # Sort by relevance (if scores available)
    sorted_docs = sorted(
        result.joined_results,
        key=lambda d: d.get("score", 0.0),
        reverse=True
    )
    
    # Display top 10
    for i, doc in enumerate(sorted_docs[:10], 1):
        doc_id = doc.get("document_id", "unknown")
        title = doc.get("title", "Untitled")
        score = doc.get("score", 0.0)
        print(f"{i}. [{doc_id}] {title} (Score: {score:.3f})")
else:
    print(f"❌ Query failed: {result.error}")
```

---

## Common Patterns

### Pattern 1: Find Related Documents (Graph)

```python
query = create_polyglot_query(strategy)
query.graph().by_relationship("RELATED_TO", direction="BOTH").with_depth(1)
result = query.execute()
```

### Pattern 2: Filter by Metadata (Relational)

```python
query = create_polyglot_query(strategy)
query.relational()
    .where("status", "=", "active")
    .where("document_type", "IN", ["regulation", "guideline"])
    .where("created_date", ">", "2020-01-01")
    .limit(50)
result = query.execute()
```

### Pattern 3: Hybrid Search (Graph + Relational with UNION)

```python
query = create_polyglot_query(strategy)

# Graph: Find citations
query.graph().by_relationship("CITES", "OUTGOING")

# Relational: Find by keyword
query.relational().where("title", "LIKE", "%Photovoltaik%").limit(50)

# Combine with OR logic
result = query.join_strategy(JoinStrategy.UNION).execute()
```

### Pattern 4: High-Precision Search (Graph + Relational with INTERSECTION)

```python
query = create_polyglot_query(strategy)

# Graph: Must cite § 58 LBO BW
query.graph().by_relationship("CITES", "OUTGOING")

# Relational: Must be active regulation
query.relational()
    .where("status", "=", "active")
    .where("document_type", "=", "regulation")
    .limit(100)

# Combine with AND logic (must match both)
result = query.join_strategy(JoinStrategy.INTERSECTION).execute()
```

---

## Error Handling

```python
try:
    query = create_polyglot_query(strategy)
    query.graph().by_relationship("CITES", "OUTGOING")
    result = query.execute()
    
    if not result.success:
        print(f"Query failed: {result.error}")
        print(f"Failed databases: {result.databases_failed}")
    elif result.joined_count == 0:
        print("No results found (try different query or join strategy)")
    else:
        print(f"Success! Found {result.joined_count} documents")
        
except Exception as e:
    print(f"Error executing query: {e}")
    import traceback
    traceback.print_exc()
```

---

## Performance Tips

1. **Use PARALLEL execution for independent queries** (faster)
2. **Use UNION for broad searches** (more results)
3. **Use INTERSECTION for high-precision** (fewer, more relevant results)
4. **Add LIMIT to relational queries** (prevent large result sets)
5. **Use specific relationship types** (faster graph traversal)
6. **Limit graph depth** (avoid deep traversals)

---

## Limitations (Current)

- **Vector Search:** `vector().by_similarity()` requires embedding generation (not yet implemented)
- **File Storage:** `file_storage()` query builder exists but not commonly used
- **Scoring:** Individual database scores may not be preserved in joined results
- **Ordering:** Result ordering depends on join strategy and database order

---

## Next Steps for Implementation

1. **Implement Embedding Generation:**
   ```python
   from sentence_transformers import SentenceTransformer
   model = SentenceTransformer('all-MiniLM-L6-v2')
   embedding = model.encode(query_text)
   ```

2. **Add Vector Query:**
   ```python
   query.vector().by_similarity(
       embedding=embedding,
       threshold=0.8,
       top_k=100
   )
   ```

3. **Implement Result Re-Ranking:**
   - Extract scores from individual database results
   - Apply weighted scoring (vector=0.5, graph=0.2, relational=0.3)
   - Sort by final_score

4. **Add Caching:**
   - Cache PolyglotQueryResult for repeated queries
   - Cache embeddings for frequently used queries
   - Use TTL (e.g., 5 minutes)

---

**Last Updated:** 2025-01-11  
**UDS3 Version:** 3.18.4  
**Status:** ✅ Production Ready (Vector search pending)
