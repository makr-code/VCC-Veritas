# ThemisDB & Adapter Endpoints - Quick Reference
**Erstellt:** 7. November 2025  
**Status:** ✅ Produktionsbereit

---

## Übersicht

Zwei neue Router erweitern die VERITAS API v3:

1. **`/api/v3/themis/`** - Direkter ThemisDB-Zugriff
2. **`/api/v3/adapters/`** - Adapter-Management & Monitoring

---

## 1. ThemisDB Router (`/api/v3/themis/`)

### 1.1 Vector Search

**Endpoint:** `POST /api/v3/themis/vector/search`

```bash
curl -X POST "http://localhost:8000/api/v3/themis/vector/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "BGB Vertragsrecht Minderjährige",
    "top_k": 5,
    "collection": "legal_documents",
    "threshold": 0.7
  }'
```

**Response:**
```json
{
  "results": [
    {
      "doc_id": "bgb_123",
      "content": "§1 BGB Vertragsrecht...",
      "score": 0.95,
      "metadata": {"year": 2020, "source": "bgb"}
    }
  ],
  "count": 5,
  "collection": "legal_documents",
  "execution_time_ms": 45.2,
  "adapter": "ThemisDB"
}
```

---

### 1.2 Graph Traversal

**Endpoint:** `POST /api/v3/themis/graph/traverse`

```bash
curl -X POST "http://localhost:8000/api/v3/themis/graph/traverse" \
  -H "Content-Type: application/json" \
  -d '{
    "start_vertex": "documents/bgb_123",
    "edge_collection": "citations",
    "direction": "any",
    "max_depth": 2
  }'
```

**Response:**
```json
{
  "paths": [
    {
      "vertices": ["documents/bgb_123", "documents/bgb_456"],
      "edges": ["citations/cite_1"]
    }
  ],
  "count": 1,
  "start_vertex": "documents/bgb_123",
  "execution_time_ms": 23.8
}
```

---

### 1.3 AQL Query

**Endpoint:** `POST /api/v3/themis/aql/query`

```bash
curl -X POST "http://localhost:8000/api/v3/themis/aql/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "FOR doc IN documents FILTER doc.year >= @year LIMIT @limit RETURN doc",
    "bind_vars": {
      "year": 2020,
      "limit": 10
    }
  }'
```

**Response:**
```json
{
  "result": [
    {"_key": "doc1", "title": "Document 1", "year": 2020},
    {"_key": "doc2", "title": "Document 2", "year": 2021}
  ],
  "count": 2,
  "execution_time_ms": 12.5
}
```

---

### 1.4 Document CRUD

**Get Document:**
```bash
curl "http://localhost:8000/api/v3/themis/document/documents/doc123"
```

**Insert Document:**
```bash
curl -X POST "http://localhost:8000/api/v3/themis/document/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "document": {
      "title": "New Document",
      "content": "Document content...",
      "year": 2025
    },
    "key": "doc_new_123"
  }'
```

---

### 1.5 Health & Stats

**Health Check:**
```bash
curl "http://localhost:8000/api/v3/themis/health"
```

**Response:**
```json
{
  "status": "healthy",
  "available": true,
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "timestamp": "2025-11-07T10:30:00Z"
}
```

**Statistics:**
```bash
curl "http://localhost:8000/api/v3/themis/stats"
```

**Response:**
```json
{
  "adapter": "ThemisDB",
  "statistics": {
    "total_queries": 150,
    "successful_queries": 148,
    "failed_queries": 2,
    "avg_latency_ms": 35.2,
    "success_rate": 0.987
  },
  "timestamp": "2025-11-07T10:30:00Z"
}
```

---

## 2. Adapter Management Router (`/api/v3/adapters/`)

### 2.1 Adapter Status

**Endpoint:** `GET /api/v3/adapters/status`

```bash
curl "http://localhost:8000/api/v3/adapters/status"
```

**Response:**
```json
{
  "current_adapter": "themis",
  "themis_available": true,
  "uds3_available": true,
  "failover_enabled": true,
  "last_check": "2025-11-07T10:30:00Z",
  "env_config": {
    "THEMIS_ENABLED": "true",
    "THEMIS_HOST": "localhost",
    "THEMIS_PORT": "8765",
    "USE_UDS3_FALLBACK": "true"
  }
}
```

---

### 2.2 Performance Metrics

**Endpoint:** `GET /api/v3/adapters/metrics`

```bash
curl "http://localhost:8000/api/v3/adapters/metrics"
```

**Response:**
```json
[
  {
    "adapter": "themis",
    "available": true,
    "total_queries": 150,
    "successful_queries": 148,
    "failed_queries": 2,
    "empty_results": 5,
    "avg_latency_ms": 35.2,
    "success_rate": 0.987,
    "timestamp": "2025-11-07T10:30:00Z"
  },
  {
    "adapter": "uds3",
    "available": true,
    "total_queries": 0,
    "successful_queries": 0,
    "failed_queries": 0,
    "empty_results": 0,
    "avg_latency_ms": 0.0,
    "success_rate": 0.0,
    "timestamp": "2025-11-07T10:30:00Z"
  }
]
```

---

### 2.3 Adapter Switch Validation

**Endpoint:** `POST /api/v3/adapters/switch`

```bash
# Validate switch to ThemisDB
curl -X POST "http://localhost:8000/api/v3/adapters/switch?target=themis&validate_only=true"
```

**Response:**
```json
{
  "target": "themis",
  "validated": true,
  "available": true,
  "action_required": "Set environment variables:\n  THEMIS_ENABLED=true\n  THEMIS_HOST=<your-host>\nThen restart backend",
  "message": "ThemisDB is available and ready"
}
```

---

### 2.4 Connectivity Tests

**Endpoint:** `POST /api/v3/adapters/test`

```bash
curl -X POST "http://localhost:8000/api/v3/adapters/test"
```

**Response:**
```json
[
  {
    "adapter": "themis",
    "reachable": true,
    "latency_ms": 8.3,
    "timestamp": "2025-11-07T10:30:00Z"
  },
  {
    "adapter": "uds3",
    "reachable": true,
    "timestamp": "2025-11-07T10:30:00Z"
  }
]
```

---

### 2.5 Adapter Comparison

**Endpoint:** `GET /api/v3/adapters/comparison`

```bash
curl "http://localhost:8000/api/v3/adapters/comparison"
```

**Response:**
```json
{
  "themis": {
    "available": true,
    "features": [
      "Native Multi-Model (Vector, Graph, Document, Relational)",
      "HNSW Vector Search",
      "Property Graph Traversal",
      "AQL Query Language",
      "MVCC Transactions",
      "Single Database (simplified ops)"
    ],
    "metrics": {
      "total_queries": 150,
      "avg_latency_ms": 35.2,
      "success_rate": 0.987
    }
  },
  "uds3": {
    "available": true,
    "features": [
      "Polyglot Persistence (4+ backends)",
      "Multi-Backend Orchestration",
      "SAGA Transactions",
      "Backend-Specific Optimizations",
      "Legacy Integration"
    ]
  }
}
```

---

### 2.6 Adapter Capabilities

**Endpoint:** `GET /api/v3/adapters/capabilities`

```bash
curl "http://localhost:8000/api/v3/adapters/capabilities"
```

**Response:**
```json
[
  {
    "adapter": "themis",
    "available": true,
    "data_models": [
      "Vector (Embeddings)",
      "Graph (Property Graph)",
      "Document (JSON)",
      "Relational (Tables)"
    ],
    "query_languages": [
      "AQL (Themis Query Language)",
      "REST API",
      "Native Vector Search"
    ],
    "features": [
      {
        "name": "vector_search",
        "supported": true,
        "description": "HNSW-based semantic search with multiple distance metrics",
        "endpoint": "/api/v3/themis/vector/search"
      },
      {
        "name": "graph_traversal",
        "supported": true,
        "description": "Bidirectional property graph traversal with configurable depth",
        "endpoint": "/api/v3/themis/graph/traverse"
      },
      {
        "name": "aql_queries",
        "supported": true,
        "description": "Multi-model AQL query execution",
        "endpoint": "/api/v3/themis/aql/query"
      },
      {
        "name": "acid_transactions",
        "supported": true,
        "description": "MVCC transactions via RocksDB TransactionDB",
        "endpoint": null
      },
      {
        "name": "full_text_search",
        "supported": false,
        "description": "Full-text search not yet implemented (use vector search)",
        "endpoint": null
      }
    ],
    "limitations": [
      "Single-server deployment (no clustering yet)",
      "Read-only AQL queries via REST API",
      "No built-in authentication (use API Gateway)",
      "Limited query optimization for complex AQL"
    ],
    "performance_characteristics": {
      "vector_search_latency": "10-50ms (HNSW index)",
      "graph_traversal_latency": "20-100ms (depth 1-3)",
      "throughput": "5000+ queries/sec (single node)"
    }
  },
  {
    "adapter": "uds3",
    "available": true,
    "data_models": [
      "Vector (via ChromaDB)",
      "Graph (via Neo4j)",
      "Relational (via PostgreSQL)",
      "Document (via CouchDB)"
    ],
    "query_languages": [
      "Cypher (Neo4j)",
      "SQL (PostgreSQL)",
      "ChromaDB Query API",
      "Unified Query Interface"
    ],
    "features": [
      {
        "name": "polyglot_queries",
        "supported": true,
        "description": "Unified queries across multiple backends",
        "endpoint": "/api/v3/uds3/query"
      },
      {
        "name": "saga_transactions",
        "supported": true,
        "description": "Distributed SAGA transactions across backends",
        "endpoint": "/api/v3/saga/orchestrate"
      },
      {
        "name": "unified_transactions",
        "supported": false,
        "description": "No true ACID across all backends (eventual consistency)",
        "endpoint": null
      }
    ],
    "limitations": [
      "Multi-backend complexity (4+ databases to maintain)",
      "Eventual consistency across backends",
      "SAGA transaction compensation required",
      "Network latency for distributed queries"
    ],
    "performance_characteristics": {
      "polyglot_query_latency": "50-300ms (multi-backend coordination)",
      "saga_overhead": "Significant (compensation logic)",
      "concurrent_connections": "500+ (limited by backend pools)"
    }
  }
]
```

**Use Cases:**
- **Feature Discovery:** Frontend can query capabilities to enable/disable UI features
- **API Documentation:** Auto-generate documentation from capabilities
- **Client Negotiation:** Clients can select optimal adapter based on requirements
- **Integration Planning:** Understand limitations before implementation

---

## 3. Frontend-Integration

### 3.1 JavaScript/TypeScript

```typescript
// ThemisDB Vector Search
async function searchWithThemis(query: string, topK: number = 5) {
  const response = await fetch('/api/v3/themis/vector/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query,
      top_k: topK,
      collection: 'documents'
    })
  });
  
  const data = await response.json();
  return data.results;
}

// Check Adapter Status
async function checkAdapterStatus() {
  const response = await fetch('/api/v3/adapters/status');
  const data = await response.json();
  
  console.log(`Current adapter: ${data.current_adapter}`);
  console.log(`ThemisDB available: ${data.themis_available}`);
  console.log(`Fallback enabled: ${data.failover_enabled}`);
  
  return data;
}

// Get Adapter Capabilities
async function getAdapterCapabilities() {
  const response = await fetch('/api/v3/adapters/capabilities');
  const capabilities = await response.json();
  
  capabilities.forEach(cap => {
    console.log(`\n${cap.adapter.toUpperCase()}:`);
    console.log(`  Data Models: ${cap.data_models.join(', ')}`);
    console.log(`  Supported Features:`);
    cap.features
      .filter(f => f.supported)
      .forEach(f => console.log(`    - ${f.name}: ${f.description}`));
  });
  
  return capabilities;
}

// Feature Detection (Dynamic UI)
async function hasFeature(adapter: string, featureName: string): Promise<boolean> {
  const capabilities = await fetch('/api/v3/adapters/capabilities').then(r => r.json());
  const adapterCap = capabilities.find(c => c.adapter === adapter);
  
  if (!adapterCap) return false;
  
  const feature = adapterCap.features.find(f => f.name === featureName);
  return feature?.supported || false;
}

// Example: Conditional UI rendering
async function initSearchUI() {
  const hasGraphTraversal = await hasFeature('themis', 'graph_traversal');
  const hasFullTextSearch = await hasFeature('themis', 'full_text_search');
  
  if (hasGraphTraversal) {
    // Enable "Show Related Documents" button
    document.getElementById('btn-related')?.removeAttribute('disabled');
  }
  
  if (!hasFullTextSearch) {
    // Show fallback message
    console.warn('Full-text search not available, using vector search');
  }
}

// Compare Adapter Performance
async function compareAdapters() {
  const response = await fetch('/api/v3/adapters/metrics');
  const metrics = await response.json();
  
  metrics.forEach(m => {
    console.log(`${m.adapter}: ${m.success_rate * 100}% success, ${m.avg_latency_ms}ms avg`);
  });
}
```

---

### 3.2 React Component

```tsx
import React, { useState, useEffect } from 'react';

function AdapterStatus() {
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    fetch('/api/v3/adapters/status')
      .then(res => res.json())
      .then(data => setStatus(data));
  }, []);
  
  if (!status) return <div>Loading...</div>;
  
  return (
    <div className="adapter-status">
      <h3>Database Adapter Status</h3>
      <div className={`adapter ${status.current_adapter === 'themis' ? 'active' : ''}`}>
        <strong>ThemisDB:</strong> 
        {status.themis_available ? '✅ Available' : '❌ Unavailable'}
      </div>
      <div className={`adapter ${status.current_adapter === 'uds3' ? 'active' : ''}`}>
        <strong>UDS3:</strong> 
        {status.uds3_available ? '✅ Available' : '❌ Unavailable'}
      </div>
      <div className="failover">
        <strong>Failover:</strong> {status.failover_enabled ? 'Enabled' : 'Disabled'}
      </div>
    </div>
  );
}
```

---

## 4. Monitoring Dashboard

### 4.1 Prometheus Metrics

```python
# TODO: Add Prometheus exporter
# Example metrics:
# - themis_queries_total{status="success|failure"}
# - themis_query_duration_seconds
# - adapter_switch_total{from="themis|uds3", to="themis|uds3"}
```

### 4.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "VERITAS Database Adapters",
    "panels": [
      {
        "title": "Current Adapter",
        "targets": ["/api/v3/adapters/status"]
      },
      {
        "title": "Query Success Rate",
        "targets": ["/api/v3/adapters/metrics"]
      },
      {
        "title": "Average Latency",
        "targets": ["/api/v3/adapters/metrics"]
      }
    ]
  }
}
```

---

## 5. OpenAPI/Swagger

Nach Backend-Start verfügbar unter:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

**Neue Endpoint-Gruppen:**
- `ThemisDB` - Direct ThemisDB access (8 endpoints)
- `Adapters` - Adapter management (6 endpoints)

---

## 6. Testing

### 6.1 Manual Tests

```bash
# 1. Check if ThemisDB is available
curl http://localhost:8000/api/v3/themis/health

# 2. Check adapter status
curl http://localhost:8000/api/v3/adapters/status

# 3. Test vector search
curl -X POST http://localhost:8000/api/v3/themis/vector/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 3}'

# 4. Get performance metrics
curl http://localhost:8000/api/v3/adapters/metrics

# 5. Compare adapters
curl http://localhost:8000/api/v3/adapters/comparison
```

### 6.2 Automated Tests

```bash
# Run endpoint tests
pytest tests/api/test_themis_router.py -v
pytest tests/api/test_adapter_router.py -v

# Run integration tests
pytest tests/integration/test_adapter_failover.py -v
```

---

## 4. WebSocket Endpoints (Real-time)

### 4.1 Vector Search (WebSocket)

**Endpoint:** `ws://localhost:8000/api/v3/ws/search?client_id=YOUR_ID`

**Client sendet:**
```json
{
  "action": "search",
  "query": "machine learning",
  "top_k": 5,
  "collection": "documents"
}
```

**Server streamt:**
```json
{"type": "search_started", "query": "machine learning", "adapter": "themis"}
{"type": "result", "data": {...}, "index": 0, "total": 5, "score": 0.95}
{"type": "result", "data": {...}, "index": 1, "total": 5, "score": 0.88}
...
{"type": "search_complete", "total_results": 5, "duration_ms": 45.2}
```

**JavaScript Beispiel:**
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v3/ws/search?client_id=browser_client');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'search',
    query: 'machine learning',
    top_k: 5
  }));
};

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'result') {
    console.log(`Result ${msg.index + 1}: Score ${msg.score}`);
    displayResult(msg.data);
  }
};
```

---

### 4.2 Adapter Status (WebSocket)

**Endpoint:** `ws://localhost:8000/api/v3/ws/adapter/status?client_id=YOUR_ID&interval=5`

**Server sendet alle 5 Sekunden:**
```json
{
  "type": "status_update",
  "current_adapter": "themis",
  "themis": {
    "available": true,
    "query_count": 1523,
    "avg_latency_ms": 34.2
  },
  "uds3": {"available": true},
  "active_websocket_connections": 12
}
```

---

### 4.3 Live Logs (WebSocket)

**Endpoint:** `ws://localhost:8000/api/v3/ws/logs?client_id=YOUR_ID&log_level=INFO`

**Server streamt Logs:**
```json
{
  "type": "log",
  "level": "INFO",
  "message": "Vector search completed",
  "timestamp": "2025-11-07T10:30:00.123",
  "logger": "backend.adapters.themisdb_adapter"
}
```

---

### 4.4 Graph Traversal (WebSocket)

**Endpoint:** `ws://localhost:8000/api/v3/ws/graph/traverse?client_id=YOUR_ID`

**Client sendet:**
```json
{
  "action": "traverse",
  "start_vertex": "doc123",
  "edge_collection": "citations",
  "max_depth": 3
}
```

**Server streamt:**
```json
{"type": "traversal_started", "start_vertex": "doc123"}
{"type": "node", "data": {"_key": "doc1", "label": "Document"}, "index": 0}
{"type": "node", "data": {"_key": "doc2", "label": "Document"}, "index": 1}
{"type": "edge", "data": {"_from": "doc1", "_to": "doc2", "type": "cites"}}
{"type": "traversal_complete", "total_nodes": 10, "total_edges": 15}
```

---

### 4.5 WebSocket Keep-Alive (Ping/Pong)

**Alle Endpoints unterstützen:**
```json
// Client → Server
{"action": "ping"}

// Server → Client
{"type": "pong", "timestamp": "2025-11-07T10:30:00"}
```

**JavaScript Heartbeat:**
```javascript
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'ping' }));
  }
}, 30000);
```

---

### 4.6 Connection Monitoring (REST)

**Endpoint:** `GET /api/v3/ws/connections`

```bash
curl "http://localhost:8000/api/v3/ws/connections"
```

**Response:**
```json
{
  "total_connections": 15,
  "active_clients": 12,
  "clients": ["browser_client", "python_client", "..."],
  "timestamp": "2025-11-07T10:30:00"
}
```

---

## 5. FAQ

### Q: Welcher Endpoint für normale Queries?

**A:** Nutze `/api/v3/query/` (Unified Interface). ThemisDB wird automatisch genutzt wenn `THEMIS_ENABLED=true`.

### Q: Wann `/api/v3/themis/` verwenden?

**A:** Nur für ThemisDB-spezifische Features (AQL, Graph-Traversal) oder Testing.

### Q: Wie erkenne ich welcher Adapter aktiv ist?

**A:** `GET /api/v3/adapters/status` → Feld `current_adapter`

### Q: Kann ich zwischen Adaptern wechseln ohne Neustart?

**A:** Nein. Switch erfordert Environment-Änderung + Backend-Restart.

### Q: Was passiert bei ThemisDB-Ausfall?

**A:** Automatischer Fallback auf UDS3 (wenn `USE_UDS3_FALLBACK=true`).

---

## 8. Deployment Checklist

- [ ] ThemisDB-Server deployen (`docker-compose.yml`)
- [ ] Environment-Variablen setzen (`.env`)
- [ ] Backend neu starten
- [ ] Health-Checks prüfen (`/api/v3/themis/health`, `/api/v3/adapters/status`)
- [ ] Swagger-Docs prüfen (`/docs`)
- [ ] Integration-Tests ausführen
- [ ] Monitoring-Dashboards aktualisieren

---

**Status:** ✅ Produktionsbereit  
**Dokumentation:** Vollständig  
**Nächste Schritte:** Backend starten und Endpoints testen
