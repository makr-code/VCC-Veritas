# ThemisDB Adapter - Advanced Features Implementation Guide

**Datum:** 7. November 2025  
**Version:** 1.0  
**Status:** Planung & Implementierung

---

## 1. Rate Limiting (Per-User/IP)

### 1.1 Anforderungen

**Ziele:**
- Schutz vor API-Missbrauch und DDoS-Attacken
- Fair-Use-Policy für Multi-Tenant-Umgebungen
- Differenzierte Limits für verschiedene User-Tiers
- IP-basiertes Fallback wenn keine Authentifizierung

**Metriken:**
- Requests pro Minute (RPM) pro User/IP
- Burst-Toleranz für legitime Spitzen
- Sliding Window statt Fixed Window

### 1.2 Technologie-Stack

**Empfohlene Lösung:**
```python
# slowapi - FastAPI-native Rate Limiting
# Redis als Backend für verteilte Systeme

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
```

**Alternative:**
- `fastapi-limiter` (Redis-backed)
- `limits` (Memory/Redis/Memcached)

### 1.3 Implementierung

#### Installation

```bash
pip install slowapi redis
```

**requirements.txt:**
```txt
slowapi==0.1.9
redis==5.0.1
```

#### Backend Integration

**Datei:** `backend/middleware/rate_limiter.py`

```python
"""
Rate Limiting Middleware für FastAPI
Unterstützt User-basierte und IP-basierte Limits
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from typing import Optional
import redis.asyncio as redis

# Redis Connection für verteiltes Rate Limiting
redis_client = redis.from_url(
    "redis://localhost:6379",
    encoding="utf-8",
    decode_responses=True
)

# Limiter mit Custom Key Function
def get_user_or_ip(request: Request) -> str:
    """
    Extrahiert User-ID aus JWT oder fällt auf IP zurück
    """
    # Option 1: Authenticated User
    if hasattr(request.state, "user") and request.state.user:
        user_id = request.state.user.get("sub")  # JWT subject
        return f"user:{user_id}"
    
    # Option 2: API Key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"
    
    # Fallback: IP Address
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_user_or_ip,
    storage_uri="redis://localhost:6379",
    strategy="moving-window"  # Bessere Fairness als fixed-window
)

# Custom Exception Handler
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Gibt strukturierte Error-Response bei Rate Limit
    """
    return HTTPException(
        status_code=429,
        detail={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}",
            "retry_after": exc.headers.get("Retry-After"),
            "limit": str(exc)
        },
        headers={"Retry-After": exc.headers.get("Retry-After", "60")}
    )
```

#### FastAPI Integration

**Datei:** `backend/app.py`

```python
from fastapi import FastAPI
from backend.middleware.rate_limiter import limiter, rate_limit_handler
from slowapi.errors import RateLimitExceeded

app = FastAPI()

# Rate Limiter registrieren
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Alternative: Als Middleware
# app.add_middleware(SlowAPIMiddleware)
```

#### Endpoint-Spezifische Limits

**Datei:** `backend/api/v3/themis_router.py`

```python
from fastapi import APIRouter, Depends
from backend.middleware.rate_limiter import limiter

themis_router = APIRouter(prefix="/themis", tags=["ThemisDB"])

# Public Endpoint: Strenge Limits
@themis_router.post("/vector/search")
@limiter.limit("10/minute")  # 10 Requests pro Minute
async def vector_search(request: Request, query: VectorSearchRequest):
    pass

# Authenticated Endpoint: Großzügigere Limits
@themis_router.post("/aql/query")
@limiter.limit("100/minute")  # 100 Requests pro Minute
async def execute_aql(request: Request, query: AQLQueryRequest):
    pass

# Admin Endpoint: Sehr hohe Limits
@themis_router.get("/stats")
@limiter.limit("1000/hour")
async def get_stats(request: Request):
    pass
```

#### Tier-basierte Limits

```python
from enum import Enum
from functools import wraps

class UserTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

TIER_LIMITS = {
    UserTier.FREE: "10/minute",
    UserTier.PREMIUM: "100/minute",
    UserTier.ENTERPRISE: "1000/minute"
}

def tier_based_limit(endpoint_name: str):
    """
    Decorator für Tier-basierte Rate Limits
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user_tier = request.state.user.get("tier", UserTier.FREE)
            limit = TIER_LIMITS[user_tier]
            
            # Dynamisches Rate Limiting
            limiter.limit(limit)(func)
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

# Verwendung
@themis_router.post("/vector/search")
@tier_based_limit("vector_search")
async def vector_search(request: Request, query: VectorSearchRequest):
    pass
```

### 1.4 Monitoring & Metrics

```python
from prometheus_client import Counter, Histogram

rate_limit_exceeded_counter = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit violations",
    ["endpoint", "user_tier"]
)

rate_limit_remaining_gauge = Gauge(
    "rate_limit_remaining",
    "Remaining requests in current window",
    ["user_id", "endpoint"]
)
```

### 1.5 Testing

```python
import pytest
from fastapi.testclient import TestClient

def test_rate_limit_exceeded():
    client = TestClient(app)
    
    # Sende 11 Requests (Limit: 10/minute)
    for i in range(11):
        response = client.post("/api/v3/themis/vector/search", json={...})
        
        if i < 10:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
            assert "retry_after" in response.json()["detail"]
```

---

## 2. API-Versioning (v3 → v4)

### 2.1 Versioning-Strategie

**Optionen:**
1. **URL-basiert:** `/api/v3/`, `/api/v4/` ✅ **EMPFOHLEN**
2. **Header-basiert:** `Accept: application/vnd.veritas.v4+json`
3. **Query-Parameter:** `/api/themis?version=4`

**Begründung für URL-basiert:**
- Beste Dokumentierbarkeit (Swagger UI pro Version)
- Einfaches Caching (CDN, Browser)
- Klare Deprecation-Pfade

### 2.2 Implementierung

#### Ordnerstruktur

```
backend/
├── api/
│   ├── v3/
│   │   ├── __init__.py
│   │   ├── themis_router.py
│   │   └── adapter_router.py
│   ├── v4/
│   │   ├── __init__.py
│   │   ├── themis_router.py  # Neue Features
│   │   └── adapter_router.py  # Breaking Changes
│   └── common/
│       ├── models.py  # Shared Pydantic Models
│       └── dependencies.py
```

#### V4 Router Setup

**Datei:** `backend/api/v4/__init__.py`

```python
"""
API v4 - Breaking Changes & New Features
Release: Q1 2026
"""

from fastapi import APIRouter
from backend.api.v4 import themis_router, adapter_router

v4_router = APIRouter(prefix="/v4")

# Sub-Routers registrieren
v4_router.include_router(themis_router.router, prefix="/themis")
v4_router.include_router(adapter_router.router, prefix="/adapters")

# Deprecation Warning in v3
@v3_router.get("/")
async def v3_root():
    return {
        "version": "v3",
        "status": "deprecated",
        "sunset_date": "2026-12-31",
        "migration_guide": "https://docs.veritas.ai/api/v3-to-v4",
        "new_version": "/api/v4/"
    }
```

#### App Integration

**Datei:** `backend/app.py`

```python
from fastapi import FastAPI
from backend.api.v3 import v3_router
from backend.api.v4 import v4_router

app = FastAPI(
    title="Veritas API",
    version="4.0.0",
    docs_url="/docs",  # Swagger für v4
    redoc_url="/redoc"
)

# V3 mit Deprecation Warning
app.include_router(v3_router, prefix="/api/v3", deprecated=True)

# V4 als neue Hauptversion
app.include_router(v4_router, prefix="/api/v4")

# Redirect root zu v4
@app.get("/api")
async def api_root():
    return {"message": "Use /api/v4/ (latest) or /api/v3/ (deprecated)"}
```

### 2.3 Breaking Changes in V4

**Beispiel-Änderungen:**

```python
# V3: Synchrone Response
@v3_themis_router.post("/vector/search")
async def vector_search_v3(query: VectorSearchRequestV3):
    results = await adapter.vector_search(...)
    return {"results": results}

# V4: Streaming Response (SSE)
@v4_themis_router.post("/vector/search")
async def vector_search_v4(query: VectorSearchRequestV4):
    async def event_generator():
        async for result in adapter.vector_search_stream(...):
            yield {"event": "result", "data": result}
    
    return EventSourceResponse(event_generator())

# V4: Neue Required Fields
class VectorSearchRequestV4(BaseModel):
    query: str
    top_k: int = 5
    collection: str  # Jetzt REQUIRED (war optional in v3)
    filters: Optional[Dict[str, Any]] = None  # Neues Feature
    explain: bool = False  # Query Execution Plan
```

### 2.4 Deprecation Management

```python
from datetime import datetime
from fastapi import Header, HTTPException

async def check_api_version(x_api_version: str = Header(None)):
    """
    Dependency für Version-Check
    """
    if x_api_version == "v3":
        sunset_date = datetime(2026, 12, 31)
        days_remaining = (sunset_date - datetime.now()).days
        
        if days_remaining < 90:
            # Warning in Response Header
            return {
                "X-API-Deprecation": "true",
                "X-API-Sunset-Date": sunset_date.isoformat(),
                "X-API-Sunset-Days": str(days_remaining)
            }
    
    return {}

# Verwendung
@v3_router.get("/status", dependencies=[Depends(check_api_version)])
async def status():
    pass
```

---

## 3. Distributed Tracing (OpenTelemetry)

### 3.1 Architektur

```
┌─────────────┐     Traces      ┌──────────────┐
│   FastAPI   │ ──────────────→ │   Jaeger     │
│   Backend   │                  │   Collector  │
└─────────────┘                  └──────────────┘
       │                                │
       │ Spans                          │
       ↓                                ↓
┌─────────────┐                  ┌──────────────┐
│  ThemisDB   │                  │   Grafana    │
│   Adapter   │                  │   Tempo      │
└─────────────┘                  └──────────────┘
```

### 3.2 Installation

```bash
pip install opentelemetry-api \
            opentelemetry-sdk \
            opentelemetry-instrumentation-fastapi \
            opentelemetry-instrumentation-httpx \
            opentelemetry-exporter-jaeger
```

### 3.3 Implementierung

**Datei:** `backend/telemetry/tracing.py`

```python
"""
OpenTelemetry Distributed Tracing Setup
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource

def setup_tracing(app, service_name: str = "veritas-backend"):
    """
    Initialisiert OpenTelemetry Tracing
    """
    # Resource mit Service-Informationen
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "4.0.0",
        "deployment.environment": "production"
    })
    
    # Tracer Provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Jaeger Exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    # Batch Processor (bessere Performance)
    span_processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(span_processor)
    
    # Auto-Instrumentation
    FastAPIInstrumentor.instrument_app(app)  # Alle Endpoints
    HTTPXClientInstrumentor().instrument()   # HTTP-Calls zu ThemisDB
    
    return trace.get_tracer(__name__)

# Global Tracer
tracer = None
```

#### App Integration

**Datei:** `backend/app.py`

```python
from backend.telemetry.tracing import setup_tracing

app = FastAPI()

# Tracing aktivieren
tracer = setup_tracing(app, service_name="veritas-api")
```

#### Custom Spans im Adapter

**Datei:** `backend/adapters/themisdb_adapter.py`

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class ThemisDBAdapter:
    async def vector_search(self, query: str, top_k: int, **kwargs):
        # Root Span (automatisch von FastAPI)
        with tracer.start_as_current_span(
            "themis.vector_search",
            attributes={
                "db.system": "themisdb",
                "db.operation": "vector_search",
                "db.collection": kwargs.get("collection"),
                "vector.top_k": top_k
            }
        ) as span:
            # Child Span für HTTP Request
            with tracer.start_as_current_span("http.post"):
                response = await self.client.post("/api/vector/search", ...)
                
                # Span Attributes
                span.set_attribute("http.status_code", response.status_code)
                span.set_attribute("http.response_time_ms", elapsed_ms)
                
                if response.status_code >= 400:
                    span.set_status(Status(StatusCode.ERROR))
                    span.record_exception(Exception(response.text))
            
            # Child Span für Post-Processing
            with tracer.start_as_current_span("process_results"):
                results = self._process_response(response.json())
                span.set_attribute("results.count", len(results))
            
            return results
```

### 3.4 Trace Context Propagation

```python
from opentelemetry.propagate import inject

async def call_external_service():
    """
    Trace Context wird automatisch in HTTP Headers propagiert
    """
    headers = {}
    inject(headers)  # Fügt traceparent/tracestate hinzu
    
    response = await httpx.post(
        "https://external-api.com/endpoint",
        headers=headers  # Trace Context wird weitergegeben
    )
```

### 3.5 Jaeger Setup (Docker)

```yaml
# docker-compose.yml
services:
  jaeger:
    image: jaegertracing/all-in-one:1.51
    ports:
      - "6831:6831/udp"  # Agent (Thrift compact)
      - "16686:16686"     # UI
      - "14268:14268"     # Collector HTTP
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
```

**Zugriff:** `http://localhost:16686` (Jaeger UI)

---

## 4. Prometheus Metrics Export

### 4.1 Metriken-Typen

**Counter:** Monoton steigende Werte (Requests, Errors)  
**Gauge:** Aktueller Wert (Connections, Queue Size)  
**Histogram:** Verteilung (Latency, Response Size)  
**Summary:** Quantile (p50, p95, p99)

### 4.2 Installation

```bash
pip install prometheus-client prometheus-fastapi-instrumentator
```

### 4.3 Implementierung

**Datei:** `backend/telemetry/metrics.py`

```python
"""
Prometheus Metrics für ThemisDB Adapter
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator

# Custom Metrics
adapter_requests_total = Counter(
    "adapter_requests_total",
    "Total adapter requests",
    ["adapter", "operation", "status"]
)

adapter_latency_seconds = Histogram(
    "adapter_latency_seconds",
    "Adapter operation latency",
    ["adapter", "operation"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

adapter_connections = Gauge(
    "adapter_connections_active",
    "Active adapter connections",
    ["adapter"]
)

themis_query_size_bytes = Histogram(
    "themis_query_size_bytes",
    "ThemisDB query payload size",
    buckets=[100, 1000, 10000, 100000, 1000000]
)

adapter_info = Info(
    "adapter_info",
    "Adapter version and configuration"
)

# Rate Limiting Metrics
rate_limit_exceeded_total = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit violations",
    ["endpoint", "user_tier"]
)

rate_limit_remaining = Gauge(
    "rate_limit_remaining_requests",
    "Remaining requests in current window",
    ["user_id", "endpoint"]
)

def setup_metrics(app):
    """
    Initialisiert Prometheus Metrics
    """
    # Auto-Instrumentation (HTTP Metrics)
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True
    )
    
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    
    # Adapter Info setzen
    adapter_info.info({
        "version": "1.0.0",
        "themis_host": os.getenv("THEMIS_HOST", "localhost"),
        "fallback_enabled": str(os.getenv("USE_UDS3_FALLBACK", "true"))
    })
```

#### Metrics in Adapter

**Datei:** `backend/adapters/themisdb_adapter.py`

```python
from backend.telemetry.metrics import (
    adapter_requests_total,
    adapter_latency_seconds,
    adapter_connections,
    themis_query_size_bytes
)
import time

class ThemisDBAdapter:
    async def vector_search(self, query: str, top_k: int, **kwargs):
        start_time = time.time()
        status = "success"
        
        try:
            adapter_connections.labels(adapter="themis").inc()
            
            # Query Size Tracking
            query_size = len(query.encode('utf-8'))
            themis_query_size_bytes.observe(query_size)
            
            response = await self.client.post(...)
            
            return response.json()
            
        except Exception as e:
            status = "error"
            raise
        
        finally:
            # Latency Histogram
            duration = time.time() - start_time
            adapter_latency_seconds.labels(
                adapter="themis",
                operation="vector_search"
            ).observe(duration)
            
            # Request Counter
            adapter_requests_total.labels(
                adapter="themis",
                operation="vector_search",
                status=status
            ).inc()
            
            adapter_connections.labels(adapter="themis").dec()
```

### 4.4 Prometheus Configuration

**Datei:** `prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'veritas-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    
  - job_name: 'themis-db'
    static_configs:
      - targets: ['localhost:8765']
    metrics_path: '/metrics'
```

### 4.5 Grafana Dashboard

**Beispiel-Queries:**

```promql
# Request Rate (RPS)
rate(adapter_requests_total[5m])

# Error Rate
rate(adapter_requests_total{status="error"}[5m]) 
  / rate(adapter_requests_total[5m])

# P95 Latency
histogram_quantile(0.95, 
  rate(adapter_latency_seconds_bucket[5m]))

# Active Connections
adapter_connections_active{adapter="themis"}

# Rate Limit Violations per Hour
increase(rate_limit_exceeded_total[1h])
```

---

## 5. GraphQL Alternative

### 5.1 Motivation

**Vorteile gegenüber REST:**
- Client-definierte Queries (keine Over-/Underfetching)
- Single Endpoint (`/graphql`)
- Strongly Typed Schema
- Introspection & Auto-Docs

**Use Cases:**
- Frontend mit komplexen Datenabhängigkeiten
- Mobile Apps mit Bandbreitenbeschränkungen
- Aggregierte Queries über mehrere Ressourcen

### 5.2 Installation

```bash
pip install strawberry-graphql[fastapi] strawberry-graphql[debug-server]
```

### 5.3 Schema Definition

**Datei:** `backend/graphql/schema.py`

```python
"""
GraphQL Schema für ThemisDB Adapter
"""

import strawberry
from typing import List, Optional
from backend.adapters.adapter_factory import get_database_adapter

@strawberry.type
class VectorSearchResult:
    document_id: str
    score: float
    content: str
    metadata: Optional[strawberry.scalars.JSON] = None

@strawberry.type
class GraphNode:
    id: str
    label: str
    properties: strawberry.scalars.JSON

@strawberry.type
class GraphEdge:
    from_node: str
    to_node: str
    relationship: str
    properties: Optional[strawberry.scalars.JSON] = None

@strawberry.type
class AdapterStatus:
    name: str
    available: bool
    version: str
    query_count: int
    avg_latency_ms: float

@strawberry.input
class VectorSearchInput:
    query: str
    top_k: int = 5
    collection: str = "documents"
    threshold: Optional[float] = None

@strawberry.type
class Query:
    @strawberry.field
    async def vector_search(
        self, 
        input: VectorSearchInput
    ) -> List[VectorSearchResult]:
        """
        Semantic vector search
        """
        adapter = await get_database_adapter()
        results = await adapter.vector_search(
            query=input.query,
            top_k=input.top_k,
            collection=input.collection,
            threshold=input.threshold
        )
        
        return [
            VectorSearchResult(
                document_id=r["id"],
                score=r["score"],
                content=r["content"],
                metadata=r.get("metadata")
            )
            for r in results
        ]
    
    @strawberry.field
    async def graph_traverse(
        self,
        start_vertex: str,
        edge_collection: str,
        max_depth: int = 3
    ) -> List[GraphNode]:
        """
        Graph traversal from starting vertex
        """
        adapter = await get_database_adapter()
        result = await adapter.graph_traverse(
            start_vertex=start_vertex,
            edge_collection=edge_collection,
            max_depth=max_depth
        )
        
        return [
            GraphNode(
                id=node["_key"],
                label=node.get("label", ""),
                properties=node
            )
            for node in result.get("vertices", [])
        ]
    
    @strawberry.field
    async def adapter_status(self) -> List[AdapterStatus]:
        """
        Status of all database adapters
        """
        # Implementierung aus adapter_router.get_adapter_status()
        return [...]

@strawberry.type
class Mutation:
    @strawberry.mutation
    async def insert_document(
        self,
        collection: str,
        document: strawberry.scalars.JSON
    ) -> str:
        """
        Insert document into ThemisDB
        """
        adapter = await get_database_adapter()
        result = await adapter.insert_document(collection, document)
        return result["_key"]

# Schema zusammensetzen
schema = strawberry.Schema(query=Query, mutation=Mutation)
```

### 5.4 FastAPI Integration

**Datei:** `backend/app.py`

```python
from strawberry.fastapi import GraphQLRouter
from backend.graphql.schema import schema

app = FastAPI()

# GraphQL Endpoint
graphql_app = GraphQLRouter(
    schema,
    graphiql=True  # Interactive GraphiQL IDE
)

app.include_router(graphql_app, prefix="/graphql")
```

### 5.5 Beispiel-Queries

**GraphiQL UI:** `http://localhost:8000/graphql`

```graphql
# Vector Search mit selektiven Fields
query SearchDocuments {
  vectorSearch(input: {
    query: "machine learning best practices"
    topK: 5
    collection: "documents"
  }) {
    documentId
    score
    content
    metadata
  }
}

# Graph Traversal
query FindRelated {
  graphTraverse(
    startVertex: "doc123"
    edgeCollection: "citations"
    maxDepth: 2
  ) {
    id
    label
    properties
  }
}

# Kombinierte Query
query Dashboard {
  adapterStatus {
    name
    available
    queryCount
    avgLatencyMs
  }
  
  recentSearches: vectorSearch(input: {
    query: "recent updates"
    topK: 3
  }) {
    documentId
    score
  }
}

# Mutation
mutation AddDocument {
  insertDocument(
    collection: "documents"
    document: {
      title: "GraphQL Guide"
      content: "..."
      tags: ["graphql", "api"]
    }
  )
}
```

### 5.6 DataLoader für N+1 Problem

```python
from strawberry.dataloader import DataLoader

async def load_documents(keys: List[str]) -> List[Document]:
    """
    Batch-Loading für Dokumente
    """
    adapter = await get_database_adapter()
    docs = await adapter.get_documents_batch(keys)
    return docs

document_loader = DataLoader(load_fn=load_documents)

@strawberry.type
class Query:
    @strawberry.field
    async def document(self, id: str) -> Document:
        return await document_loader.load(id)  # Batched!
```

---

## 6. WebSocket Support (zusätzlich zu SSE)

### 6.1 SSE vs WebSocket Vergleich

| Feature | SSE | WebSocket |
|---------|-----|-----------|
| **Direction** | Server → Client | Bidirectional |
| **Protocol** | HTTP | WS/WSS |
| **Auto-Reconnect** | Native | Manual |
| **Browser Support** | ✅ Excellent | ✅ Excellent |
| **Proxy-Friendly** | ✅ Yes | ⚠️ Depends |
| **Overhead** | Lower | Higher |
| **Use Case** | Real-time updates | Chat, Gaming |

**Empfehlung:**
- **SSE:** Log Streaming, Metrics Updates, Notifications
- **WebSocket:** Interactive Chat, Real-time Collaboration, Gaming

### 6.2 Installation

```bash
pip install websockets
# FastAPI hat native WebSocket support (keine extra deps)
```

### 6.3 Implementierung

**Datei:** `backend/api/v4/websocket_router.py`

```python
"""
WebSocket Endpoints für Real-time Features
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

websocket_router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        self.active_connections[client_id].remove(websocket)
        if not self.active_connections[client_id]:
            del self.active_connections[client_id]
    
    async def send_personal_message(self, message: dict, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_json(message)
    
    async def broadcast(self, message: dict):
        for client_connections in self.active_connections.values():
            for connection in client_connections:
                await connection.send_json(message)

manager = ConnectionManager()

# WebSocket Endpoint: Real-time Vector Search
@websocket_router.websocket("/search")
async def websocket_search(websocket: WebSocket, client_id: str):
    """
    Real-time vector search mit Streaming Results
    
    Client sendet:
    {
      "action": "search",
      "query": "machine learning",
      "top_k": 10
    }
    
    Server streamt:
    {
      "type": "result",
      "data": {...},
      "index": 0
    }
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Warte auf Client Message
            data = await websocket.receive_json()
            
            if data["action"] == "search":
                query = data["query"]
                top_k = data.get("top_k", 5)
                
                # Adapter Query
                adapter = await get_database_adapter()
                
                # Streaming Response
                await websocket.send_json({
                    "type": "search_started",
                    "query": query
                })
                
                results = await adapter.vector_search(query, top_k)
                
                for i, result in enumerate(results):
                    await websocket.send_json({
                        "type": "result",
                        "data": result,
                        "index": i,
                        "total": len(results)
                    })
                    await asyncio.sleep(0.1)  # Progressive loading
                
                await websocket.send_json({
                    "type": "search_complete",
                    "total_results": len(results)
                })
            
            elif data["action"] == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        await manager.broadcast({
            "type": "user_disconnected",
            "client_id": client_id
        })

# WebSocket: Adapter Status Updates
@websocket_router.websocket("/adapter/status")
async def websocket_adapter_status(websocket: WebSocket):
    """
    Real-time Adapter Status Updates
    Sendet alle 5 Sekunden Status-Update
    """
    await websocket.accept()
    
    try:
        while True:
            status = await get_adapter_status()
            await websocket.send_json({
                "type": "status_update",
                "timestamp": datetime.now().isoformat(),
                "data": status
            })
            await asyncio.sleep(5)
    
    except WebSocketDisconnect:
        pass

# WebSocket: Query Logs (Alternative zu SSE)
@websocket_router.websocket("/logs")
async def websocket_logs(websocket: WebSocket, log_level: str = "INFO"):
    """
    Real-time Log Streaming via WebSocket
    """
    await websocket.accept()
    
    # Custom Log Handler
    from backend.telemetry.logging import WebSocketLogHandler
    
    handler = WebSocketLogHandler(websocket, level=log_level)
    logger.addHandler(handler)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    
    except WebSocketDisconnect:
        logger.removeHandler(handler)
```

### 6.4 Client Implementation

**JavaScript:**

```javascript
// WebSocket Connection
const ws = new WebSocket('ws://localhost:8000/api/v4/ws/search?client_id=user123');

ws.onopen = () => {
  console.log('Connected to WebSocket');
  
  // Send Search Query
  ws.send(JSON.stringify({
    action: 'search',
    query: 'machine learning best practices',
    top_k: 10
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'search_started':
      console.log('Search started:', message.query);
      break;
    
    case 'result':
      console.log(`Result ${message.index + 1}/${message.total}:`, message.data);
      displayResult(message.data);
      break;
    
    case 'search_complete':
      console.log('Search complete:', message.total_results, 'results');
      break;
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('WebSocket disconnected');
  // Auto-reconnect
  setTimeout(() => connectWebSocket(), 5000);
};

// Heartbeat (Keep-Alive)
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'ping' }));
  }
}, 30000);
```

**Python Client:**

```python
import asyncio
import websockets
import json

async def search_websocket():
    uri = "ws://localhost:8000/api/v4/ws/search?client_id=python_client"
    
    async with websockets.connect(uri) as websocket:
        # Send Query
        await websocket.send(json.dumps({
            "action": "search",
            "query": "machine learning",
            "top_k": 5
        }))
        
        # Receive Results
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "result":
                print(f"Result {data['index']}: {data['data']}")
            
            elif data["type"] == "search_complete":
                print(f"Total: {data['total_results']}")
                break

asyncio.run(search_websocket())
```

### 6.5 Testing

```python
from fastapi.testclient import TestClient

def test_websocket():
    client = TestClient(app)
    
    with client.websocket_connect("/api/v4/ws/search?client_id=test") as websocket:
        # Send Query
        websocket.send_json({
            "action": "search",
            "query": "test",
            "top_k": 3
        })
        
        # Receive search_started
        data = websocket.receive_json()
        assert data["type"] == "search_started"
        
        # Receive results
        results = []
        while True:
            data = websocket.receive_json()
            if data["type"] == "result":
                results.append(data["data"])
            elif data["type"] == "search_complete":
                break
        
        assert len(results) == 3
```

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Wochen 1-2)
- ✅ Rate Limiting (slowapi + Redis)
- ✅ Prometheus Metrics Export
- ✅ Basic OpenTelemetry Setup

### Phase 2: Versioning (Wochen 3-4)
- 🔄 API v4 Structure
- 🔄 Breaking Changes dokumentieren
- 🔄 Migration Guide

### Phase 3: Advanced Tracing (Wochen 5-6)
- 🔄 Custom Spans in allen Adaptern
- 🔄 Jaeger Production Setup
- 🔄 Grafana Dashboards

### Phase 4: Alternative Protocols (Wochen 7-8)
- 🔄 GraphQL Schema & Resolvers
- 🔄 WebSocket Endpoints
- 🔄 Client SDKs

### Phase 5: Production Hardening (Wochen 9-10)
- 🔄 Load Testing
- 🔄 Security Audit
- 🔄 Documentation Finalization

---

## 8. Dependencies Overview

```txt
# requirements.txt (neue Dependencies)

# Rate Limiting
slowapi==0.1.9
redis==5.0.1

# Distributed Tracing
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-httpx==0.42b0
opentelemetry-exporter-jaeger==1.21.0

# Metrics
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0

# GraphQL
strawberry-graphql[fastapi]==0.216.0
strawberry-graphql[debug-server]==0.216.0

# WebSockets (FastAPI native - keine extra deps)
```

---

## 9. Testing Strategy

### Unit Tests
```python
# tests/test_rate_limiting.py
# tests/test_metrics.py
# tests/test_graphql_schema.py
# tests/test_websocket.py
```

### Integration Tests
```python
# tests/integration/test_tracing_e2e.py
# tests/integration/test_api_versioning.py
```

### Load Tests
```python
# locust/load_test.py - Locust für Last-Tests
# k6/script.js - k6 für Performance-Tests
```

---

## 10. Documentation Updates

- [ ] OpenAPI/Swagger Docs für v4
- [ ] GraphQL Schema Documentation (introspection)
- [ ] WebSocket Protocol Specification
- [ ] Metrics & Tracing Runbooks
- [ ] Migration Guide v3 → v4

---

**Ende der Implementierungsplanung**
