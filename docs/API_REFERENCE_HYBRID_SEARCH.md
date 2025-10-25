# VERITAS API Reference - Hybrid Search Endpoints

**Version:** 4.0.1  
**Last Updated:** 2025-10-20  
**Base URL:** `http://localhost:8000/api`

Comprehensive API documentation for VERITAS Hybrid Search endpoints.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
4. [Request Models](#request-models)
5. [Response Models](#response-models)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## 🎯 Overview

VERITAS provides a unified query API with multiple modes:

| Mode | Endpoint | Description | Latency |
|------|----------|-------------|---------|
| **Hybrid** | `POST /api/query/hybrid` | Multi-database + Re-ranking | ~5-8s |
| RAG | `POST /api/query/rag` | Standard RAG with UDS3 | ~3-5s |
| Ask | `POST /api/query/ask` | Direct LLM (no retrieval) | ~1-2s |
| Streaming | `POST /api/query/stream` | Progressive results | Variable |
| Unified | `POST /api/query` | Mode-agnostic endpoint | Variable |

---

## 🔐 Authentication

Currently **no authentication required** (development).

**Production:** Add Bearer token in header:
```http
Authorization: Bearer <your_api_token>
```

---

## 📡 Endpoints

### 1. Hybrid Search

**Endpoint:** `POST /api/query/hybrid`

**Description:** Multi-database hybrid search with LLM re-ranking

**Request:**
```http
POST /api/query/hybrid HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "query": "Was sind die Anforderungen für einen Bauantrag nach BauGB?",
    "model": "llama3.1:8b",
    "temperature": 0.1,
    "top_k": 20,
    "enable_reranking": true,
    "enable_rrf": true,
    "rrf_k": 60,
    "session_id": "user_session_123"
}
```

**Response:**
```json
{
    "answer": "Ein Bauantrag nach dem Baugesetzbuch (BauGB) erfordert folgende Unterlagen...",
    "sources": [
        {
            "id": "source_1",
            "title": "§ 35 BauGB - Bauen im Außenbereich",
            "content": "Im Außenbereich ist ein Vorhaben nur zulässig, wenn öffentliche Belange nicht entgegenstehen...",
            "metadata": {
                "document_id": "bauGB_35",
                "source_type": "legal",
                "file_path": "/data/bauGB.pdf",
                "page_number": 45,
                "search_method": "hybrid",
                "ranking_strategy": "reciprocal_rank_fusion",
                "original_score": 0.8523,
                "rerank_score": 0.9234,
                "score_delta": 0.0711,
                "rerank_confidence": 0.9512,
                "vector_rank": 1,
                "graph_rank": 3,
                "relational_rank": 2,
                "rrf_score": 0.04861,
                "execution_time_ms": 1250.5,
                "ieee_citation": "[1] Baugesetzbuch (BauGB), § 35 'Bauen im Außenbereich', p. 45",
                "bibtex": "@article{bauGB_35, title={§ 35 BauGB - Bauen im Außenbereich}, ...}",
                "custom_fields": {
                    "law_reference": "§ 35 BauGB",
                    "legal_area": "Baurecht",
                    "relevance_category": "high"
                }
            }
        }
    ],
    "metadata": {
        "query_id": "qry_123456",
        "query_mode": "hybrid",
        "model_used": "llama3.1:8b",
        "reranking_enabled": true,
        "total_sources": 15,
        "execution_time_ms": 5420.3,
        "retrieval_breakdown": {
            "vector_search_ms": 450.2,
            "graph_search_ms": 320.5,
            "relational_search_ms": 280.8,
            "rrf_fusion_ms": 52.3,
            "reranking_ms": 4200.1
        },
        "timestamp": "2025-10-20T14:35:22.123Z"
    }
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | User query text (max 2000 chars) |
| `model` | string | No | `llama3.1:8b` | LLM model for answer generation |
| `temperature` | float | No | `0.1` | LLM temperature (0.0-1.0) |
| `top_k` | integer | No | `20` | Max results to retrieve |
| `enable_reranking` | boolean | No | `true` | Enable LLM re-ranking |
| `enable_rrf` | boolean | No | `true` | Use RRF fusion strategy |
| `rrf_k` | integer | No | `60` | RRF k parameter (1-1000) |
| `bm25_weight` | float | No | `0.5` | ⚠️ DEPRECATED: Use environment config |
| `dense_weight` | float | No | `0.5` | ⚠️ DEPRECATED: Use environment config |
| `session_id` | string | No | `null` | Optional session identifier |

**Status Codes:**

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Invalid request parameters |
| `500` | Internal server error |
| `503` | Service unavailable (UDS3/Ollama down) |

---

### 2. Unified Query Endpoint

**Endpoint:** `POST /api/query`

**Description:** Mode-agnostic query endpoint

**Request:**
```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "query": "Erkläre § 35 BauGB",
    "mode": "hybrid",
    "model": "llama3.1:8b",
    "temperature": 0.1,
    "top_k": 20,
    "session_id": "user_session_123"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | User query text |
| `mode` | string | ✅ Yes | - | Query mode: `hybrid`, `rag`, `ask`, `streaming`, `agent` |
| `model` | string | No | `llama3.1:8b` | LLM model |
| `temperature` | float | No | `0.1` | LLM temperature |
| `top_k` | integer | No | `20` | Max results |
| `session_id` | string | No | `null` | Session ID |
| `metadata` | object | No | `{}` | Mode-specific metadata |

**Response:** Same as Hybrid Search response

---

### 3. RAG Query

**Endpoint:** `POST /api/query/rag`

**Description:** Standard RAG with UDS3 vector database

**Request:**
```http
POST /api/query/rag HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "query": "Was ist die Genehmigungspflicht nach BImSchG?",
    "model": "llama3.1:8b",
    "temperature": 0.1,
    "top_k": 10,
    "session_id": "user_session_123"
}
```

**Response:** Similar to Hybrid Search, but with `vector_search` only (no graph/relational)

---

### 4. Simple Ask

**Endpoint:** `POST /api/query/ask`

**Description:** Direct LLM query without document retrieval

**Request:**
```http
POST /api/query/ask HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
    "query": "Was ist ein Bauantrag?",
    "model": "llama3.1:8b",
    "temperature": 0.3,
    "max_tokens": 500
}
```

**Response:**
```json
{
    "answer": "Ein Bauantrag ist ein formeller Antrag...",
    "sources": [],
    "metadata": {
        "query_mode": "ask",
        "model_used": "llama3.1:8b",
        "execution_time_ms": 1250.3
    }
}
```

---

## 📥 Request Models

### HybridSearchRequest

```python
class HybridSearchRequest(BaseModel):
    query: str = Field(..., max_length=2000, description="User query text")
    model: str = Field("llama3.1:8b", description="LLM model name")
    temperature: float = Field(0.1, ge=0.0, le=1.0, description="LLM temperature")
    top_k: int = Field(20, ge=1, le=100, description="Max results")
    enable_reranking: bool = Field(True, description="Enable LLM re-ranking")
    enable_rrf: bool = Field(True, description="Use RRF fusion")
    rrf_k: int = Field(60, ge=1, le=1000, description="RRF k parameter")
    bm25_weight: float = Field(0.5, deprecated=True)  # Legacy
    dense_weight: float = Field(0.5, deprecated=True)  # Legacy
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Bauantrag Anforderungen BauGB",
                "model": "llama3.1:8b",
                "temperature": 0.1,
                "top_k": 20,
                "enable_reranking": True,
                "enable_rrf": True,
                "rrf_k": 60
            }
        }
```

### UnifiedQueryRequest

```python
class UnifiedQueryRequest(BaseModel):
    query: str = Field(..., max_length=2000)
    mode: QueryMode = Field(..., description="Query mode")
    model: str = Field("llama3.1:8b")
    temperature: float = Field(0.1, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4096)
    top_k: int = Field(20, ge=1, le=100)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### QueryMode Enum

```python
class QueryMode(str, Enum):
    ASK = "ask"              # Direct LLM
    RAG = "rag"              # Standard RAG
    HYBRID = "hybrid"        # Multi-database hybrid
    STREAMING = "streaming"  # Progressive results
    AGENT = "agent"          # Multi-agent pipeline
    VERITAS = "veritas"      # Default VERITAS mode
```

---

## 📤 Response Models

### UnifiedResponse

```python
class UnifiedResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    sources: List[UnifiedSource] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Ein Bauantrag nach BauGB erfordert...",
                "sources": [...],
                "metadata": {
                    "query_mode": "hybrid",
                    "execution_time_ms": 5420.3
                }
            }
        }
```

### UnifiedSource

```python
class UnifiedSource(BaseModel):
    id: str = Field(..., description="Unique source identifier")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Relevant excerpt")
    metadata: UnifiedSourceMetadata = Field(..., description="Source metadata")
```

### UnifiedSourceMetadata (IEEE Compliant, 35+ Fields)

```python
class UnifiedSourceMetadata(BaseModel):
    # Core Identification
    document_id: str
    source_type: str  # legal, scientific, administrative, etc.
    file_path: str
    page_number: Optional[int]
    
    # Search Metadata (Hybrid-specific)
    search_method: str  # "hybrid", "rag", "vector", etc.
    ranking_strategy: Optional[str]  # "reciprocal_rank_fusion", "weighted", "borda"
    
    # Scoring (Hybrid Search)
    original_score: float  # Pre-reranking score (0.0-1.0)
    rerank_score: Optional[float]  # Post-reranking score
    score_delta: Optional[float]  # Improvement from reranking
    rerank_confidence: Optional[float]  # Confidence in reranked score
    
    # Ranking Details
    vector_rank: Optional[int]  # Rank in vector search results
    graph_rank: Optional[int]  # Rank in graph search results
    relational_rank: Optional[int]  # Rank in relational search results
    final_rank: int  # Final rank after fusion
    
    # RRF-specific
    rrf_score: Optional[float]  # RRF fusion score
    
    # Performance
    execution_time_ms: Optional[float]
    retrieval_time_ms: Optional[float]
    reranking_time_ms: Optional[float]
    
    # IEEE Citations
    ieee_citation: str  # "[1] Title, Author, Year, p. X"
    apa_citation: Optional[str]
    bibtex: Optional[str]
    
    # Content Metadata
    authors: Optional[List[str]]
    publication_date: Optional[str]
    doi: Optional[str]
    url: Optional[str]
    
    # Legal-specific
    law_reference: Optional[str]  # "§ 35 BauGB"
    legal_area: Optional[str]  # "Baurecht", "Umweltrecht"
    relevance_category: Optional[str]  # "high", "medium", "low"
    
    # Additional
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
```

---

## ❌ Error Handling

### Error Response Format

```json
{
    "error": "Error type",
    "detail": "Detailed error message",
    "status_code": 500,
    "timestamp": "2025-10-20T14:35:22.123Z"
}
```

### Common Errors

#### 400 Bad Request

**Cause:** Invalid request parameters

```json
{
    "error": "ValidationError",
    "detail": "query field is required",
    "status_code": 400
}
```

**Solution:** Check request payload against request model

#### 500 Internal Server Error

**Cause:** Backend processing error

```json
{
    "error": "InternalServerError",
    "detail": "RAGService initialization failed",
    "status_code": 500
}
```

**Solution:** Check logs, verify UDS3/Ollama availability

#### 503 Service Unavailable

**Cause:** Required services down

```json
{
    "error": "ServiceUnavailable",
    "detail": "Ollama service not responding",
    "status_code": 503
}
```

**Solution:** Start required services (UDS3, Ollama, databases)

---

## 🚦 Rate Limiting

**Current:** No rate limiting (development)

**Production:**
- **Authenticated users:** 100 requests/minute
- **Anonymous:** 10 requests/minute

**Headers:**
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

---

## 💡 Examples

### Example 1: Basic Hybrid Search

```bash
curl -X POST http://localhost:8000/api/query/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was sind die Anforderungen für einen Bauantrag?",
    "enable_reranking": true,
    "top_k": 10
  }'
```

### Example 2: Custom Weights (via Environment)

```bash
# Set environment variables
export HYBRID_WEIGHT_VECTOR=0.7
export HYBRID_WEIGHT_GRAPH=0.2
export HYBRID_WEIGHT_RELATIONAL=0.1

# Query uses custom weights
curl -X POST http://localhost:8000/api/query/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query": "BImSchG Genehmigungspflicht"}'
```

### Example 3: Fast Mode (No Re-Ranking)

```bash
curl -X POST http://localhost:8000/api/query/hybrid \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Lärmschutz BImSchG",
    "enable_reranking": false,
    "top_k": 10
  }'
```

### Example 4: Python SDK

```python
import requests

response = requests.post(
    "http://localhost:8000/api/query/hybrid",
    json={
        "query": "Bauantrag Anforderungen BauGB",
        "model": "llama3.1:8b",
        "temperature": 0.1,
        "top_k": 20,
        "enable_reranking": True,
        "enable_rrf": True,
        "rrf_k": 60
    }
)

data = response.json()
print(f"Answer: {data['answer']}")
print(f"Sources: {len(data['sources'])}")

for source in data['sources']:
    metadata = source['metadata']
    print(f"- {source['title']}")
    print(f"  Original: {metadata['original_score']:.3f}")
    print(f"  Reranked: {metadata['rerank_score']:.3f}")
    print(f"  Delta: {metadata['score_delta']:.3f}")
```

### Example 5: JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:8000/api/query/hybrid', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'Umweltverträglichkeitsprüfung nach BImSchG',
    enable_reranking: true,
    top_k: 15
  })
});

const data = await response.json();
console.log(`Answer: ${data.answer}`);
console.log(`Sources: ${data.sources.length}`);
```

---

## 📊 Postman Collection

**Import:** `postman/VERITAS_Hybrid_Search.postman_collection.json`

**Includes:**
- All endpoint examples
- Environment variables
- Pre-request scripts
- Test assertions

**Download:**
```bash
curl -O https://veritas.example.com/postman/VERITAS_Hybrid_Search.postman_collection.json
```

---

## 📚 Related Documentation

- **Developer Guide:** `docs/HYBRID_SEARCH_DEVELOPER_GUIDE.md`
- **Configuration:** `config/README_HYBRID_CONFIG.md`
- **Architecture:** `docs/ARCHITECTURE.md`
- **OpenAPI Spec:** `http://localhost:8000/docs` (Swagger UI)
- **ReDoc:** `http://localhost:8000/redoc`

---

## 🆘 Support

**Questions?**
- Check Developer Guide
- Review examples above
- Check logs: `tail -f data/veritas_backend.log`

**Issues?**
- Verify services running: `docker ps` or `systemctl status`
- Check environment variables: `env | grep HYBRID`
- Test individual components

**Feature Requests:**
- Open GitHub issue
- Contact development team

---

**Version:** 4.0.1  
**Last Updated:** 2025-10-20  
**Maintainer:** VERITAS Development Team
