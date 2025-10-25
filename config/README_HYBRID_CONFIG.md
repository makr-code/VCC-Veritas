# Hybrid Search Configuration Guide

Umfassende Dokumentation für das Hybrid Search Configuration System von VERITAS.

## 📋 Inhaltsverzeichnis

- [Überblick](#überblick)
- [Schnellstart](#schnellstart)
- [Konfigurationsoptionen](#konfigurationsoptionen)
- [Preset-Konfigurationen](#preset-konfigurationen)
- [Environment Variables](#environment-variables)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Überblick

Das Hybrid Search Configuration System bietet eine zentrale, typsichere Konfiguration für:

- **Search Weights**: Gewichtung von Vector, Graph und Relational Search
- **Ranking Strategies**: RRF, Weighted, Borda Count
- **Re-Ranking**: LLM-basierte semantische Neubewertung
- **Performance Tuning**: Batch-Größen, Timeouts, Thresholds
- **Environment Support**: Flexible Konfiguration via Umgebungsvariablen

### Architektur

```
config/hybrid_search_config.py
├── SearchWeights (Vector/Graph/Relational Ratios)
├── SearchFilters (max_results, min_relevance)
├── RRFConfig (k-Parameter für Reciprocal Rank Fusion)
├── ReRankingConfig (LLM Model, Scoring Mode, Batch Size)
└── HybridSearchConfig (Master Configuration)
```

---

## 🚀 Schnellstart

### 1. Installation

```bash
# Keine zusätzlichen Dependencies erforderlich
# Alles in Python Standard Library + existing VERITAS dependencies
```

### 2. Basic Usage

```python
from config.hybrid_search_config import HybridSearchConfig, load_config_from_env

# Option A: Load from environment variables
config = load_config_from_env()

# Option B: Use preset configuration
from config.hybrid_search_config import get_preset_config
config = get_preset_config("production")

# Option C: Custom configuration
from config.hybrid_search_config import SearchWeights
config = HybridSearchConfig(
    weights=SearchWeights(vector=0.7, graph=0.2, relational=0.1),
    reranking_config=ReRankingConfig(batch_size=10)
)
```

### 3. Integration in QueryService

```python
from config.hybrid_search_config import DEFAULT_CONFIG

class QueryService:
    def __init__(self):
        self.config = DEFAULT_CONFIG
        
    async def _process_hybrid(self, query: str):
        # Use config for hybrid search
        hybrid_result = self.rag_service.hybrid_search(
            query=query,
            weights=self.config.weights,
            filters=self.config.filters,
            ranking_strategy=self.config.ranking_strategy
        )
        
        # Apply re-ranking if enabled
        if self.config.reranking_config.enabled:
            hybrid_result = await self._apply_reranking(
                hybrid_result, 
                query,
                batch_size=self.config.reranking_config.batch_size
            )
```

---

## ⚙️ Konfigurationsoptionen

### SearchWeights

Gewichtung der drei Retrieval-Komponenten (müssen zu 1.0 summieren):

```python
SearchWeights(
    vector=0.6,        # Dense retrieval (ChromaDB embeddings)
    graph=0.2,         # Knowledge graph (Neo4j relationships)
    relational=0.2     # Structured DB (PostgreSQL metadata)
)
```

**Use Cases:**
- **Balanced (0.6/0.2/0.2)**: Standard für gemischte Queries
- **Vector-Heavy (0.8/0.1/0.1)**: Semantic Search dominant
- **Graph-Heavy (0.4/0.4/0.2)**: Entity-Relationships wichtig

### SearchFilters

```python
SearchFilters(
    max_results=20,           # Max results per retriever
    min_relevance=0.5,        # Minimum score threshold (0.0-1.0)
    date_from="2024-01-01",   # Optional: ISO date filter
    document_types=["pdf"]    # Optional: Document type filter
)
```

### RRFConfig

Reciprocal Rank Fusion Parameter:

```python
RRFConfig(k=60)  # Higher k → flatter distribution
```

**Formula:** `score(doc) = Σ[1 / (k + rank_i)]`

**Empfehlungen:**
- `k=10-30`: Sharp distribution (top ranks matter most)
- `k=60`: Balanced (default)
- `k=100+`: Flat distribution (all ranks weighted similarly)

### ReRankingConfig

LLM-based semantic re-ranking:

```python
ReRankingConfig(
    enabled=True,
    model_name="llama3.1:8b",
    scoring_mode=ScoringMode.COMBINED,  # RELEVANCE_ONLY | INFORMATIVENESS_ONLY | COMBINED
    temperature=0.1,                     # Low = consistent scores
    batch_size=5,                        # Documents per LLM call
    timeout_seconds=30,
    max_retries=2
)
```

**Scoring Modes:**
- `RELEVANCE_ONLY`: Focus on query-document relevance
- `INFORMATIVENESS_ONLY`: Focus on information quality
- `COMBINED`: Balanced (recommended)

---

## 🎨 Preset-Konfigurationen

### Balanced (Default)
```python
config = get_preset_config("balanced")
# Vector: 60%, Graph: 20%, Relational: 20%
# RRF with k=60
# Re-ranking enabled
# Target: ~5-8s latency
```

### Vector Heavy
```python
config = get_preset_config("vector_heavy")
# Vector: 80%, Graph: 10%, Relational: 10%
# Weighted combination (fast)
# Best for semantic search queries
```

### Graph Heavy
```python
config = get_preset_config("graph_heavy")
# Vector: 40%, Graph: 40%, Relational: 20%
# Best for entity-relationship queries
# Example: "Zeige alle Referenzen zu § 35 BauGB"
```

### Fast (Low Latency)
```python
config = get_preset_config("fast")
# Vector: 70%, Graph: 20%, Relational: 10%
# Re-ranking DISABLED
# max_results=10 (fewer candidates)
# Target: ~2s latency
```

### Accurate (Best Quality)
```python
config = get_preset_config("accurate")
# Vector: 60%, Graph: 20%, Relational: 20%
# Re-ranking enabled with batch_size=10
# max_results=30, min_relevance=0.3 (more candidates)
# Target: ~10s latency
```

### Production
```python
config = get_preset_config("production")
# Balanced weights
# Robust timeouts and retries
# Optimized for reliability
```

---

## 🌍 Environment Variables

Alle Einstellungen können über Environment Variables überschrieben werden:

```bash
# General settings
export HYBRID_SEARCH_ENABLED=true
export HYBRID_RANKING_STRATEGY=reciprocal_rank_fusion

# Search weights (must sum to 1.0)
export HYBRID_WEIGHT_VECTOR=0.6
export HYBRID_WEIGHT_GRAPH=0.2
export HYBRID_WEIGHT_RELATIONAL=0.2

# Search filters
export HYBRID_MAX_RESULTS=20
export HYBRID_MIN_RELEVANCE=0.5

# RRF configuration
export HYBRID_RRF_K=60

# Re-ranking configuration
export RERANKING_ENABLED=true
export RERANKING_MODEL=llama3.1:8b
export RERANKING_SCORING_MODE=combined
export RERANKING_TEMPERATURE=0.1
export RERANKING_BATCH_SIZE=5
export RERANKING_TIMEOUT=30
export RERANKING_MAX_RETRIES=2
```

### .env File

Kopiere `.env.example` zu `.env` und passe die Werte an:

```bash
cp .env.example .env
nano .env  # Edit configuration
```

---

## ✅ Best Practices

### 1. Development Environment

```bash
# Fast iteration, no re-ranking
export HYBRID_SEARCH_ENABLED=true
export RERANKING_ENABLED=false
export HYBRID_MAX_RESULTS=10
```

### 2. Production Environment

```python
# Use production preset + environment overrides
config = get_preset_config("production")

# Or load from .env
config = load_config_from_env()
```

### 3. Performance Optimization

**For Low Latency (<2s):**
- Use `fast` preset
- Disable re-ranking (`RERANKING_ENABLED=false`)
- Reduce max_results to 10
- Use `weighted_combination` strategy

**For Best Quality (<10s):**
- Use `accurate` preset
- Enable re-ranking with larger batch_size
- Increase max_results to 30-50
- Lower min_relevance to 0.3

### 4. Weight Tuning

Start with defaults and iterate based on use case:

```python
# Legal document search (entity relationships important)
weights = SearchWeights(vector=0.4, graph=0.4, relational=0.2)

# General knowledge search (semantic similarity primary)
weights = SearchWeights(vector=0.7, graph=0.2, relational=0.1)

# Structured data search (metadata filters important)
weights = SearchWeights(vector=0.5, graph=0.2, relational=0.3)
```

### 5. Validation

Always validate configuration on startup:

```python
from config.hybrid_search_config import load_config_from_env

try:
    config = load_config_from_env()
    logger.info(f"Hybrid search config loaded: {config.to_dict()}")
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
    raise
```

---

## 🔧 Troubleshooting

### Issue: "SearchWeights must sum to 1.0"

**Ursache:** Die drei Gewichte ergeben nicht 1.0

**Lösung:**
```python
# ✗ Falsch (sum = 1.1)
HYBRID_WEIGHT_VECTOR=0.5
HYBRID_WEIGHT_GRAPH=0.3
HYBRID_WEIGHT_RELATIONAL=0.3

# ✓ Korrekt (sum = 1.0)
HYBRID_WEIGHT_VECTOR=0.6
HYBRID_WEIGHT_GRAPH=0.2
HYBRID_WEIGHT_RELATIONAL=0.2
```

### Issue: "RerankerService timeout"

**Ursache:** LLM braucht zu lange für Re-Ranking

**Lösungen:**
1. Erhöhe Timeout: `RERANKING_TIMEOUT=60`
2. Reduziere Batch-Size: `RERANKING_BATCH_SIZE=3`
3. Nutze kleineres Model: `RERANKING_MODEL=llama3.2:3b`
4. Deaktiviere Re-Ranking: `RERANKING_ENABLED=false`

### Issue: "RRF k must be in [1, 1000]"

**Ursache:** Ungültiger RRF k-Parameter

**Lösung:**
```bash
# ✗ Falsch
HYBRID_RRF_K=0

# ✓ Korrekt (1-1000)
HYBRID_RRF_K=60
```

### Issue: Langsame Performance

**Diagnose:**
1. Check Re-Ranking Status: `RERANKING_ENABLED=true` (deaktivieren für Test)
2. Check max_results: `HYBRID_MAX_RESULTS=20` (reduzieren auf 10)
3. Check Ranking Strategy: `weighted_combination` ist schneller als RRF

**Lösung:**
```python
# Use fast preset
config = get_preset_config("fast")
```

### Issue: Schlechte Ergebnis-Qualität

**Diagnose:**
1. Check Weights: Passen sie zum Use Case?
2. Check min_relevance: Zu hoch → zu wenige Results
3. Check Re-Ranking: Aktiviert?

**Lösung:**
```python
# Use accurate preset
config = get_preset_config("accurate")

# Or manually tune:
config = HybridSearchConfig(
    weights=SearchWeights(vector=0.6, graph=0.2, relational=0.2),
    filters=SearchFilters(max_results=30, min_relevance=0.3),
    reranking_config=ReRankingConfig(enabled=True, batch_size=10)
)
```

---

## 📊 Performance Benchmarks

### Hardware: i7/Ryzen 7, 16GB RAM, No GPU

| Preset | Hybrid Search | Re-Ranking | Total Latency |
|--------|--------------|------------|---------------|
| Fast   | ~500ms       | Disabled   | **~2s**       |
| Balanced | ~1s        | ~4s (5 docs) | **~5-8s**   |
| Accurate | ~1.5s      | ~8s (30 docs) | **~10-12s** |

### Mit GPU-Beschleunigung:
- Re-Ranking Latenz: **~50% schneller**
- Empfohlen für Production

---

## 🧪 Testing

Run tests:

```bash
# All config tests
pytest tests/backend/test_hybrid_search_config.py -v

# Specific test class
pytest tests/backend/test_hybrid_search_config.py::TestSearchWeights -v

# With coverage
pytest tests/backend/test_hybrid_search_config.py --cov=config.hybrid_search_config
```

Expected: **48 tests passed, >95% coverage**

---

## 📚 Weitere Ressourcen

- **API Documentation**: `docs/API_REFERENCE.md`
- **Developer Guide**: `docs/HYBRID_SEARCH_DEVELOPER_GUIDE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Example Queries**: `docs/EXAMPLE_QUERIES.md`

---

## 🤝 Support

Bei Fragen oder Problemen:
1. Check Troubleshooting Section
2. Review Test Cases (`tests/backend/test_hybrid_search_config.py`)
3. Check Logs: `tail -f data/veritas_backend.log`
4. Open Issue im Repository

---

**Version:** 1.0.0  
**Last Updated:** 2025-10-20  
**Maintainer:** VERITAS Development Team
