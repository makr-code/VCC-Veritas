# VERITAS API v3 - Complete Reference Guide
**Version:** 3.0.0  
**Release Date:** 18. Oktober 2025  
**Base URL:** `http://localhost:5000/api/v3`  
**Documentation:** `/docs` (Swagger UI)

---

## 📋 Quick Reference

| Router | File | Endpoints | Purpose |
|--------|------|-----------|---------|
| Query | `query_router.py` | 5 | Main query operations |
| Agent | `agent_router.py` | 4 | Agent management |
| System | `system_router.py` | 5 | System info & health |
| VPB | `vpb_router.py` | 3 | VPB domain queries |
| COVINA | `covina_router.py` | 4 | COVINA domain queries |
| IMMI | `immi_router.py` | 3 | Geographic/spatial data |
| PKI | `pki_router.py` | 4 | Cryptographic operations |
| Database | `database_router.py` | 5 | Database management |
| UDS3 | `uds3_router.py` | 4 | Unified database strategy |
| Themis | `themis_router.py` | 5 | Advanced query compilation |
| Compliance | `compliance_router.py` | 4 | Compliance & audit |
| Governance | `governance_router.py` | 3 | Config & governance |
| Adapter | `adapter_router.py` | 4 | Custom adapter management |
| User | `user_router.py` | 4 | Authentication & profiles |
| **TOTAL** | | **58+** | |

---

## 🔷 1. QUERY ROUTER - Core Query Operations

### POST /api/v3/query
**Unified Query Endpoint** - Processes queries in any supported mode

**Request:**
```json
{
  "query": "Was sind die aktuellen BImSchG Regelungen?",
  "mode": "hybrid",
  "include_sources": true,
  "top_k": 5,
  "use_streaming": false
}
```

**Parameters:**
- `query` (string, required) - Query text
- `mode` (string, enum) - Query mode: `rag` | `keyword` | `semantic` | `hybrid` | `vfb`
- `include_sources` (boolean) - Include source references
- `top_k` (integer, default: 5) - Number of results
- `use_streaming` (boolean) - Enable streaming response

**Response:**
```json
{
  "query_id": "q-12345-67890",
  "result": "Die aktuellen BImSchG Regelungen...",
  "sources": [
    {
      "document": "BImSchG § 58",
      "relevance": 0.92,
      "excerpt": "...",
      "url": "..."
    }
  ],
  "execution_time": 1.234,
  "model": "gpt-4o",
  "citations": [
    {"type": "IEEE", "text": "[1] §58, BImSchG (2025)"}
  ]
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid query mode or parameters
- `429` - Rate limit exceeded
- `500` - Server error

---

### POST /api/v3/query/ask
**Simple Q&A** - Direct answers without RAG

**Request:**
```json
{
  "question": "Was ist Verwaltungsrecht?"
}
```

**Response:**
```json
{
  "answer": "Verwaltungsrecht ist...",
  "confidence": 0.85,
  "processing_time": 0.456
}
```

---

### POST /api/v3/query/rag
**Retrieval-Augmented Generation** - Queries with source retrieval

**Request:**
```json
{
  "query": "BImSchG Anforderungen Genehmigung",
  "max_sources": 10,
  "rerank": true,
  "chunk_size": 1000
}
```

**Response:**
```json
{
  "answer": "...",
  "retrieved_documents": 8,
  "chunks": [
    {
      "id": "chunk-001",
      "text": "...",
      "metadata": {"source": "BImSchG", "section": "§58"}
    }
  ],
  "reranked_score": 0.87
}
```

---

### POST /api/v3/query/hybrid
**Hybrid Search** - Combined keyword + semantic search

**Request:**
```json
{
  "query": "Umweltschutz Genehmigung",
  "keyword_weight": 0.5,
  "semantic_weight": 0.5
}
```

**Response:**
```json
{
  "combined_results": [...],
  "keyword_results": 12,
  "semantic_results": 8,
  "merged_score": 0.89
}
```

---

### POST /api/v3/query/stream
**Streaming Query** - Real-time token-by-token streaming

**Request:**
```json
{
  "query": "Erklären Sie BImSchG",
  "stream_buffer_size": 50
}
```

**Response:** 
Server-Sent Events (SSE) stream
```
data: {"token": "Die", "cumulative": "Die"}
data: {"token": "Bundes", "cumulative": "Die Bundes"}
data: {"token": "-", "cumulative": "Die Bundes-"}
...
data: {"complete": true, "total_tokens": 256}
```

---

## 🔷 2. AGENT ROUTER - Agent Management

### GET /api/v3/agents/list
**List Available Agents**

**Response:**
```json
{
  "agents": [
    {
      "id": "rag-agent",
      "name": "RAG Agent",
      "status": "active",
      "description": "Retrieval-Augmented Generation",
      "capabilities": ["query", "retrieval", "ranking"]
    },
    {
      "id": "vpb-agent",
      "name": "VPB Agent",
      "status": "active",
      "description": "Verwaltungsrecht Processing",
      "capabilities": ["analysis", "citation", "inference"]
    }
  ],
  "total": 5
}
```

---

### GET /api/v3/agents/{id}/status
**Agent Status**

**Path Parameters:**
- `id` (string) - Agent ID

**Response:**
```json
{
  "id": "rag-agent",
  "status": "healthy",
  "uptime_seconds": 123456,
  "processed_queries": 1234,
  "avg_response_time": 0.856,
  "last_error": null,
  "memory_usage": "256MB",
  "gpu_usage": "4GB"
}
```

---

### GET /api/v3/agents/capabilities
**Capabilities Matrix**

**Response:**
```json
{
  "rag": {
    "retrieval": true,
    "ranking": true,
    "streaming": true,
    "sources": true
  },
  "vpb": {
    "citation": true,
    "inference": true,
    "validation": true,
    "export": true
  }
}
```

---

### POST /api/v3/agents/{id}/execute
**Execute Custom Agent**

**Request:**
```json
{
  "input": {"query": "..."},
  "parameters": {"timeout": 30}
}
```

---

## 🔷 3. SYSTEM ROUTER - System Operations

### GET /api/v3/system/health
**Health Status**

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-04T12:34:56Z",
  "services": {
    "backend": "running",
    "database": "connected",
    "cache": "connected",
    "search": "running"
  },
  "databases": {
    "postgresql": {"status": "connected", "latency_ms": 5},
    "chromadb": {"status": "connected", "latency_ms": 12},
    "neo4j": {"status": "connected", "latency_ms": 8}
  }
}
```

---

### GET /api/v3/system/info
**System Information**

**Response:**
```json
{
  "version": "4.0.0",
  "api_version": "3.0.0",
  "environment": "production",
  "release_date": "2025-10-18",
  "features": {
    "streaming": true,
    "websocket": true,
    "uds3": true,
    "themis": true
  }
}
```

---

### GET /api/v3/system/status
**Full Status Report**

**Response:**
```json
{
  "uptime": 7891234,
  "memory": {"used": "2.3GB", "available": "5.7GB"},
  "cpu": {"usage": 23.4, "cores": 8},
  "requests": {"total": 45678, "active": 12},
  "errors": {"24h": 3, "7d": 15}
}
```

---

### GET /api/v3/system/metrics
**Performance Metrics**

**Query Parameters:**
- `period` (string) - Time period: `1h` | `24h` | `7d`
- `metric` (string) - Specific metric name

**Response:**
```json
{
  "period": "24h",
  "metrics": {
    "query_latency": {"p50": 0.456, "p95": 1.234, "p99": 2.567},
    "error_rate": 0.001,
    "cache_hit_rate": 0.87,
    "throughput_qps": 234.5
  }
}
```

---

### POST /api/v3/system/config
**Configuration Updates**

**Request:**
```json
{
  "setting": "max_chunk_size",
  "value": 1500
}
```

---

## 🔷 4. DOMAIN ROUTERS

### VPB ROUTER (`vpb_router.py`)

#### POST /api/v3/vpb/analyze
**Analyze VPB Data**
```json
{
  "data": {...},
  "analysis_type": "compliance"
}
```

#### GET /api/v3/vpb/models
**List VPB Models**

#### POST /api/v3/vpb/predict
**Make Predictions**

---

### COVINA ROUTER (`covina_router.py`)

#### POST /api/v3/covina/query
**COVINA Domain Query**

#### GET /api/v3/covina/sources
**Available Sources**

#### POST /api/v3/covina/validate
**Validate Queries**

#### GET /api/v3/covina/status
**COVINA Service Status**

---

### IMMI ROUTER (`immi_router.py`)

#### GET /api/v3/immi/markers/bimschg
**BImSchG Geographic Markers**

**Query Parameters:**
- `bbox` (string) - Bounding box: "lat1,lon1,lat2,lon2"
- `limit` (integer) - Max results

**Response:**
```json
{
  "markers": [
    {
      "id": "m-001",
      "name": "Industrie Gebiet Nord",
      "lat": 52.5200,
      "lon": 13.4050,
      "category": "industrial",
      "regulations": ["BImSchG §58"]
    }
  ]
}
```

---

#### GET /api/v3/immi/markers/wka
**WKA (Windenergieanlage) Markers**

---

#### POST /api/v3/immi/search
**Spatial Search**

```json
{
  "query": "Industrie",
  "geometry": {"type": "Point", "coordinates": [13.4050, 52.5200]},
  "radius_km": 10
}
```

---

## 🔷 5. DATA INTEGRATION ROUTERS

### DATABASE ROUTER (`database_router.py`)

#### GET /api/v3/database/status
**Database Connection Status**

#### GET /api/v3/database/stats
**Database Statistics**

#### POST /api/v3/database/query
**Execute Custom Query**

```json
{
  "query": "SELECT * FROM documents WHERE ...",
  "database": "postgresql"
}
```

#### GET /api/v3/database/schema
**Database Schema**

#### POST /api/v3/database/migrate
**Run Migrations**

---

### UDS3 ROUTER (`uds3_router.py`)

#### POST /api/v3/uds3/query
**Unified Database Query**

```json
{
  "query": "BImSchG regulations",
  "auto_route": true,
  "preferred_database": null
}
```

#### GET /api/v3/uds3/sources
**Available Data Sources**

#### POST /api/v3/uds3/optimize
**Optimize Query Routing**

#### GET /api/v3/uds3/status
**UDS3 Health Status**

---

### THEMIS ROUTER (`themis_router.py`)

#### POST /api/v3/themis/query
**ThemisDB Query**

#### GET /api/v3/themis/status
**Themis Service Status**

#### GET /api/v3/themis/schema
**Themis Database Schema**

#### POST /api/v3/themis/compile
**Compile AQL Queries**

```json
{
  "aql_query": "MATCH (n:Document) WHERE n.type='regulation' RETURN n"
}
```

#### GET /api/v3/themis/benchmarks
**Performance Benchmarks**

---

## 🔷 6. ENTERPRISE ROUTERS

### COMPLIANCE ROUTER (`compliance_router.py`)

#### GET /api/v3/compliance/rules
**Compliance Rules**

#### POST /api/v3/compliance/check
**Check Compliance**

```json
{
  "document": "...",
  "standard": "ISO27001"
}
```

#### GET /api/v3/compliance/audit
**Audit Trail**

#### POST /api/v3/compliance/report
**Generate Report**

---

### GOVERNANCE ROUTER (`governance_router.py`)

#### GET /api/v3/governance/config
**Configuration Management**

#### POST /api/v3/governance/policy
**Policy Updates**

#### GET /api/v3/governance/audit
**Governance Audit**

---

### ADAPTER ROUTER (`adapter_router.py`)

#### GET /api/v3/adapters/list
**List Custom Adapters**

#### POST /api/v3/adapters/register
**Register Adapter**

#### POST /api/v3/adapters/{id}/test
**Test Adapter**

#### DELETE /api/v3/adapters/{id}
**Remove Adapter**

---

### USER ROUTER (`user_router.py`)

#### POST /api/v3/users/login
**User Authentication**

```json
{
  "username": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 3600,
  "user": {"id": "u-001", "email": "user@example.com"}
}
```

#### GET /api/v3/users/profile
**User Profile**

**Headers:**
```
Authorization: Bearer <token>
```

#### POST /api/v3/users/preferences
**Update Preferences**

#### POST /api/v3/users/logout
**User Logout**

---

### PKI ROUTER (`pki_router.py`)

#### POST /api/v3/pki/verify
**Verify Signatures**

```json
{
  "signature": "...",
  "certificate": "...",
  "data": "..."
}
```

#### POST /api/v3/pki/encrypt
**Encrypt Data**

#### POST /api/v3/pki/decrypt
**Decrypt Data**

#### GET /api/v3/pki/certs
**List Certificates**

---

### SAGA ROUTER (`saga_router.py`)

#### POST /api/v3/saga/execute
**Execute SAGA Pattern**

```json
{
  "workflow": "process_document",
  "steps": [...]
}
```

#### GET /api/v3/saga/{id}/status
**Check SAGA Status**

#### POST /api/v3/saga/{id}/rollback
**Rollback SAGA**

---

## 🔷 7. WEBSOCKET ROUTER

### WS /api/v3/ws/streaming
**Real-time Streaming**

**Message Types:**
```json
{"type": "query", "query": "..."}
{"type": "subscribe", "channel": "notifications"}
```

---

## 🔐 Authentication

All endpoints (except `/health`) require authentication:

```bash
# Login first
curl -X POST http://localhost:5000/api/v3/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com", "password":"..."}'

# Use returned token
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/v3/system/info
```

---

## 🚫 Error Handling

### Standard Error Response
```json
{
  "detail": "Error message",
  "error_code": "INVALID_QUERY_MODE",
  "status_code": 400,
  "timestamp": "2025-12-04T12:34:56Z"
}
```

### Common Error Codes
- `INVALID_QUERY_MODE` (400) - Unknown query mode
- `RATE_LIMIT_EXCEEDED` (429) - Too many requests
- `AUTHENTICATION_REQUIRED` (401) - Missing or invalid token
- `PERMISSION_DENIED` (403) - Insufficient permissions
- `RESOURCE_NOT_FOUND` (404) - Resource doesn't exist
- `INTERNAL_SERVER_ERROR` (500) - Server-side error

---

## 📊 Rate Limiting

**Default Limits:**
- 1000 requests per minute (global)
- 100 requests per minute (per user)
- 10 concurrent streams

**Response Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 987
X-RateLimit-Reset: 1733316300
```

---

## 🔗 Pagination

For list endpoints:

**Query Parameters:**
- `skip` (integer) - Offset
- `limit` (integer) - Items per page (max: 100)

**Response:**
```json
{
  "items": [...],
  "total": 1234,
  "skip": 0,
  "limit": 10,
  "has_more": true
}
```

---

## 📋 Request/Response Examples

### Example 1: Query with Sources
```bash
curl -X POST http://localhost:5000/api/v3/query \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was sind die Anforderungen nach BImSchG?",
    "mode": "hybrid",
    "include_sources": true,
    "top_k": 5
  }'
```

### Example 2: Streaming Query
```bash
curl -X POST http://localhost:5000/api/v3/query/stream \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Erklär BImSchG"
  }' \
  --stream
```

### Example 3: Geographic Search
```bash
curl -X GET "http://localhost:5000/api/v3/immi/markers/bimschg?bbox=52.5,13.4,52.6,13.5&limit=20" \
  -H "Authorization: Bearer <token>"
```

---

## 📚 Further Resources

- **Interactive Documentation:** `/docs` (Swagger UI)
- **OpenAPI Spec:** `/openapi.json`
- **Architecture Guide:** `docs/architecture/CONSOLIDATED_ARCHITECTURE_v4.md`
- **Development:** `docs/development/`
- **Integration Guides:** `docs/integration/`

---

**Last Updated:** 4. Dezember 2025  
**API Version:** 3.0.0  
**Status:** ✅ Production Ready
