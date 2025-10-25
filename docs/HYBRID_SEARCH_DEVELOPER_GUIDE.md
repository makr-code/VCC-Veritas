# VERITAS Hybrid Search - Developer Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-20  
**Status:** Production Ready  

Umfassender Entwickler-Guide für das Hybrid Search System mit Multi-Database Retrieval und LLM-basiertem Re-Ranking.

---

## 📋 Inhaltsverzeichnis

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Usage Examples](#usage-examples)
4. [Configuration Guide](#configuration-guide)
5. [Ranking Strategies](#ranking-strategies)
6. [Performance Optimization](#performance-optimization)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [API Reference](#api-reference)

---

## 🏗️ Architecture Overview

### System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      Query Service                           │
│  (mode='hybrid' with re-ranking)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      RAG Service                             │
│              (Hybrid Search Orchestrator)                    │
└─┬──────────────────┬──────────────────┬─────────────────────┘
  │                  │                  │
  ▼                  ▼                  ▼
┌─────────┐    ┌──────────┐    ┌────────────────┐
│ ChromaDB│    │  Neo4j   │    │  PostgreSQL    │
│ (Vector)│    │ (Graph)  │    │ (Relational)   │
└─────────┘    └──────────┘    └────────────────┘
  60%             20%               20%
  │                  │                  │
  └──────────────────┴──────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Reciprocal Rank Fusion (RRF)                    │
│         score(d) = Σ[1 / (k + rank_i)]                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Reranker Service                            │
│            (LLM: llama3.1:8b via Ollama)                    │
│    Scoring: Relevance + Informativeness                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Unified Response                            │
│        (IEEE Citations, 35+ Metadata Fields)                │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Query Input** → QueryService receives query with `mode='hybrid'`
2. **Parallel Retrieval** → RAGService queries all 3 databases simultaneously
3. **Result Fusion** → RRF combines results with configurable weights
4. **Re-Ranking** → RerankerService applies LLM-based semantic scoring
5. **Response** → UnifiedResponse with IEEE citations and metadata

### Key Features

✅ **Multi-Database Retrieval**: Vector (ChromaDB) + Graph (Neo4j) + Relational (PostgreSQL)  
✅ **Flexible Fusion**: RRF, Weighted Average, Borda Count  
✅ **LLM Re-Ranking**: Semantic quality assessment with llama3.1:8b  
✅ **Configurable Weights**: Adjust Vector/Graph/Relational ratios  
✅ **Graceful Degradation**: Fallbacks for database/LLM failures  
✅ **Production Ready**: Comprehensive testing, monitoring, error handling  

---

## 🔧 Core Components

### 1. RAGService (Hybrid Search Orchestrator)

**Location:** `backend/services/rag_service.py`

**Responsibilities:**
- Orchestrates parallel queries to ChromaDB, Neo4j, PostgreSQL
- Applies SearchWeights to balance retrieval methods
- Implements RRF, Weighted, and Borda ranking strategies
- Returns HybridSearchResult with fused rankings

**Key Methods:**

```python
class RAGService:
    async def hybrid_search(
        self,
        query: str,
        weights: SearchWeights,
        filters: SearchFilters,
        ranking_strategy: RankingStrategy
    ) -> HybridSearchResult:
        """
        Execute hybrid search across all databases.
        
        Args:
            query: User query string
            weights: Vector/Graph/Relational weights (must sum to 1.0)
            filters: max_results, min_relevance, date filters
            ranking_strategy: RRF, WEIGHTED, or BORDA
        
        Returns:
            HybridSearchResult with ranked documents
        """
```

**Example Usage:**

```python
from backend.services.rag_service import RAGService
from config.hybrid_search_config import SearchWeights, SearchFilters, RankingStrategy

rag_service = RAGService(chromadb=..., neo4j=..., postgresql=...)

result = await rag_service.hybrid_search(
    query="Was sind die Anforderungen für einen Bauantrag?",
    weights=SearchWeights(vector=0.6, graph=0.2, relational=0.2),
    filters=SearchFilters(max_results=20, min_relevance=0.5),
    ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION
)

print(f"Found {len(result.documents)} documents")
print(f"Execution time: {result.execution_time_ms}ms")
```

### 2. RerankerService (LLM-based Semantic Scoring)

**Location:** `backend/services/reranker_service.py`

**Responsibilities:**
- LLM-based semantic quality assessment
- Batch processing for efficiency (default: 5 docs/batch)
- Score documents on relevance + informativeness
- Graceful fallback on LLM errors

**Key Methods:**

```python
class RerankerService:
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        batch_size: int = 5,
        scoring_mode: ScoringMode = ScoringMode.COMBINED
    ) -> List[RerankingResult]:
        """
        Re-rank documents using LLM scoring.
        
        Args:
            query: Original user query
            documents: List of documents to rerank
            batch_size: Documents per LLM batch call
            scoring_mode: RELEVANCE_ONLY, INFORMATIVENESS_ONLY, COMBINED
        
        Returns:
            List of RerankingResult with updated scores
        """
```

**Example Usage:**

```python
from backend.services.reranker_service import RerankerService, ScoringMode

reranker = RerankerService(
    model_name="llama3.1:8b",
    scoring_mode=ScoringMode.COMBINED,
    temperature=0.1
)

documents = [
    {"document_id": "doc1", "content": "...", "score": 0.85},
    {"document_id": "doc2", "content": "...", "score": 0.82},
]

results = reranker.rerank(
    query="Bauantrag Anforderungen",
    documents=documents,
    batch_size=5
)

for result in results:
    print(f"Doc {result.document_id}: {result.original_score:.3f} → {result.new_score:.3f}")
```

### 3. QueryService (Hybrid Mode Integration)

**Location:** `backend/services/query_service.py`

**Responsibilities:**
- Entry point for all query modes (rag, hybrid, streaming, agent, ask)
- Integrates RAGService + RerankerService
- Converts results to UnifiedResponse format
- Implements error handling and fallbacks

**Key Methods:**

```python
class QueryService:
    async def _process_hybrid(
        self,
        query: str,
        enable_reranking: bool = True
    ) -> UnifiedResponse:
        """
        Process hybrid search query with optional re-ranking.
        
        Args:
            query: User query string
            enable_reranking: Whether to apply LLM re-ranking
        
        Returns:
            UnifiedResponse with IEEE citations
        """
```

### 4. HybridSearchConfig (Configuration System)

**Location:** `config/hybrid_search_config.py`

**Responsibilities:**
- Centralized configuration for all hybrid search settings
- Environment variable support
- Preset configurations (balanced, fast, accurate, etc.)
- Validation and type safety

**Key Classes:**

```python
@dataclass
class SearchWeights:
    vector: float = 0.6      # ChromaDB weight
    graph: float = 0.2       # Neo4j weight
    relational: float = 0.2  # PostgreSQL weight

@dataclass
class ReRankingConfig:
    enabled: bool = True
    model_name: str = "llama3.1:8b"
    scoring_mode: ScoringMode = ScoringMode.COMBINED
    temperature: float = 0.1
    batch_size: int = 5
```

---

## 💻 Usage Examples

### Example 1: Basic Hybrid Search

```python
from backend.services.query_service import QueryService
from config.hybrid_search_config import DEFAULT_CONFIG

# Initialize service
query_service = QueryService()

# Execute hybrid search
response = await query_service.process_query(
    query="Was sind die Voraussetzungen für einen Bauantrag nach BauGB?",
    mode="hybrid"
)

# Access results
print(f"Answer: {response.answer}")
print(f"Sources: {len(response.sources)}")

for source in response.sources:
    print(f"- {source.title} (Score: {source.metadata.custom_fields.get('rerank_score', 'N/A')})")
```

### Example 2: Custom Weights (Entity-Heavy Search)

```python
from config.hybrid_search_config import HybridSearchConfig, SearchWeights

# Create custom config
config = HybridSearchConfig(
    weights=SearchWeights(
        vector=0.4,      # Less semantic search
        graph=0.4,       # More entity relationships
        relational=0.2   # Standard metadata
    )
)

# Use in QueryService
query_service = QueryService()
query_service.config = config

response = await query_service.process_query(
    query="Zeige alle Paragraphen die auf § 35 BauGB verweisen",
    mode="hybrid"
)
```

### Example 3: Fast Mode (No Re-Ranking)

```python
from config.hybrid_search_config import get_preset_config

# Load fast preset
config = get_preset_config("fast")

query_service = QueryService()
query_service.config = config

# Fast search (~2s)
response = await query_service.process_query(
    query="BImSchG Lärmschutz",
    mode="hybrid"
)
```

### Example 4: Accurate Mode (Maximum Quality)

```python
from config.hybrid_search_config import get_preset_config

# Load accurate preset
config = get_preset_config("accurate")

query_service = QueryService()
query_service.config = config

# Accurate search (~10s)
response = await query_service.process_query(
    query="Detaillierte Analyse der Genehmigungspflicht nach § 4 BImSchG",
    mode="hybrid"
)
```

### Example 5: Environment-Based Configuration

```bash
# .env file
HYBRID_SEARCH_ENABLED=true
HYBRID_RANKING_STRATEGY=reciprocal_rank_fusion
HYBRID_WEIGHT_VECTOR=0.7
HYBRID_WEIGHT_GRAPH=0.2
HYBRID_WEIGHT_RELATIONAL=0.1
RERANKING_ENABLED=true
RERANKING_MODEL=llama3.1:8b
```

```python
from config.hybrid_search_config import load_config_from_env

# Load from environment
config = load_config_from_env()

query_service = QueryService()
query_service.config = config

# Uses environment settings
response = await query_service.process_query(
    query="Umweltverträglichkeitsprüfung",
    mode="hybrid"
)
```

---

## ⚙️ Configuration Guide

### Configuration Hierarchy

1. **Code-based (highest priority)**
   ```python
   config = HybridSearchConfig(weights=SearchWeights(...))
   ```

2. **Environment Variables**
   ```bash
   export HYBRID_WEIGHT_VECTOR=0.7
   ```

3. **Presets**
   ```python
   config = get_preset_config("production")
   ```

4. **Defaults (lowest priority)**
   - Vector: 60%, Graph: 20%, Relational: 20%
   - RRF with k=60
   - Re-ranking enabled

### Configuration Parameters

#### SearchWeights

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| vector | 0.6 | 0.0-1.0 | ChromaDB semantic search weight |
| graph | 0.2 | 0.0-1.0 | Neo4j knowledge graph weight |
| relational | 0.2 | 0.0-1.0 | PostgreSQL metadata weight |

**Constraint:** Must sum to 1.0

**Recommendations:**
- Semantic queries: `vector=0.7+`
- Entity queries: `graph=0.4+`
- Structured queries: `relational=0.3+`

#### SearchFilters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| max_results | 20 | 1-100 | Max results per retriever |
| min_relevance | 0.5 | 0.0-1.0 | Minimum relevance threshold |

**Recommendations:**
- Fast mode: `max_results=10`
- Balanced: `max_results=20`
- Accurate: `max_results=30-50`

#### RRFConfig

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| k | 60 | 1-1000 | RRF smoothing parameter |

**Formula:** `score(d) = Σ[1 / (k + rank_i)]`

**Recommendations:**
- Sharp distribution: `k=10-30`
- Balanced: `k=60`
- Flat distribution: `k=100+`

#### ReRankingConfig

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| enabled | true | bool | Enable/disable re-ranking |
| model_name | llama3.1:8b | string | Ollama model name |
| scoring_mode | COMBINED | enum | RELEVANCE_ONLY, INFORMATIVENESS_ONLY, COMBINED |
| temperature | 0.1 | 0.0-1.0 | LLM temperature for scoring |
| batch_size | 5 | 1-20 | Documents per LLM batch |
| timeout_seconds | 30 | 1-300 | Timeout per batch |
| max_retries | 2 | 0-10 | Retry attempts on failure |

---

## 🎯 Ranking Strategies

### 1. Reciprocal Rank Fusion (RRF) ⭐ RECOMMENDED

**Formula:**
$$
score(d) = \sum_{r \in R} \frac{1}{k + rank_r(d)}
$$

Where:
- $R$ = set of retrievers (Vector, Graph, Relational)
- $rank_r(d)$ = rank of document $d$ in retriever $r$
- $k$ = smoothing constant (default: 60)

**Characteristics:**
- ✅ No score normalization required
- ✅ Robust to outliers
- ✅ Emphasizes top-ranked documents
- ⚠️ Slightly slower than weighted average

**Use Cases:**
- General-purpose hybrid search
- Production deployments
- When retriever scores have different scales

**Example:**

```python
from config.hybrid_search_config import RankingStrategy

config = HybridSearchConfig(
    ranking_strategy=RankingStrategy.RECIPROCAL_RANK_FUSION,
    rrf_config=RRFConfig(k=60)
)
```

**Performance:** ~50ms overhead vs. weighted

### 2. Weighted Combination

**Formula:**
$$
score(d) = w_v \cdot s_v(d) + w_g \cdot s_g(d) + w_r \cdot s_r(d)
$$

Where:
- $w_v, w_g, w_r$ = weights (must sum to 1.0)
- $s_v, s_g, s_r$ = normalized scores from each retriever

**Characteristics:**
- ✅ Fastest strategy (~20ms)
- ✅ Simple and interpretable
- ⚠️ Requires score normalization
- ⚠️ Sensitive to score scales

**Use Cases:**
- Low-latency requirements (<2s)
- Score ranges are known and consistent
- Fast mode presets

**Example:**

```python
config = HybridSearchConfig(
    ranking_strategy=RankingStrategy.WEIGHTED_COMBINATION,
    weights=SearchWeights(vector=0.7, graph=0.2, relational=0.1)
)
```

**Performance:** ~20ms overhead

### 3. Borda Count (Experimental)

**Formula:**
$$
score(d) = \sum_{r \in R} (N - rank_r(d)) \cdot w_r
$$

Where:
- $N$ = total number of documents
- $rank_r(d)$ = rank in retriever $r$
- $w_r$ = weight for retriever $r$

**Characteristics:**
- ✅ Position-based (not score-based)
- ✅ Robust to score variations
- ⚠️ Slower for large result sets
- ⚠️ Experimental (limited testing)

**Use Cases:**
- Research and experimentation
- When scores are unreliable
- Benchmarking against RRF

**Example:**

```python
config = HybridSearchConfig(
    ranking_strategy=RankingStrategy.BORDA_COUNT,
    weights=SearchWeights(vector=0.6, graph=0.2, relational=0.2)
)
```

**Performance:** ~100ms overhead (large result sets)

### Strategy Comparison

| Metric | RRF | Weighted | Borda |
|--------|-----|----------|-------|
| Speed | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Accuracy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Robustness | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Interpretability | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Production Ready | ✅ | ✅ | ⚠️ |

### Decision Tree: Which Strategy?

```
START
  │
  ├─ Latency < 2s?
  │   └─ YES → Weighted Combination
  │
  ├─ Score ranges consistent?
  │   └─ NO → RRF (recommended)
  │
  ├─ Research/Benchmarking?
  │   └─ YES → Try Borda Count
  │
  └─ Default → RRF (Reciprocal Rank Fusion)
```

---

## ⚡ Performance Optimization

### Latency Breakdown (Balanced Config)

```
Total Query Time: ~5-8s
├─ Hybrid Search: ~1s (20%)
│   ├─ Vector (ChromaDB): ~400ms
│   ├─ Graph (Neo4j): ~300ms
│   └─ Relational (PostgreSQL): ~300ms
├─ RRF Fusion: ~50ms (1%)
├─ Re-Ranking (5 docs): ~4s (75%)
└─ Response Formatting: ~50ms (1%)
```

### Optimization Strategies

#### 1. Fast Mode (<2s)

```python
config = get_preset_config("fast")
# - Disable re-ranking
# - Reduce max_results to 10
# - Use weighted_combination
```

**Expected:** ~2s total latency

#### 2. Batch Size Tuning

```python
# Smaller batches = more LLM calls but lower memory
config.reranking_config.batch_size = 3  # For accuracy

# Larger batches = fewer LLM calls but more memory
config.reranking_config.batch_size = 10  # For speed
```

#### 3. Parallel Retrieval

RAGService already parallelizes database queries:

```python
async with asyncio.gather(
    self._vector_search(query),
    self._graph_search(query),
    self._relational_search(query)
) as results:
    # All queries run simultaneously
```

#### 4. Caching (Recommended for Production)

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_hybrid_search(query: str) -> HybridSearchResult:
    # Cache frequent queries
    return rag_service.hybrid_search(query, ...)
```

#### 5. GPU Acceleration (Re-Ranking)

```bash
# Install Ollama with GPU support
curl -fsSL https://ollama.com/install.sh | sh

# Pull GPU-optimized model
ollama pull llama3.1:8b

# Configure GPU usage
export OLLAMA_NUM_GPU=1
```

**Expected:** ~50% faster re-ranking

### Performance Benchmarks

| Config | Hybrid Search | Re-Ranking | Total | Use Case |
|--------|--------------|------------|-------|----------|
| Fast | ~500ms | Disabled | **~2s** | Interactive UI |
| Balanced | ~1s | ~4s | **~5-8s** | Production default |
| Accurate | ~1.5s | ~8s | **~10-12s** | Research/Analysis |
| GPU Accelerated | ~1s | ~2s | **~3-4s** | High-throughput |

---

## ✅ Best Practices

### 1. Configuration Management

**✓ DO:**
- Use environment variables for deployment-specific settings
- Version control `.env.example` but not `.env`
- Validate configuration on startup
- Use presets as starting points

**✗ DON'T:**
- Hardcode configurations in application code
- Commit sensitive credentials to Git
- Change weights without testing impact

### 2. Weight Tuning

**Start with Balanced:**
```python
weights = SearchWeights(vector=0.6, graph=0.2, relational=0.2)
```

**Iterate based on domain:**

| Domain | Vector | Graph | Relational | Reasoning |
|--------|--------|-------|------------|-----------|
| Legal documents | 0.4 | 0.4 | 0.2 | Strong entity relationships (§ references) |
| General knowledge | 0.7 | 0.2 | 0.1 | Semantic similarity primary |
| Structured data | 0.5 | 0.2 | 0.3 | Metadata filters important |
| Research papers | 0.6 | 0.3 | 0.1 | Citations and entity links |

### 3. Error Handling

```python
try:
    response = await query_service.process_query(query, mode="hybrid")
except Exception as e:
    logger.error(f"Hybrid search failed: {e}")
    # Fallback to dense-only search
    response = await query_service.process_query(query, mode="rag")
```

### 4. Monitoring

```python
import time

start = time.time()
response = await query_service.process_query(query, mode="hybrid")
latency_ms = (time.time() - start) * 1000

logger.info(f"Hybrid search completed in {latency_ms:.2f}ms")
logger.info(f"Sources: {len(response.sources)}")
logger.info(f"Re-ranking: {response.metadata.get('reranking_enabled', False)}")
```

### 5. Testing

```python
# Unit tests with mocked dependencies
@pytest.mark.asyncio
async def test_hybrid_search():
    rag_service = MockRAGService()
    reranker_service = MockRerankerService()
    
    query_service = QueryService(rag_service, reranker_service)
    response = await query_service.process_query("test", mode="hybrid")
    
    assert response.answer is not None
    assert len(response.sources) > 0

# Integration tests with real services
@pytest.mark.integration
async def test_hybrid_search_e2e():
    query_service = QueryService()  # Real services
    response = await query_service.process_query(
        "Bauantrag Anforderungen",
        mode="hybrid"
    )
    
    assert response.answer is not None
```

---

## 🔍 Troubleshooting

### Common Issues

#### Issue 1: "RAGService not available"

**Symptoms:**
- Error: `RAGService initialization failed`
- Fallback to mock response

**Diagnosis:**
```python
# Check UDS3 components
logger.info(f"ChromaDB: {chromadb.is_available()}")
logger.info(f"Neo4j: {neo4j.is_available()}")
logger.info(f"PostgreSQL: {postgresql.is_available()}")
```

**Solutions:**
1. Ensure all databases are running
2. Check connection strings in `.env`
3. Verify credentials
4. Test database connections individually

#### Issue 2: "RerankerService timeout"

**Symptoms:**
- Timeout after 30s
- Re-ranking step fails
- Fallback to original scores

**Diagnosis:**
```python
# Check Ollama status
!ollama list
!ollama ps

# Test model
!ollama run llama3.1:8b "Test query"
```

**Solutions:**
1. Increase timeout: `RERANKING_TIMEOUT=60`
2. Reduce batch size: `RERANKING_BATCH_SIZE=3`
3. Use smaller model: `RERANKING_MODEL=llama3.2:3b`
4. Disable re-ranking: `RERANKING_ENABLED=false`

#### Issue 3: "Weights must sum to 1.0"

**Symptoms:**
- ValueError on config load
- Application fails to start

**Diagnosis:**
```python
# Check weight sum
weights = SearchWeights(vector=0.5, graph=0.3, relational=0.3)
total = weights.vector + weights.graph + weights.relational
print(f"Weight sum: {total}")  # Should be 1.0
```

**Solutions:**
```python
# ✗ Wrong (sum = 1.1)
weights = SearchWeights(vector=0.5, graph=0.3, relational=0.3)

# ✓ Correct (sum = 1.0)
weights = SearchWeights(vector=0.6, graph=0.2, relational=0.2)
```

#### Issue 4: Slow Performance

**Symptoms:**
- Queries take >10s
- Timeout in production
- Poor user experience

**Diagnosis:**
```python
# Measure component latency
import time

start = time.time()
hybrid_result = await rag_service.hybrid_search(...)
hybrid_ms = (time.time() - start) * 1000

start = time.time()
rerank_results = reranker_service.rerank(...)
rerank_ms = (time.time() - start) * 1000

logger.info(f"Hybrid: {hybrid_ms:.2f}ms, Rerank: {rerank_ms:.2f}ms")
```

**Solutions:**
1. Use fast preset
2. Reduce max_results
3. Disable re-ranking for fast queries
4. Enable GPU acceleration
5. Implement caching

#### Issue 5: Poor Result Quality

**Symptoms:**
- Irrelevant results
- Low user feedback scores
- Wrong documents ranked high

**Diagnosis:**
```python
# Check scores and metadata
for source in response.sources:
    print(f"{source.title}")
    print(f"  Original: {source.metadata.custom_fields.get('original_score')}")
    print(f"  Reranked: {source.metadata.custom_fields.get('rerank_score')}")
    print(f"  Search method: {source.metadata.custom_fields.get('search_method')}")
```

**Solutions:**
1. Use accurate preset
2. Increase max_results
3. Lower min_relevance threshold
4. Enable re-ranking
5. Adjust weights for domain
6. Use RRF instead of weighted

---

## 📚 API Reference

### QueryService.process_query()

```python
async def process_query(
    query: str,
    mode: str = "hybrid",
    enable_reranking: bool = True,
    **kwargs
) -> UnifiedResponse:
    """
    Process user query with specified mode.
    
    Args:
        query: User query string
        mode: Query mode ('rag', 'hybrid', 'streaming', 'agent', 'ask')
        enable_reranking: Whether to apply LLM re-ranking (hybrid mode only)
        **kwargs: Additional mode-specific parameters
    
    Returns:
        UnifiedResponse with answer, sources, and metadata
    
    Raises:
        ValueError: If mode is invalid
        RuntimeError: If RAGService/RerankerService unavailable
    """
```

### RAGService.hybrid_search()

```python
async def hybrid_search(
    query: str,
    weights: SearchWeights,
    filters: SearchFilters,
    ranking_strategy: RankingStrategy = RankingStrategy.RECIPROCAL_RANK_FUSION
) -> HybridSearchResult:
    """
    Execute hybrid search across all databases.
    
    Args:
        query: User query string
        weights: Vector/Graph/Relational weights (must sum to 1.0)
        filters: Search filters (max_results, min_relevance, etc.)
        ranking_strategy: Fusion strategy (RRF, WEIGHTED, BORDA)
    
    Returns:
        HybridSearchResult with ranked documents
    
    Raises:
        ValueError: If weights invalid or databases unavailable
    """
```

### RerankerService.rerank()

```python
def rerank(
    query: str,
    documents: List[Dict[str, Any]],
    batch_size: int = 5,
    scoring_mode: ScoringMode = ScoringMode.COMBINED
) -> List[RerankingResult]:
    """
    Re-rank documents using LLM scoring.
    
    Args:
        query: Original user query
        documents: List of documents to rerank
        batch_size: Documents per LLM batch call
        scoring_mode: RELEVANCE_ONLY, INFORMATIVENESS_ONLY, COMBINED
    
    Returns:
        List of RerankingResult with updated scores
    
    Raises:
        TimeoutError: If LLM call exceeds timeout
        RuntimeError: If Ollama unavailable
    """
```

### HybridSearchConfig

```python
@dataclass
class HybridSearchConfig:
    weights: SearchWeights
    filters: SearchFilters
    rrf_config: RRFConfig
    reranking_config: ReRankingConfig
    ranking_strategy: RankingStrategy
    enable_hybrid_search: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
```

---

## 📖 Further Reading

- **Configuration Guide:** `config/README_HYBRID_CONFIG.md`
- **API Documentation:** `docs/API_REFERENCE.md` (see Task 14)
- **Architecture Overview:** `docs/ARCHITECTURE.md`
- **Test Suite:** `tests/backend/test_hybrid_search_*.py`
- **Benchmarks:** `docs/RANKING_STRATEGY_BENCHMARK.md` (see Task 16)

---

## 🤝 Support & Contributing

**Questions?**
- Check this guide first
- Review test cases for examples
- Check logs: `tail -f data/veritas_backend.log`

**Issues?**
- Review Troubleshooting section
- Check environment variables
- Enable DEBUG logging

**Contributing:**
- Add test cases for new features
- Update documentation
- Follow code style (Black, isort, mypy)

---

**Maintainer:** VERITAS Development Team  
**License:** Proprietary  
**Last Review:** 2025-10-20
