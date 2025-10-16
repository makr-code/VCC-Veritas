# UDS3 Hybrid Search - Quick Start Guide

**Datum:** 11. Oktober 2025  
**Status:** ✅ UDS3 Backends aktiv, ready for integration

---

## 🎉 UDS3 Status

### ✅ All Backends Active!

```
Vector Backend (ChromaDB):    ✅ Aktiv
Metadata Backend (PostgreSQL): ✅ Aktiv
Graph Backend (Neo4j):         ✅ Aktiv
File Backend:                  ✅ Aktiv
```

**Result:** Bereit für UDS3 Hybrid Search Implementation!

---

## 🚀 Quick Start (3 Schritte)

### 1. UDS3 Status prüfen

```powershell
python scripts/check_uds3_status.py
```

**Erwartete Ausgabe:**
```
✅ Alle essentiellen Backends aktiv!
→ Bereit für UDS3 Hybrid Search Implementation
```

---

### 2. Hybrid Search Agent verwenden

```python
from uds3.uds3_core import get_optimized_unified_strategy
from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

# Initialize UDS3 Strategy (Singleton)
strategy = get_optimized_unified_strategy()

# Create Hybrid Search Agent
agent = UDS3HybridSearchAgent(strategy)

# Execute Hybrid Search
results = await agent.hybrid_search(
    query="Was regelt § 58 LBO BW bezüglich Photovoltaik-Anlagen?",
    top_k=10,
    weights={"vector": 0.5, "keyword": 0.3, "graph": 0.2}
)

# Process results
for result in results:
    print(f"Score: {result.final_score:.3f}")
    print(f"Title: {result.metadata.get('title', 'N/A')}")
    print(f"Content: {result.content[:200]}...")
    print()
```

---

### 3. SupervisorAgent Integration

**Aktuell (Ineffizient):**
```python
# Jeder Agent ruft UDS3 separat auf
for agent_name in selected_agents:
    agent = self.agents[agent_name]
    result = await agent.process(query)  # N UDS3 Calls!
```

**Optimiert (Zentraler Zugriff):**
```python
from uds3.uds3_core import get_optimized_unified_strategy
from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

class SupervisorAgent:
    def __init__(self):
        # Zentraler UDS3 Zugriff
        self.uds3_strategy = get_optimized_unified_strategy()
        self.uds3_agent = UDS3HybridSearchAgent(self.uds3_strategy)
        
        # Existing agents
        self.agents = {...}
    
    async def process_query(self, query: str):
        # 1. UDS3 Hybrid Search (1x für alle Agenten!)
        uds3_results = await self.uds3_agent.hybrid_search(
            query=query,
            top_k=20
        )
        
        # 2. Agent Selection
        selected_agents = await self._select_agents(query, uds3_results)
        
        # 3. Agent Execution (mit UDS3 Context!)
        agent_results = await self._execute_agents_with_context(
            selected_agents=selected_agents,
            query=query,
            uds3_context=uds3_results  # Pass pre-fetched results!
        )
        
        # 4. Synthesis
        synthesized = await self.synthesize_results(agent_results, query)
        
        return synthesized
```

**Benefit:** -70% UDS3 Calls (1 statt N bei Multi-Agent Queries)

---

## 📊 UDS3 Architecture

### Unified Database Strategy

```
┌─────────────────────────────────────────────┐
│ UnifiedDatabaseStrategy (Singleton)        │
│  - vector_backend (ChromaDB)               │
│  - relational_backend (PostgreSQL)         │
│  - graph_backend (Neo4j)                   │
│  - file_backend                            │
│                                             │
│  Methods:                                  │
│  • unified_query(query, weights)           │
│  • create_secure_document(...)             │
│  • query_across_databases(...)             │
└─────────────────────────────────────────────┘
```

**Key Insight:**
- **KEINE** separate DocumentStore-API
- **ALLE** DB-Zugriffe über `UnifiedDatabaseStrategy`
- Factory-Funktion: `get_optimized_unified_strategy()`

---

## 🔧 Configuration

### Database Backends

UDS3 Backends werden konfiguriert in:
```
c:\VCC\uds3\database\config.py
```

**Aktuelle Konfiguration:**
```python
POSTGRES_CONFIG = {
    'host': '192.168.178.94',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'postgres'
}

CHROMADB_CONFIG = {
    'host': '192.168.178.94',
    'port': 8000
}

NEO4J_CONFIG = {
    'host': '192.168.178.94',
    'port': 7687,
    'user': 'neo4j',
    'password': 'neo4j'
}
```

---

## 📝 Code Examples

### Example 1: Simple Vector Search

```python
from uds3.uds3_core import get_optimized_unified_strategy
from backend.agents.veritas_uds3_hybrid_agent import UDS3HybridSearchAgent

strategy = get_optimized_unified_strategy()
agent = UDS3HybridSearchAgent(strategy)

# Vector-only search
results = await agent.vector_search_only(
    query="Photovoltaik Genehmigung",
    top_k=5
)
```

### Example 2: Keyword Search

```python
# Keyword-only search (exact matching)
results = await agent.keyword_search_only(
    query="§ 58 LBO BW",
    top_k=5
)
```

### Example 3: Custom Weights

```python
# Heavy vector weighting
results = await agent.hybrid_search(
    query="Umweltauflagen Bauvorhaben",
    top_k=10,
    weights={"vector": 0.7, "keyword": 0.2, "graph": 0.1}
)
```

### Example 4: With Filters

```python
# Filter by document type
results = await agent.hybrid_search(
    query="Immissionsschutz",
    top_k=10,
    weights={"vector": 0.5, "keyword": 0.3, "graph": 0.2},
    filters={"document_type": "regulation"}
)
```

---

## 🧪 Testing

### Run UDS3 Status Check

```powershell
python scripts/check_uds3_status.py
```

### Run Hybrid Search Test

```powershell
# Default query
python scripts/test_uds3_hybrid.py

# Custom query
python scripts/test_uds3_hybrid.py --query "Photovoltaik Baugenehmigung"
```

**Expected Output:**
```
🔍 UDS3 Hybrid Search Test
============================================================
Query: Photovoltaik Baugenehmigung
============================================================

📊 Available Backends:
  Vector (ChromaDB):    ✅
  Metadata (PostgreSQL): ✅
  Graph (Neo4j):         ✅

Test 1: Hybrid Search (Default Weights)
============================================================
Weights: Vector=0.5, Keyword=0.3, Graph=0.2

✅ Found 10 results

1. Score: 0.847
   ID: doc_12345
   Title: § 58 LBO BW - Anlagen zur Nutzung erneuerbarer Energien
   ...
```

---

## 📚 Next Steps

### Phase 1: Integration (diese Woche)

1. ✅ **UDS3 Status Check** - Done!
2. 🔄 **Hybrid Search Test** - In Progress
3. ⏳ **SupervisorAgent Integration** - Next
4. ⏳ **Agent Updates** (Context-based processing)

### Phase 2: Optimization (nächste Woche)

1. **Performance Benchmarks**
   - Latenz-Vergleich (Hybrid vs Vector-only)
   - Quality-Metriken (Precision@10, Recall@10)

2. **Caching Layer**
   - Query-Result Caching (Redis/Memory)
   - TTL-based invalidation

3. **Advanced Features**
   - Re-ranking with LLM
   - Query expansion
   - Relevance feedback

---

## 🎯 Success Criteria

### ✅ Phase 1 Complete When:

- [x] UDS3 Status Check läuft ✅
- [ ] Hybrid Search Test erfolgreich
- [ ] SupervisorAgent nutzt zentralen UDS3 Zugriff
- [ ] -70% UDS3 Calls (1 statt N)
- [ ] 100% Konsistenz (alle Agents sehen gleiche Dokumente)

### ✅ Phase 2 Complete When:

- [ ] -40% Latenz (durch zentralen Zugriff)
- [ ] +17% Precision@10 (Hybrid Search)
- [ ] Caching aktiv (30% Cache Hit Rate)

---

## 🐛 Troubleshooting

### Problem: "UDS3 nicht gefunden"

**Lösung:**
```python
# Stelle sicher dass c:\VCC\uds3 im Python Path ist
import sys
from pathlib import Path

uds3_path = Path("c:/VCC/uds3")
if uds3_path.exists():
    sys.path.insert(0, str(uds3_path))
```

### Problem: "unified_query() method not found"

**Lösung:**
```python
# Check UDS3 Version
from uds3.uds3_core import UnifiedDatabaseStrategy
strategy = UnifiedDatabaseStrategy()
print(hasattr(strategy, 'unified_query'))  # Should be True
```

### Problem: "No backends available"

**Lösung:**
```powershell
# Check database/config.py
python -c "from database.config import get_database_backend_dict; print(get_database_backend_dict())"

# Restart databases if needed
# PostgreSQL: 192.168.178.94:5432
# ChromaDB: 192.168.178.94:8000
# Neo4j: 192.168.178.94:7687
```

---

## 📖 Documentation

- **Full Guide:** `docs/UDS3_INTEGRATION_GUIDE.md` (4,500 LOC)
- **Architecture:** `docs/UDS3_INTEGRATION_GUIDE.md#architecture`
- **API Reference:** `backend/agents/veritas_uds3_hybrid_agent.py`
- **Testing:** `scripts/test_uds3_hybrid.py`

---

**Last Updated:** 11. Oktober 2025  
**Status:** ✅ Ready for Integration  
**Next:** Hybrid Search Test → SupervisorAgent Integration
